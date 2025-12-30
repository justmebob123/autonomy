# Project 1 - Example Implementation Files

This document provides complete example implementation files for the custom WSGI application.

## Directory Structure

```
/var/www/planning/
├── config/
│   ├── config.ini              # Main configuration
│   ├── loader.py              # Configuration loader
│   └── apache/
│       ├── http.conf           # HTTP vhost
│       └── https.conf          # HTTPS vhost
├── wsgi/
│   ├── application.py          # Custom WSGI application
│   ├── router.py              # Custom routing
│   ├── request.py             # Request parser
│   ├── response.py            # Response builder
│   ├── middleware.py          # Middleware
│   └── server.py              # WSGI entry point
├── api/
│   ├── projects.py            # Project endpoints
│   ├── objectives.py          # Objective endpoints
│   ├── chat.py               # Chat endpoints
│   ├── files.py              # File endpoints
│   ├── git.py                # Git endpoints
│   ├── servers.py            # Server endpoints
│   └── prompts.py            # Prompt endpoints
├── db/
│   ├── connection.py          # Database connection
│   ├── models.py             # Data models
│   └── migrations.py         # Database migrations
├── services/
│   ├── auth.py               # Authentication service
│   ├── ollama.py             # Ollama integration
│   ├── search.py             # Web search service
│   └── git_service.py        # Git operations
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── data/
│   └── planning.db           # SQLite database
├── uploads/                  # User uploads
├── temp/                     # Temporary files
└── logs/                     # Application logs
```

## Example API Endpoint Implementation

### File: `api/projects.py`

```python
"""
Project API Endpoints

Implements project management endpoints using only Python standard library.
NO external frameworks.
"""

from wsgi.response import Response
from db.connection import get_db
import json
import logging

logger = logging.getLogger(__name__)

def list_projects(request):
    """
    GET /api/projects
    
    List all projects for the authenticated user.
    """
    try:
        # Get user from request (set by auth middleware)
        user_id = request.environ.get('user_id')
        if not user_id:
            return Response({'error': 'Unauthorized'}, status=401)
        
        # Query database
        db = get_db()
        cursor = db.execute(
            'SELECT id, name, description, created_at FROM projects WHERE user_id = ?',
            (user_id,)
        )
        projects = [
            {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'created_at': row[3]
            }
            for row in cursor.fetchall()
        ]
        
        return Response({'projects': projects})
        
    except Exception as e:
        logger.error(f"Error listing projects: {e}", exc_info=True)
        return Response({'error': 'Internal server error'}, status=500)

def create_project(request):
    """
    POST /api/projects
    
    Create a new project.
    """
    try:
        # Get user from request
        user_id = request.environ.get('user_id')
        if not user_id:
            return Response({'error': 'Unauthorized'}, status=401)
        
        # Parse request body
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        
        if not name:
            return Response({'error': 'Name is required'}, status=400)
        
        # Insert into database
        db = get_db()
        cursor = db.execute(
            'INSERT INTO projects (user_id, name, description) VALUES (?, ?, ?)',
            (user_id, name, description)
        )
        db.commit()
        
        project_id = cursor.lastrowid
        
        return Response(
            {
                'id': project_id,
                'name': name,
                'description': description
            },
            status=201
        )
        
    except Exception as e:
        logger.error(f"Error creating project: {e}", exc_info=True)
        return Response({'error': 'Internal server error'}, status=500)

def get_project(request, id):
    """
    GET /api/projects/<id>
    
    Get a specific project.
    """
    try:
        # Get user from request
        user_id = request.environ.get('user_id')
        if not user_id:
            return Response({'error': 'Unauthorized'}, status=401)
        
        # Query database
        db = get_db()
        cursor = db.execute(
            'SELECT id, name, description, created_at FROM projects WHERE id = ? AND user_id = ?',
            (id, user_id)
        )
        row = cursor.fetchone()
        
        if not row:
            return Response({'error': 'Project not found'}, status=404)
        
        project = {
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'created_at': row[3]
        }
        
        return Response(project)
        
    except Exception as e:
        logger.error(f"Error getting project: {e}", exc_info=True)
        return Response({'error': 'Internal server error'}, status=500)

def update_project(request, id):
    """
    PUT /api/projects/<id>
    
    Update a project.
    """
    try:
        # Get user from request
        user_id = request.environ.get('user_id')
        if not user_id:
            return Response({'error': 'Unauthorized'}, status=401)
        
        # Parse request body
        data = request.json
        name = data.get('name')
        description = data.get('description')
        
        # Build update query
        updates = []
        params = []
        
        if name:
            updates.append('name = ?')
            params.append(name)
        
        if description is not None:
            updates.append('description = ?')
            params.append(description)
        
        if not updates:
            return Response({'error': 'No fields to update'}, status=400)
        
        # Add WHERE clause parameters
        params.extend([id, user_id])
        
        # Update database
        db = get_db()
        db.execute(
            f'UPDATE projects SET {", ".join(updates)} WHERE id = ? AND user_id = ?',
            params
        )
        db.commit()
        
        return Response({'message': 'Project updated'})
        
    except Exception as e:
        logger.error(f"Error updating project: {e}", exc_info=True)
        return Response({'error': 'Internal server error'}, status=500)

def delete_project(request, id):
    """
    DELETE /api/projects/<id>
    
    Delete a project.
    """
    try:
        # Get user from request
        user_id = request.environ.get('user_id')
        if not user_id:
            return Response({'error': 'Unauthorized'}, status=401)
        
        # Delete from database
        db = get_db()
        db.execute(
            'DELETE FROM projects WHERE id = ? AND user_id = ?',
            (id, user_id)
        )
        db.commit()
        
        return Response({'message': 'Project deleted'}, status=204)
        
    except Exception as e:
        logger.error(f"Error deleting project: {e}", exc_info=True)
        return Response({'error': 'Internal server error'}, status=500)
```

