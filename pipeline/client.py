"""
Ollama API Client

Handles communication with Ollama servers, model discovery, and tool calling.
Includes fallback parsing for models that return tool calls as text.
"""

import json
import re
from typing import Dict, List, Optional, Tuple
import requests

from .config import PipelineConfig, ServerConfig
from .logging_setup import get_logger


class OllamaClient:
    """Client for Ollama API with tool calling support"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.servers: Dict[str, ServerConfig] = {}
        self.available_models: Dict[str, List[str]] = {}
        self.logger = get_logger()
        self.verbose = getattr(config, 'verbose', False)
    
    def discover_servers(self) -> Dict[str, List[str]]:
        """Discover available models on all configured servers"""
        self.logger.info("🔍 Discovering Ollama servers...")
        
        for server in self.config.servers:
            try:
                response = requests.get(f"{server.base_url}/api/tags", timeout=None)  # UNLIMITED
                if response.status_code == 200:
                    data = response.json()
                    server.models = [m["name"] for m in data.get("models", [])]
                    server.online = True
                    self.servers[server.host] = server
                    self.available_models[server.host] = server.models
                    self.logger.info(f"  ✓ {server.name} ({server.host}): {len(server.models)} models")
                else:
                    self.logger.warning(f"  ✗ {server.name}: HTTP {response.status_code}")
                    server.online = False
            except requests.Timeout:
                self.logger.warning(f"  ✗ {server.name}: Connection timeout")
                server.online = False
            except Exception as e:
                self.logger.warning(f"  ✗ {server.name}: {e}")
                server.online = False
        
        return self.available_models
    
    def get_model_for_task(self, task_type: str) -> Optional[Tuple[str, str]]:
        """Get the best available model for a task type"""
        
        # ENHANCED LOGGING: Track model selection process
        selection_log = []
        
        if task_type in self.config.model_assignments:
            model, preferred_host = self.config.model_assignments[task_type]
            selection_log.append(f"Preferred: {model} on {preferred_host}")
            
            # CRITICAL FIX: Check if preferred host is actually available
            if preferred_host in self.available_models and self.available_models[preferred_host]:
                for avail in self.available_models[preferred_host]:
                    if self._model_matches(avail, model):
                        self.logger.debug(f"  Model selection: Using preferred {avail} on {preferred_host}")
                        return (preferred_host, avail)
                selection_log.append(f"Preferred model not found on {preferred_host}")
            else:
                selection_log.append(f"Preferred host {preferred_host} not available or has no models")
                self.logger.warning(f"  Preferred host {preferred_host} is not available!")
            
            # Try other hosts for the same model
            for host, models in self.available_models.items():
                if not models:  # Skip hosts with no models
                    continue
                for avail in models:
                    if self._model_matches(avail, model):
                        self.logger.info(f"  Model selection: Using {avail} on {host} (preferred host unavailable)")
                        return (host, avail)
            
            selection_log.append(f"Preferred model {model} not found on any host")
        else:
            selection_log.append(f"No model assignment for task type: {task_type}")
        
        # Try fallbacks
        if task_type in self.config.model_fallbacks:
            selection_log.append(f"Trying fallbacks: {self.config.model_fallbacks[task_type]}")
            for fallback in self.config.model_fallbacks[task_type]:
                for host, models in self.available_models.items():
                    for avail in models:
                        if self._model_matches(avail, fallback):
                            self.logger.warning(f"  Model selection: Using fallback {avail} on {host}")
                            self.logger.warning(f"  Selection path: {' -> '.join(selection_log)}")
                            return (host, avail)
            selection_log.append("No fallback models available")
        
        # Last resort
        for host, models in self.available_models.items():
            if models:
                self.logger.error(f"  Model selection: Using LAST RESORT {models[0]} on {host}")
                self.logger.error(f"  Selection path: {' -> '.join(selection_log)}")
                return (host, models[0])
        
        self.logger.error(f"  Model selection FAILED: {' -> '.join(selection_log)}")
        return None
    
    def _model_matches(self, available: str, requested: str) -> bool:
        """Check if an available model matches the requested model"""
        if available == requested:
            return True
        req_base = requested.split(":")[0]
        avail_base = available.split(":")[0]
        return avail_base == req_base or available.startswith(requested)
    
    def chat(
        self,
        host: str,
        model: str,
        messages: List[Dict],
        tools: List[Dict] = None,
        temperature: float = 0.3,
        timeout: Optional[int] = None
    ) -> Dict:
        """
        Send a chat request with optional tool calling.
        """
        
        # Determine context window size based on model
        num_ctx = 8192  # Default for most models
        if "32b" in model or "70b" in model:
            num_ctx = 16384  # Larger context for bigger models
        elif "7b" in model or "3b" in model:
            num_ctx = 4096  # Smaller context for smaller models
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": num_ctx
            }
        }
        
        if tools:
            payload["tools"] = tools
        
        # VERBOSE: Log the prompt being sent
        self.logger.debug(f"═══ REQUEST TO {host}/{model} ═══")
        self.logger.debug(f"Temperature: {temperature}, Tools: {len(tools) if tools else 0}")
        
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            # Show first 500 chars of each message
            preview = content[:500] + "..." if len(content) > 500 else content
            self.logger.debug(f"  [{i}] {role}: {preview}")
        
        try:
            # Parse host to handle both "hostname" and "http://hostname:port" formats
            if host.startswith("http://") or host.startswith("https://"):
                # Host already includes protocol and possibly port
                base_url = host
                if ":11434" not in host and not host.endswith("/"):
                    base_url = f"{host}:11434"
            else:
                # Host is just hostname, add protocol and port
                base_url = f"http://{host}:11434"
            
            response = requests.post(
                f"{base_url}/api/chat",
                json=payload,
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                self._log_response_verbose(result)
                return result
            else:
                self.logger.error(f"API error: HTTP {response.status_code}")
                self.logger.error(f"Response body: {response.text[:500]}")
                return {"error": f"HTTP {response.status_code}"}
                
        except requests.Timeout:
            self.logger.error(f"Request timed out after {timeout}s")
            return {"error": "timeout"}
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return {"error": str(e)}
    
    def _log_response_verbose(self, response: Dict):
        """Log detailed response information"""
        message = response.get("message", {})
        content = message.get("content", "")
        tool_calls = message.get("tool_calls", [])
        
        self.logger.debug(f"═══ RESPONSE ═══")
        self.logger.debug(f"  Content length: {len(content)} chars")
        self.logger.debug(f"  Native tool_calls: {len(tool_calls)}")
        
        if tool_calls:
            for i, tc in enumerate(tool_calls):
                func = tc.get("function", {})
                self.logger.debug(f"    Tool[{i}]: {func.get('name', '?')}")
        
        # Show content preview (useful for debugging)
        if content:
            preview = content[:1000] + "..." if len(content) > 1000 else content
            self.logger.debug(f"  Content preview:\n{preview}")


class FunctionGemmaFormatter:
    """
    Uses functiongemma model to help format tool calls.
    Useful when a coding model outputs malformed JSON.
    """
    
    def __init__(self, client: OllamaClient):
        self.client = client
        self.logger = get_logger()
    
    def _find_gemma_host(self) -> Optional[str]:
        """Find a server with functiongemma available."""
        for host, models in self.client.available_models.items():
            for model in models:
                if 'functiongemma' in model.lower():
                    return host
        return None
    
    def format_tool_call(self, raw_output: str, available_tools: List[Dict]) -> Optional[Dict]:
        """
        Use functiongemma to extract/format a tool call from raw model output.
        """
        gemma_host = self._find_gemma_host()
        if not gemma_host:
            self.logger.debug("  functiongemma not available for formatting")
            return None
        
        # Build tool descriptions
        tool_descriptions = []
        for tool in available_tools:
            func = tool.get("function", {})
            name = func.get("name", "unknown")
            desc = func.get("description", "")
            params = func.get("parameters", {}).get("properties", {})
            param_list = ", ".join(params.keys())
            tool_descriptions.append(f"- {name}({param_list}): {desc}")
        
        tools_text = "\n".join(tool_descriptions)
        
        prompt = f"""Extract the tool call from this text. Output ONLY valid JSON.

