#!/usr/bin/env python3
"""
Verify which models are installed on Ollama servers
"""

import requests
import json
from typing import Dict, List

def check_server_models(host: str, port: int = 11434) -> List[str]:
    """Check which models are available on a server"""
    try:
        url = f"http://{host}:{port}/api/tags"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        return []
    except Exception as e:
        print(f"❌ Error connecting to {host}: {e}")
        return []

def main():
    servers = {
        "ollama01": "ollama01.thiscluster.net",
        "ollama02": "ollama02.thiscluster.net"
    }
    
    # Models we need
    required_models = {
        "qwen2.5-coder:32b": "Primary coding/debugging model (BEST)",
        "qwen2.5:14b": "Planning and QA model",
        "functiongemma": "Routing and tool formatting",
        "qwen2.5-coder:7b": "Quick fixes"
    }
    
    print("=" * 70)
    print("MODEL VERIFICATION REPORT")
    print("=" * 70)
    
    for server_name, host in servers.items():
        print(f"\n📡 Checking {server_name} ({host})...")
        models = check_server_models(host)
        
        if not models:
            print(f"   ⚠️  Could not connect or no models found")
            continue
            
        print(f"   ✅ Found {len(models)} models")
        
        # Check required models
        print(f"\n   Required Models Status:")
        for model, description in required_models.items():
            # Check for exact match or version variants
            found = any(m.startswith(model.split(':')[0]) for m in models)
            status = "✅" if found else "❌"
            print(f"   {status} {model:25s} - {description}")
            if found:
                matching = [m for m in models if m.startswith(model.split(':')[0])]
                if len(matching) > 1 or matching[0] != model:
                    print(f"      Available: {', '.join(matching)}")
        
        # Show all models
        print(f"\n   All Available Models ({len(models)}):")
        for model in sorted(models):
            print(f"      • {model}")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS:")
    print("=" * 70)
    print("\nIf any required models are missing, install them with:")
    print("  ollama pull <model_name>")
    print("\nFor best performance, ensure qwen2.5-coder:32b is on ollama02")
    print("(It's the best open-source coding model, competitive with GPT-4o)")
    print()

if __name__ == "__main__":
    main()