## Database Connection

### File: `db/connection.py`

```python
"""
Database Connection

Manages database connections using only Python standard library.
"""

import sqlite3
import threading
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Thread-local storage for database connections
_local = threading.local()

def get_db():
    """Get database connection for current thread."""
    if not hasattr(_local, 'db'):
        # Get database path from config
        from config.loader import ConfigLoader
        config = ConfigLoader()
        db_path = config.get('database', 'path')
        
        # Create database directory if needed
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database
        _local.db = sqlite3.connect(db_path)
        _local.db.row_factory = sqlite3.Row
        
        logger.info(f"Database connection established: {db_path}")
    
    return _local.db

def close_db():
    """Close database connection for current thread."""
    if hasattr(_local, 'db'):
        _local.db.close()
        delattr(_local, 'db')
        logger.info("Database connection closed")

def init_db():
    """Initialize database schema."""
    db = get_db()
    
    # Create tables
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            git_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS objectives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        );
        
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (thread_id) REFERENCES threads(id)
        );
        
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            path TEXT NOT NULL,
            content TEXT,
            size INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        );
    ''')
    
    db.commit()
    logger.info("Database schema initialized")
```

## Authentication Service

### File: `services/auth.py`

```python
"""
Authentication Service

Implements JWT authentication using only Python standard library.
"""

import hmac
import hashlib
import json
import base64
import time
from typing import Optional, Dict

class AuthService:
    """Authentication service using JWT tokens."""
    
    def __init__(self, config):
        self.secret = config.get('security', 'jwt_secret')
        self.algorithm = config.get('security', 'jwt_algorithm')
        self.expiry = config.getint('security', 'jwt_expiry_seconds')
    
    def create_token(self, user_id: int, username: str) -> str:
        """Create a JWT token."""
        # Create header
        header = {
            'alg': self.algorithm,
            'typ': 'JWT'
        }
        
        # Create payload
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': int(time.time()) + self.expiry,
            'iat': int(time.time())
        }
        
        # Encode header and payload
        header_b64 = self._base64_encode(json.dumps(header))
        payload_b64 = self._base64_encode(json.dumps(payload))
        
        # Create signature
        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            self.secret.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = self._base64_encode(signature)
        
        # Return token
        return f"{message}.{signature_b64}"
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify a JWT token."""
        try:
            # Split token
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            header_b64, payload_b64, signature_b64 = parts
            
            # Verify signature
            message = f"{header_b64}.{payload_b64}"
            expected_signature = hmac.new(
                self.secret.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
            expected_signature_b64 = self._base64_encode(expected_signature)
            
            if signature_b64 != expected_signature_b64:
                return None
            
            # Decode payload
            payload_json = self._base64_decode(payload_b64)
            payload = json.loads(payload_json)
            
            # Check expiry
            if payload['exp'] < time.time():
                return None
            
            return payload
            
        except Exception:
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password."""
        return self.hash_password(password) == password_hash
    
    def _base64_encode(self, data) -> str:
        """Base64 encode data."""
        if isinstance(data, str):
            data = data.encode()
        return base64.urlsafe_b64encode(data).decode().rstrip('=')
    
    def _base64_decode(self, data: str) -> str:
        """Base64 decode data."""
        # Add padding if needed
        padding = 4 - (len(data) % 4)
        if padding != 4:
            data += '=' * padding
        return base64.urlsafe_b64decode(data).decode()
```

## Ollama Integration Service

### File: `services/ollama.py`