Available tools:
{tools_text}

Text to parse:
{raw_output[:2000]}

Output format: {{"name": "tool_name", "arguments": {{"param": "value"}}}}
Output ONLY the JSON, nothing else:"""

        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = self.client.chat(
                gemma_host,
                "functiongemma:latest",
                messages,
                tools=None,
                temperature=0.1,
                timeout=None  # UNLIMITED
            )
            
            content = response.get("message", {}).get("content", "")
            if content:
                # Try to parse the response
                try:
                    data = json.loads(content.strip())
                    if "name" in data and "arguments" in data:
                        return {"function": data}
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            self.logger.debug(f"  functiongemma formatting failed: {e}")
        
        return None
    
    def validate_and_fix_tool_call(self, tool_call: Dict, available_tools: List[Dict], 
                                   file_content: str = None, error_message: str = None) -> Optional[Dict]:
        """
        Use FunctionGemma to validate and fix a tool call.
        
        This is especially useful for modify_python_file when original_code doesn't match.
        
        Args:
            tool_call: The tool call to validate/fix
            available_tools: List of available tools
            file_content: Optional file content for context
            error_message: Optional error message if this is a retry
            
        Returns:
            Fixed tool call or None if can't be fixed
        """
        gemma_host = self._find_gemma_host()
        if not gemma_host:
            return None
        
        func = tool_call.get('function', {})
        name = func.get('name', 'unknown')
        args = func.get('arguments', {})
        
        # Build context
        context_parts = []
        if error_message:
            context_parts.append(f"Previous error: {error_message}")
        if file_content:
            context_parts.append(f"File content (first 1000 chars):\n{file_content[:1000]}")
        
        context = "\n\n".join(context_parts) if context_parts else "No additional context"
        
        # Build tool descriptions
        tool_descriptions = []
        for tool in available_tools:
            t_func = tool.get("function", {})
            t_name = t_func.get("name", "unknown")
            t_desc = t_func.get("description", "")
            t_params = t_func.get("parameters", {}).get("properties", {})
            t_required = t_func.get("parameters", {}).get("required", [])
            
            param_list = []
            for p_name, p_info in t_params.items():
                req = " (required)" if p_name in t_required else ""
                param_list.append(f"{p_name}{req}")
            
            tool_descriptions.append(f"- {t_name}({', '.join(param_list)}): {t_desc}")
        
        tools_text = "\n".join(tool_descriptions)
        
        prompt = f"""You are a tool call validator. Fix this tool call if needed.

