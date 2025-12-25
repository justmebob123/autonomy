"""
Specialist Agent System

Multiple AI models working together with shared conversation context.
Each specialist has expertise in specific areas and can call tools.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
from dataclasses import dataclass

from .conversation_thread import ConversationThread, Message


@dataclass
class SpecialistConfig:
    """Configuration for a specialist agent"""
    name: str
    model: str
    host: str
    expertise: str
    system_prompt: str
    temperature: float = 0.3


class SpecialistAgent:
    """
    A specialist AI agent with specific expertise.
    
    Can:
    - Access full conversation history
    - Call tools to gather information
    - Provide analysis and recommendations
    - Collaborate with other specialists
    """
    
    def __init__(self, config: SpecialistConfig, client, logger: logging.Logger):
        self.config = config
        self.client = client
        self.logger = logger
    
    def analyze(self, thread: ConversationThread, tools: List[Dict]) -> Dict:
        """
        Analyze the issue using full conversation context.
        
        Returns analysis with:
        - findings: What the specialist discovered
        - recommendations: Suggested actions
        - tool_calls: Tools the specialist wants to call
        - confidence: Confidence level (0-1)
        """
        
        # Build prompt with full context
        prompt = self._build_analysis_prompt(thread)
        
        # Get conversation history
        messages = thread.get_conversation_history()
        
        # Add specialist's analysis request
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Call the specialist model
        response = self.client.chat(
            self.config.host,
            self.config.model,
            messages,
            tools,
            temperature=self.config.temperature,
            timeout=300
        )
        
        if "error" in response:
            return {
                "specialist": self.config.name,
                "error": response["error"],
                "findings": [],
                "recommendations": [],
                "tool_calls": [],
                "confidence": 0.0
            }
        
        # Parse response
        from .client import ResponseParser
        parser = ResponseParser(self.logger)
        tool_calls, text_response = parser.parse_response(response)
        
        # Extract analysis from response
        analysis = {
            "specialist": self.config.name,
            "expertise": self.config.expertise,
            "findings": self._extract_findings(text_response),
            "recommendations": self._extract_recommendations(text_response),
            "tool_calls": tool_calls,
            "raw_response": text_response,
            "confidence": self._estimate_confidence(text_response)
        }
        
        return analysis
    
    def _build_analysis_prompt(self, thread: ConversationThread) -> str:
        """Build analysis prompt with full context"""
        
        prompt = f"""# Specialist Analysis Request

You are **{self.config.name}**, a specialist in {self.config.expertise}.

## Your Role
{self.config.system_prompt}

## Current Situation
{thread.get_comprehensive_context()}

## Your Task
1. **Analyze** the issue using your expertise in {self.config.expertise}
2. **Use tools** to gather any additional information you need
3. **Provide findings** - What did you discover?
4. **Make recommendations** - What should be done next?

## Available Tools
You have access to all debugging tools. Use them to:
- Read files
- Search code
- Execute commands (non-sudo)
- Analyze patterns
- Check syntax
- Examine whitespace
- Compare versions

## Output Format
Provide your analysis in this format:

### Findings
- List your key discoveries
- Include evidence from tool calls
- Reference specific lines/code

### Recommendations
- Suggest specific actions
- Prioritize by importance
- Explain your reasoning

### Confidence
Rate your confidence (0-100%) and explain why.

Remember: You're collaborating with other specialists. Build on their analysis and add your unique perspective.
"""
        
        return prompt
    
    def _extract_findings(self, response: str) -> List[str]:
        """Extract findings from response"""
        findings = []
        
        if "### Findings" in response or "## Findings" in response:
            # Extract findings section
            lines = response.split('\n')
            in_findings = False
            
            for line in lines:
                if "Findings" in line and ("#" in line or "**" in line):
                    in_findings = True
                    continue
                
                if in_findings:
                    if line.startswith("###") or line.startswith("##"):
                        break
                    
                    if line.strip().startswith("-") or line.strip().startswith("*"):
                        findings.append(line.strip().lstrip("-*").strip())
        
        return findings
    
    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract recommendations from response"""
        recommendations = []
        
        if "### Recommendations" in response or "## Recommendations" in response:
            lines = response.split('\n')
            in_recommendations = False
            
            for line in lines:
                if "Recommendations" in line and ("#" in line or "**" in line):
                    in_recommendations = True
                    continue
                
                if in_recommendations:
                    if line.startswith("###") or line.startswith("##"):
                        break
                    
                    if line.strip().startswith("-") or line.strip().startswith("*"):
                        recommendations.append(line.strip().lstrip("-*").strip())
        
        return recommendations
    
    def _estimate_confidence(self, response: str) -> float:
        """Estimate confidence from response"""
        
        # Look for explicit confidence statements
        if "confidence" in response.lower():
            import re
            # Look for percentage
            match = re.search(r'(\d+)%', response)
            if match:
                return float(match.group(1)) / 100.0
        
        # Estimate based on language
        high_confidence_words = ["clearly", "definitely", "certainly", "obvious"]
        low_confidence_words = ["might", "possibly", "maybe", "unclear", "uncertain"]
        
        response_lower = response.lower()
        
        high_count = sum(1 for word in high_confidence_words if word in response_lower)
        low_count = sum(1 for word in low_confidence_words if word in response_lower)
        
        if high_count > low_count:
            return 0.8
        elif low_count > high_count:
            return 0.4
        else:
            return 0.6