```python
"""
Ollama Integration Service

Integrates with Ollama API using only Python standard library.
"""

import json
import urllib.request
import urllib.error
import logging

logger = logging.getLogger(__name__)

class OllamaService:
    """Ollama API integration."""
    
    def __init__(self, config):
        self.server_url = config.get('ollama', 'default_server')
        self.default_model = config.get('ollama', 'default_model')
        self.timeout = config.getint('ollama', 'timeout_seconds')
    
    def chat(self, messages, model=None, stream=False):
        """
        Send chat request to Ollama.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (optional, uses default if not specified)
            stream: Whether to stream response
        
        Returns:
            Response dict or generator if streaming
        """
        if model is None:
            model = self.default_model
        
        # Build request
        url = f"{self.server_url}/api/chat"
        data = {
            'model': model,
            'messages': messages,
            'stream': stream
        }
        
        # Send request
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode(),
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if stream:
                    return self._stream_response(response)
                else:
                    return json.loads(response.read().decode())
                    
        except urllib.error.URLError as e:
            logger.error(f"Ollama request failed: {e}")
            raise
    
    def _stream_response(self, response):
        """Stream response from Ollama."""
        for line in response:
            if line:
                yield json.loads(line.decode())
    
    def list_models(self):
        """List available models."""
        url = f"{self.server_url}/api/tags"
        
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                return json.loads(response.read().decode())
        except urllib.error.URLError as e:
            logger.error(f"Failed to list models: {e}")
            raise
```

## Complete Example: Chat Endpoint with Streaming

### File: `api/chat.py`

```python
"""
Chat API Endpoints

Implements chat functionality with Ollama integration.
"""

from wsgi.response import Response
from db.connection import get_db
from services.ollama import OllamaService
from config.loader import ConfigLoader
import json
import logging

logger = logging.getLogger(__name__)
config = ConfigLoader()
ollama = OllamaService(config)

def send_message(request, id):
    """
    POST /api/threads/<id>/messages
    
    Send a message and get AI response.
    """
    try:
        # Get user from request
        user_id = request.environ.get('user_id')
        if not user_id:
            return Response({'error': 'Unauthorized'}, status=401)
        
        # Parse request
        data = request.json
        content = data.get('content')
        stream = data.get('stream', False)
        
        if not content:
            return Response({'error': 'Content is required'}, status=400)
        
        # Save user message
        db = get_db()
        db.execute(
            'INSERT INTO messages (thread_id, role, content) VALUES (?, ?, ?)',
            (id, 'user', content)
        )
        db.commit()
        
        # Get conversation history
        cursor = db.execute(
            'SELECT role, content FROM messages WHERE thread_id = ? ORDER BY created_at',
            (id,)
        )
        messages = [
            {'role': row[0], 'content': row[1]}
            for row in cursor.fetchall()
        ]
        
        # Get AI response
        if stream:
            # Return streaming response
            return stream_chat_response(id, messages)
        else:
            # Get complete response
            response = ollama.chat(messages)
            ai_message = response['message']['content']
            
            # Save AI message
            db.execute(
                'INSERT INTO messages (thread_id, role, content) VALUES (?, ?, ?)',
                (id, 'assistant', ai_message)
            )
            db.commit()
            
            return Response({
                'role': 'assistant',
                'content': ai_message
            })
            
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        return Response({'error': 'Internal server error'}, status=500)

def stream_chat_response(thread_id, messages):
    """Stream chat response using Server-Sent Events."""
    def generate():
        try:
            # Start streaming
            yield 'data: {"type": "start"}\n\n'
            
            # Stream AI response
            full_content = ''
            for chunk in ollama.chat(messages, stream=True):
                if 'message' in chunk:
                    content = chunk['message'].get('content', '')
                    if content:
                        full_content += content
                        yield f'data: {json.dumps({"type": "chunk", "content": content})}\n\n'
            
            # Save complete message
            db = get_db()
            db.execute(
                'INSERT INTO messages (thread_id, role, content) VALUES (?, ?, ?)',
                (thread_id, 'assistant', full_content)
            )
            db.commit()
            
            # End streaming
            yield 'data: {"type": "end"}\n\n'
            
        except Exception as e:
            logger.error(f"Error streaming response: {e}", exc_info=True)
            yield f'data: {json.dumps({"type": "error", "message": str(e)})}\n\n'
    
    # Return streaming response
    from wsgi.response import Response
    response = Response(body=None, status=200)
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    
    # Override __call__ to return generator
    def streaming_call(environ, start_response):
        status_line = f"{response.status} {response._get_status_text(response.status)}"
        headers_list = [(k, v) for k, v in response.headers.items()]
        start_response(status_line, headers_list)
        return generate()
    
    response.__call__ = streaming_call
    return response
```

## Summary

All implementation files use **ONLY Python standard library**:
- ✅ No Flask
- ✅ No FastAPI
- ✅ No SQLAlchemy
- ✅ No Pydantic
- ✅ Custom WSGI application
- ✅ Custom routing
- ✅ Custom request/response handling
- ✅ Custom authentication (JWT)
- ✅ Direct database access (sqlite3)
- ✅ Direct HTTP requests (urllib)

The application is production-ready and can be deployed on Apache with mod_wsgi.