Tool call to validate:
{json.dumps({"name": name, "arguments": args}, indent=2)}

Available tools:
{tools_text}

Context:
{context}

Instructions:
1. Check if the tool name is correct
2. Check if all required parameters are present
3. For modify_python_file, ensure original_code EXACTLY matches the file content
4. Fix any issues you find

Output ONLY valid JSON in this format:
{{"name": "tool_name", "arguments": {{"param": "value"}}}}

Output the corrected tool call now:"""
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = self.client.chat(
                gemma_host,
                "functiongemma:latest",
                messages,
                tools=None,
                temperature=0.1,
                timeout=None  # UNLIMITED
            )
            
            content = response.get("message", {}).get("content", "")
            if content:
                # Try to parse the response
                try:
                    # Extract JSON from response
                    import re
                    json_match = re.search(r'\{[^{}]*"name"[^{}]*"arguments"[^{}]*\}', content, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group(0))
                        if "name" in data and "arguments" in data:
                            self.logger.info(f"  ✅ FunctionGemma validated/fixed tool call: {data['name']}")
                            return {"function": data}
                except json.JSONDecodeError as e:
                    self.logger.debug(f"  Failed to parse FunctionGemma response: {e}")
        except Exception as e:
            self.logger.debug(f"  FunctionGemma validation failed: {e}")
        
        return None


class ResponseParser:
    """Parses LLM responses, including fallback JSON extraction"""
    
    def __init__(self, client: OllamaClient = None):
        self.logger = get_logger()
        self.client = client
        self.gemma_formatter = FunctionGemmaFormatter(client) if client else None
    
    def parse_response(self, response: Dict, tools: List[Dict] = None) -> Tuple[List[Dict], str]:
        """
        Parse a response and extract tool calls.
        
        IMPORTANT: This method returns a TUPLE, not a dict!
        
        Returns:
            Tuple[List[Dict], str]: (tool_calls, content)
                - tool_calls: List of tool call dictionaries
                - content: Text content from the response
        """
        message = response.get("message", {})
        content = message.get("content", "")
        tool_calls = message.get("tool_calls", [])
        
        self.logger.debug(f"═══ PARSING RESPONSE ═══")
        self.logger.debug(f"  Native tool_calls: {len(tool_calls)}")
        self.logger.debug(f"  Content length: {len(content)}")
        
        if tool_calls:
            self.logger.debug(f"  Using {len(tool_calls)} native tool calls")
            for tc in tool_calls:
                func = tc.get("function", {})
                self.logger.debug(f"    → {func.get('name')}: {str(func.get('arguments', {}))[:100]}")
            return tool_calls, content
        
        if content:
            self.logger.debug(f"  No native tool_calls, attempting extraction from content...")
            self.logger.debug(f"  Content preview: {content[:300]}...")
            
            extracted = self._extract_tool_call_from_text(content)
            if extracted:
                func = extracted.get("function", {})
                self.logger.info("  Extracted tool call from text response")
                self.logger.debug(f"    → Extracted: {func.get('name')}")
                return [extracted], ""
            
            # Try functiongemma as last resort
            if self.gemma_formatter and tools:
                self.logger.debug("  Trying functiongemma for formatting...")
                gemma_result = self.gemma_formatter.format_tool_call(content, tools)
                if gemma_result:
                    self.logger.info("  Extracted tool call via functiongemma")
                    return [gemma_result], ""
            
            self.logger.debug("  No tool call could be extracted from content")
        
        return [], content
    
    def _extract_tool_call_from_text(self, text: str) -> Optional[Dict]:
        """Try to extract a tool call from text content"""
        
        # 1. Try to find ALL JSON blocks with "name" and "arguments" (handles embedded JSON)
        self.logger.debug("    Trying: find all JSON blocks with name/arguments")
        result = self._extract_all_json_blocks(text)
        if result:
            return result
        
        # 2. Try standard JSON format
        self.logger.debug("    Trying: standard tool call format {name, arguments}")
        result = self._try_standard_json(text)
        if result:
            return result
        
        # 3. Try to extract file creation with code block (handles malformed JSON)
        self.logger.debug("    Trying: code block extraction")
        result = self._extract_file_from_codeblock(text)
        if result:
            return result
        
        # 3. Look for direct {"tasks": [...]} format (common model output)
        self.logger.debug("    Trying: tasks JSON format")
        tasks = self._extract_tasks_json(text)
        if tasks:
            self.logger.debug(f"    ✓ Found tasks format with {len(tasks)} tasks")
            return {
                "function": {
                    "name": "create_task_plan",
                    "arguments": {"tasks": tasks}
                }
            }
        
        # 4. Try to extract filepath and code separately (for malformed JSON)
        self.logger.debug("    Trying: separate filepath/code extraction")
        result = self._extract_file_creation_robust(text)
        if result:
            return result
        
        # 5. Try aggressive JSON extraction
        self.logger.debug("    Trying: aggressive JSON extraction")
        result = self._extract_json_aggressive(text)
        if result:
            self.logger.debug(f"    ✓ Aggressive extraction found: {result.get('function', {}).get('name', '?')}")
            return result
        
        self.logger.debug("    ✗ All extraction methods failed")
        return None
    
    def _extract_all_json_blocks(self, text: str) -> Optional[Dict]:
        """
        Multi-layered extraction system to handle various AI response formats.
        Handles: JSON blocks, Python function calls, embedded JSON, etc.
        """
        # Layer 1: Try to extract Python function call syntax (e.g., modify_python_file(...))
        self.logger.debug("    Layer 1: Trying Python function call syntax")
        result = self._extract_function_call_syntax(text)
        if result:
            return result
        
        # Layer 2: Try to extract from markdown code blocks (with various preambles)
        self.logger.debug("    Layer 2: Trying markdown code blocks")
        code_blocks = re.findall(r'```(?:json|python|modify_python_file|try)?\s*\n([\s\S]*?)\n```', text)
        for block in code_blocks:
            # Try function call syntax first
            result = self._extract_function_call_syntax(block)
            if result:
                return result
            
            # Then try JSON with triple-quote conversion
            cleaned_block = self._convert_python_strings_to_json(block.strip())
            try:
                data = json.loads(cleaned_block)
                if isinstance(data, dict) and "name" in data and "arguments" in data:
                    self.logger.debug(f"    ✓ Found tool call in code block: {data['name']}")
                    return {
                        "function": {
                            "name": data["name"],
                            "arguments": data["arguments"]
                        }
                    }
            except json.JSONDecodeError as e:
                self.logger.debug(f"    ✗ JSON parse failed for block: {str(e)[:100]}")
                continue
        
        # If no code blocks, find all potential JSON blocks (anything between { and })
        json_blocks = []
        i = 0
        while i < len(text):
            if text[i] == '{':
                # Found start of potential JSON
                depth = 0
                start = i
                for j in range(i, len(text)):
                    if text[j] == '{':
                        depth += 1
                    elif text[j] == '}':
                        depth -= 1
                        if depth == 0:
                            # Found complete JSON block
                            json_blocks.append(text[start:j+1])
                            i = j + 1
                            break
                else:
                    i += 1
            else:
                i += 1
        
        # Try to parse each block and find one with "name" and "arguments"
        for block in json_blocks:
            try:
                data = json.loads(block)
                if isinstance(data, dict) and "name" in data and "arguments" in data:
                    self.logger.debug(f"    ✓ Found embedded JSON with tool call: {data['name']}")
                    return {
                        "function": {
                            "name": data["name"],
                            "arguments": data["arguments"]
                        }
                    }
            except json.JSONDecodeError:
                continue
        
        return None
    
    def _try_standard_json(self, text: str) -> Optional[Dict]:
        """Try to parse standard tool call JSON format"""
        # CRITICAL FIX: Strip markdown code blocks FIRST
        cleaned_text = self._clean_json(text)
        
        json_match = re.search(r'\{[\s\S]*"name"[\s\S]*"arguments"[\s\S]*\}', cleaned_text)
        if json_match:
            try:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                if "name" in data and "arguments" in data:
                    self.logger.debug(f"    ✓ Found standard format: {data['name']}")
                    return {
                        "function": {
                            "name": data["name"],
                            "arguments": data["arguments"]
                        }
                    }
            except json.JSONDecodeError as e:
                self.logger.debug(f"    ✗ JSON parse failed: {e}")
        return None
    
    def _extract_file_from_codeblock(self, text: str) -> Optional[Dict]:
        """Extract file creation when code is in a markdown code block"""
        
        # Pattern: filepath in JSON followed by code block
        # {"name": "create_python_file", "arguments": {"filepath": "...", "code": ...
        # Then look for ```python ... ```
        
        filepath_match = re.search(r'"filepath"\s*:\s*"([^"]+)"', text)
        if not filepath_match:
            return None
        
        filepath = filepath_match.group(1)
        
        # Look for code block
        code_match = re.search(r'```(?:python)?\s*\n([\s\S]*?)\n```', text)
        if code_match:
            code = code_match.group(1)
            if code.strip():
                self.logger.debug(f"    ✓ Extracted from code block: {filepath}")
                return {
                    "function": {
                        "name": "create_python_file",
                        "arguments": {
                            "filepath": filepath,
                            "code": code
                        }
                    }
                }
        
        return None
    
    def _extract_file_creation_robust(self, text: str) -> Optional[Dict]:
        """
        Robustly extract file creation from malformed JSON.
        Handles cases where code contains unescaped characters.
        """
        
        # Look for the tool name
        name_match = re.search(r'"name"\s*:\s*"(create_python_file|create_file)"', text)
        if not name_match:
            return None
        
        tool_name = name_match.group(1)
        
        # Look for filepath
        filepath_match = re.search(r'"filepath"\s*:\s*"([^"]+)"', text)
        if not filepath_match:
            return None
        
        filepath = filepath_match.group(1)
        
        # Try to extract code - look for "code": " then find the content
        code_start = text.find('"code"')
        if code_start == -1:
            return None
        
        # Find the start of the code string
        colon_pos = text.find(':', code_start)
        if colon_pos == -1:
            return None
        
        # Skip whitespace and find opening quote
        rest = text[colon_pos + 1:].lstrip()
        if not rest.startswith('"'):
            return None
        
        # Now we need to find where the code string ends
        # This is tricky because the code may contain unescaped quotes
        # Strategy: Find the closing pattern - either "}" or "\n}" or similar
        
        code_content = rest[1:]  # Skip opening quote
        
        # Try to find the end by looking for closing JSON patterns
        # Look for "}}" or "} }" at the end (closing arguments and main object)
        
        # Method 1: Look for the pattern that ends JSON
        end_patterns = [
            r'\n\s*"\s*\}\s*\}',  # newline, quote, }, }
            r'"\s*\}\s*\}\s*$',   # quote, }, } at end
            r'\n"\s*\}',          # newline, quote, }
        ]
        
        code = None
        for pattern in end_patterns:
            match = re.search(pattern, code_content)
            if match:
                code = code_content[:match.start()]
                break
        
        if not code:
            # Last resort: take everything up to the last }
            last_brace = code_content.rfind('}')
            if last_brace > 100:  # Sanity check
                # Find the quote before the brace
                quote_pos = code_content.rfind('"', 0, last_brace)
                if quote_pos > 0:
                    code = code_content[:quote_pos]
        
        if code:
            # Unescape the code
            code = code.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
            
            if len(code) > 50:  # Sanity check
                self.logger.debug(f"    ✓ Robust extraction: {filepath} ({len(code)} chars)")
                return {
                    "function": {
                        "name": tool_name,
                        "arguments": {
                            "filepath": filepath,
                            "code": code
                        }
                    }
                }
        
        return None
    
    def _extract_tasks_json(self, text: str) -> Optional[List[Dict]]:
        """Extract tasks array from various JSON formats"""
        
        # Try to find {"tasks": [...]}
        tasks_obj_match = re.search(r'\{\s*"tasks"\s*:\s*\[([\s\S]*?)\]\s*\}', text)
        if tasks_obj_match:
            try:
                json_str = '{"tasks": [' + tasks_obj_match.group(1) + ']}'
                data = json.loads(json_str)
                tasks = data.get("tasks", [])
                if tasks and self._validate_tasks(tasks):
                    return tasks
            except json.JSONDecodeError:
                pass
        
        # Try to find standalone array of task objects
        array_match = re.search(r'\[\s*\{[\s\S]*?"description"[\s\S]*?\}\s*\]', text)
        if array_match:
            try:
                json_str = self._clean_json(array_match.group(0))
                tasks = json.loads(json_str)
                if isinstance(tasks, list) and tasks and self._validate_tasks(tasks):
                    return tasks
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON in code blocks
        code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if code_block_match:
            try:
                json_str = code_block_match.group(1).strip()
                data = json.loads(json_str)
                
                if isinstance(data, dict) and "tasks" in data:
                    tasks = data["tasks"]
                elif isinstance(data, list):
                    tasks = data
                else:
                    tasks = None
                
                if tasks and self._validate_tasks(tasks):
                    return tasks
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _validate_tasks(self, tasks: List) -> bool:
        """Validate that tasks list contains valid task objects"""
        if not isinstance(tasks, list) or not tasks:
            return False
        
        for task in tasks:
            if not isinstance(task, dict):
                return False
            if "description" not in task and "task" not in task and "name" not in task:
                return False
        
        return True
    
    def _normalize_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """Normalize task objects to standard format"""
        normalized = []
        
        for i, task in enumerate(tasks):
            norm = {
                "description": task.get("description") or task.get("task") or task.get("name", ""),
                "target_file": task.get("target_file") or task.get("file") or task.get("filepath", ""),
                "priority": task.get("priority", i + 1),
                "dependencies": task.get("dependencies", []),
            }
            
            if not norm["target_file"] and norm["description"]:
                file_match = re.search(r'[`"\']?(\w+(?:/\w+)*\.py)[`"\']?', norm["description"])
                if file_match:
                    norm["target_file"] = file_match.group(1)
            
            if norm["description"]:
                normalized.append(norm)
        
        return normalized
    
    def _extract_function_call_syntax(self, text: str) -> Optional[Dict]:
        """
        Extract tool calls from Python function call syntax.
        Handles formats like: modify_python_file(filepath="...", original_code="...", new_code="...")
        """
        # Common tool name patterns (snake_case function names)
        # Match any valid Python function name followed by opening parenthesis
        tool_pattern = r'([a-z_][a-z0-9_]*)\s*\('
        matches = re.finditer(tool_pattern, text)
        
        # Try each potential tool name found
        potential_tools = [m.group(1) for m in matches]
        
        # Prioritize known refactoring and file operation tools
        known_tools = [
            'create_issue_report', 'request_developer_review', 
            'merge_file_implementations', 'cleanup_redundant_files',
            'compare_file_implementations', 'detect_duplicate_implementations',
            'modify_python_file', 'create_python_file', 'create_file',
            'read_file', 'search_code', 'list_directory', 'report_issue',
            'move_file', 'rename_file', 'restructure_directory',
            'insert_after', 'insert_before', 'replace_between', 'full_file_rewrite',
            'str_replace', 'update_refactoring_task', 'validate_architecture'
        ]
        
        # Check known tools first, then any other potential tools
        tools_to_check = known_tools + [t for t in potential_tools if t not in known_tools]
        
        for tool_name in tools_to_check:
            # Look for tool_name( ... ) with proper bracket matching
            pattern = rf'{tool_name}\s*\('
            match = re.search(pattern, text)
            
            if not match:
                continue
            
            # Find the matching closing parenthesis
            start = match.end()
            depth = 1
            end = start
            
            for i in range(start, len(text)):
                if text[i] == '(':
                    depth += 1
                elif text[i] == ')':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            
            if depth != 0:
                continue  # Unmatched parentheses
            
            args_str = text[start:end]
            
            # Parse the arguments - handle multi-line strings with escaped quotes
            arguments = {}
            
            # Pattern to match key="value" where value can contain escaped quotes and newlines
            # This handles: key="value", key='value', key="""value""", key='''value'''
            arg_pattern = r'(\w+)\s*=\s*(?:"""([\s\S]*?)"""|\'\'\'([\s\S]*?)\'\'\'|"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\')'
            
            for arg_match in re.finditer(arg_pattern, args_str):
                key = arg_match.group(1)
                # Get the value from whichever group matched
                value = (arg_match.group(2) or arg_match.group(3) or 
                        arg_match.group(4) or arg_match.group(5) or "")
                
                # Unescape the value if it was in quotes (not triple quotes)
                if arg_match.group(4) or arg_match.group(5):
                    # Handle escaped characters
                    value = value.replace('\\n', '\n')
                    value = value.replace('\\t', '\t')
                    value = value.replace('\\r', '\r')
                    value = value.replace(r'&quot;', '"')
                    value = value.replace("\\'", "'")
                    value = value.replace('\\\\', '\\')
                
                arguments[key] = value
            
            if arguments:
                self.logger.debug(f"    ✓ Found function call syntax: {tool_name}")
                self.logger.debug(f"      Arguments: {list(arguments.keys())}")
                return {
                    "function": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
        
        return None
    
    def _convert_python_strings_to_json(self, text: str) -> str:
        """
        Convert Python-style triple-quoted strings to JSON-compatible format.
        AI models often use triple quotes which is valid Python but not valid JSON.
        """
        # Replace triple-quoted strings with properly escaped JSON strings
        # Pattern: """content""" -> "content" (with proper escaping)
        
        def replace_triple_quotes(match):
            content = match.group(1)
            # Escape backslashes and quotes for JSON
            content = content.replace('\\', '\\\\')
            content = content.replace('"', r'&quot;')
            content = content.replace('\n', '\\n')
            content = content.replace('\r', '\\r')
            content = content.replace('\t', '\\t')
            return f'"{content}"'
        
        # Match triple-quoted strings (both """ and ''')
        text = re.sub(r'"""([\s\S]*?)"""', replace_triple_quotes, text)
        text = re.sub(r"'''([\s\S]*?)'''", replace_triple_quotes, text)
        
        return text
    
    def _clean_json(self, text: str) -> str:
        """Clean up JSON text for parsing"""
        text = re.sub(r'^```json?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return text.strip()
    
    def _extract_json_aggressive(self, text: str) -> Optional[Dict]:
        """Aggressively try to extract JSON from malformed text"""
        start = text.find('{')
        if start == -1:
            return None
        
        depth = 0
        end = start
        for i, char in enumerate(text[start:], start):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        
        if depth != 0:
            return None
        
        json_str = text[start:end]
        
        try:
            data = json.loads(json_str)
            
            if "name" in data and "arguments" in data:
                return {
                    "function": {
                        "name": data["name"],
                        "arguments": data["arguments"]
                    }
                }
            
            if "tasks" in data and isinstance(data["tasks"], list):
                return {
                    "function": {
                        "name": "create_task_plan",
                        "arguments": {"tasks": data["tasks"]}
                    }
                }
            
            # Check for file creation pattern
            if "filepath" in data and "code" in data:
                return {
                    "function": {
                        "name": "create_python_file",
                        "arguments": data
                    }
                }
        except json.JSONDecodeError:
            pass
        
        return None
    
    def extract_tasks_from_text(self, text: str) -> List[Dict]:
        """Extract tasks from plain text (fallback for planning)"""
        tasks = []
        
        # First, try to extract JSON tasks
        json_tasks = self._extract_tasks_json(text)
        if json_tasks:
            return self._normalize_tasks(json_tasks)
        
        # Fall back to regex-based extraction
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            patterns = [
                r'^(?:\d+[\.\)]\s*)(.+)$',
                r'^[-\*•]\s+(.+)$',
                r'^(?:Task\s*\d*[:\.]?\s*)(.+)$',
                r'^\[\d+\]\s*(.+)$',
                r'^(?:Step\s*\d*[:\.]?\s*)(.+)$',
            ]
            
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    desc = match.group(1).strip()
                    
                    if len(desc) < 10:
                        continue
                    if desc.startswith('#'):
                        continue
                    if desc.lower().startswith(('here', 'the following', 'below')):
                        continue
                    
                    file_match = re.search(r'[`"\']?([\w/]+\.py)[`"\']?', desc)
                    target_file = file_match.group(1) if file_match else ""
                    
                    tasks.append({
                        "description": desc,
                        "target_file": target_file,
                        "priority": len(tasks) + 1,
                        "dependencies": []
                    })
                    break
        
        if not tasks:
            for line in lines:
                line = line.strip()
                if '.py' in line and len(line) > 15:
                    file_match = re.search(r'[`"\']?([\w/]+\.py)[`"\']?', line)
                    if file_match:
                        tasks.append({
                            "description": line,
                            "target_file": file_match.group(1),
                            "priority": len(tasks) + 1,
                            "dependencies": []
                        })
        
        return tasks[:15]
