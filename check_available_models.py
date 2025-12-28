#!/usr/bin/env python3
"""
Check which models are actually available on Ollama servers
"""

import requests
import json

servers = [
    {"name": "ollama01", "host": "ollama01.thiscluster.net", "port": 11434},
    {"name": "ollama02", "host": "ollama02.thiscluster.net", "port": 11434}
]

print("=" * 80)
print("CHECKING AVAILABLE MODELS ON OLLAMA SERVERS")
print("=" * 80)

for server in servers:
    print(f"\n📡 {server['name']} ({server['host']}:{server['port']})")
    print("-" * 80)
    
    try:
        url = f"http://{server['host']}:{server['port']}/api/tags"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            
            print(f"✅ Online - {len(models)} models available:")
            
            # Group models by base name
            model_groups = {}
            for model in models:
                name = model["name"]
                base_name = name.split(":")[0]
                if base_name not in model_groups:
                    model_groups[base_name] = []
                model_groups[base_name].append(name)
            
            # Print grouped
            for base_name in sorted(model_groups.keys()):
                variants = model_groups[base_name]
                print(f"  • {base_name}:")
                for variant in sorted(variants):
                    print(f"    - {variant}")
            
            # Check for qwen2.5-coder specifically
            qwen_coder_models = [m["name"] for m in models if "qwen2.5-coder" in m["name"].lower()]
            if qwen_coder_models:
                print(f"\n  🎯 qwen2.5-coder variants found:")
                for model in qwen_coder_models:
                    print(f"    ✓ {model}")
            else:
                print(f"\n  ❌ No qwen2.5-coder models found on this server")
                
        else:
            print(f"❌ HTTP {response.status_code}")
            
    except requests.Timeout:
        print(f"❌ Connection timeout")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)