class SpecialistTeam:
    """
    Manages a team of specialist agents working together.
    """
    
    def __init__(self, client, logger: logging.Logger):
        self.client = client
        self.logger = logger
        self.specialists: Dict[str, SpecialistAgent] = {}
        
        # Initialize specialists
        self._initialize_specialists()
    
    def _initialize_specialists(self):
        """Initialize the specialist team"""
        
        # Whitespace & Formatting Specialist
        self.add_specialist(SpecialistConfig(
            name="Whitespace Analyst",
            model="qwen2.5-coder:32b",
            host="ollama02.thiscluster.net",
            expertise="whitespace, indentation, and formatting analysis",
            system_prompt="""You are an expert in analyzing whitespace and formatting issues in code.

Your expertise includes:
- Detecting tab vs space inconsistencies
- Analyzing indentation levels
- Identifying line ending issues (CRLF vs LF)
- Finding formatting mismatches
- Comparing code formatting across attempts

When analyzing, use tools to:
- Read files and examine exact whitespace
- Compare different versions
- Identify patterns in formatting

Provide precise, actionable findings about whitespace issues."""
        ))
        
        # Syntax & Structure Specialist
        self.add_specialist(SpecialistConfig(
            name="Syntax Analyst",
            model="qwen2.5-coder:32b",
            host="ollama02.thiscluster.net",
            expertise="Python syntax and code structure",
            system_prompt="""You are an expert in Python syntax and code structure.

Your expertise includes:
- Identifying syntax errors
- Detecting missing colons, brackets, quotes
- Analyzing code structure
- Finding logical errors
- Validating Python semantics

When analyzing, use tools to:
- Check syntax validity
- Examine AST structure
- Compare working vs broken code
- Test code snippets

Provide specific, line-by-line syntax analysis."""
        ))
        
        # Code Pattern Specialist
        self.add_specialist(SpecialistConfig(
            name="Pattern Analyst",
            model="deepseek-coder-v2",
            host="ollama02.thiscluster.net",
            expertise="code patterns and similar code detection",
            system_prompt="""You are an expert in finding and analyzing code patterns.

Your expertise includes:
- Finding similar code blocks
- Detecting code duplication
- Identifying refactoring opportunities
- Analyzing code evolution
- Pattern matching across files

When analyzing, use tools to:
- Search for similar code
- Compare code blocks
- Examine file history
- Find related implementations

Provide insights about code patterns and similarities."""
        ))
        
        # Root Cause Specialist
        self.add_specialist(SpecialistConfig(
            name="Root Cause Analyst",
            model="qwen2.5:14b",
            host="ollama02.thiscluster.net",
            expertise="root cause analysis and debugging strategy",
            system_prompt="""You are an expert in root cause analysis and debugging strategy.

Your expertise includes:
- Identifying underlying causes
- Analyzing failure patterns
- Developing debugging strategies
- Synthesizing multiple perspectives
- Making strategic recommendations

When analyzing, use tools to:
- Examine error patterns
- Review attempt history
- Analyze specialist findings
- Test hypotheses

Provide strategic, high-level analysis and recommendations."""
        ))
    
    def add_specialist(self, config: SpecialistConfig):
        """Add a specialist to the team"""
        specialist = SpecialistAgent(config, self.client, self.logger)
        self.specialists[config.name] = specialist
    
    def consult_specialist(self, specialist_name: str, 
                          thread: ConversationThread,
                          tools: List[Dict]) -> Dict:
        """Consult a specific specialist"""
        
        if specialist_name not in self.specialists:
            return {
                "error": f"Specialist '{specialist_name}' not found",
                "available": list(self.specialists.keys())
            }
        
        self.logger.info(f"  🔬 Consulting {specialist_name}...")
        
        specialist = self.specialists[specialist_name]
        analysis = specialist.analyze(thread, tools)
        
        # Add to thread
        thread.add_specialist_analysis(specialist_name, analysis)
        
        return analysis
    
    def consult_team(self, thread: ConversationThread, 
                    tools: List[Dict],
                    specialists: Optional[List[str]] = None) -> Dict:
        """
        Consult multiple specialists in sequence.
        
        Each specialist sees the previous specialists' analysis.
        """
        
        if specialists is None:
            # Default consultation order
            specialists = [
                "Whitespace Analyst",
                "Syntax Analyst",
                "Pattern Analyst",
                "Root Cause Analyst"
            ]
        
        team_analysis = {
            "specialists_consulted": [],
            "analyses": {},
            "consensus_findings": [],
            "consensus_recommendations": [],
            "confidence": 0.0
        }
        
        for specialist_name in specialists:
            if specialist_name not in self.specialists:
                self.logger.warning(f"  ⚠️  Specialist '{specialist_name}' not available")
                continue
            
            analysis = self.consult_specialist(specialist_name, thread, tools)
            
            if "error" not in analysis:
                team_analysis["specialists_consulted"].append(specialist_name)
                team_analysis["analyses"][specialist_name] = analysis
                
                # Aggregate findings
                team_analysis["consensus_findings"].extend(analysis.get("findings", []))
                team_analysis["consensus_recommendations"].extend(analysis.get("recommendations", []))
                
                # Update confidence (average)
                confidences = [a.get("confidence", 0.0) for a in team_analysis["analyses"].values()]
                team_analysis["confidence"] = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Deduplicate and prioritize
        team_analysis["consensus_findings"] = list(set(team_analysis["consensus_findings"]))
        team_analysis["consensus_recommendations"] = list(set(team_analysis["consensus_recommendations"]))
        
        return team_analysis
    
    def get_best_specialist_for_failure(self, failure_type: str) -> str:
        """Get the best specialist for a specific failure type"""
        
        specialist_map = {
            "CODE_NOT_FOUND": "Pattern Analyst",
            "SYNTAX_ERROR": "Syntax Analyst",
            "INDENTATION_ERROR": "Whitespace Analyst",
            "VERIFICATION_FAILURE": "Root Cause Analyst",
            "IMPORT_ERROR": "Syntax Analyst"
        }
        
        return specialist_map.get(failure_type, "Root Cause Analyst")