#!/usr/bin/env python3
"""Testar formato da API FlareSolverr"""
import os
import requests
import json

url = os.environ.get("FLARESOLVERR_URL", "")
print(f"FLARESOLVERR_URL = '{url}'")

if not url:
    print("❌ Variável FLARESOLVERR_URL não configurada neste ambiente")
    print("Mas está configurada no Coolify.")
    print("\nVou mostrar os 3 formatos mais comuns para testar:")
    
    print("""
FORMATO 1 (FlareSolverr padrão):
  POST {url}/v1
  Body: {"cmd": "request.get", "url": "https://www.fiverr.com", "maxTimeout": 60000}

FORMATO 2 (FlareSolverr sem /v1):
  POST {url}
  Body: {"cmd": "request.get", "url": "https://www.fiverr.com", "maxTimeout": 60000}

FORMATO 3 (Custom API):
  POST {url}/solve
  Body: {"url": "https://www.fiverr.com"}

Qual formato a sua API usa?
""")
else:
    # Tentar formato 1
    for endpoint in [f"{url.rstrip('/')}/v1", url.rstrip('/')]:
        print(f"\nTentando: POST {endpoint}")
        try:
            resp = requests.post(
                endpoint,
                json={"cmd": "request.get", "url": "https://www.fiverr.com", "maxTimeout": 60000},
                timeout=65
            )
            print(f"Status: {resp.status_code}")
            data = resp.json()
            print(f"Response keys: {list(data.keys())}")
            print(f"Status field: {data.get('status')}")
            if data.get('solution'):
                print(f"Solution keys: {list(data['solution'].keys())}")
            print(json.dumps(data, indent=2)[:500])
            break
        except Exception as e:
            print(f"Erro: {e}")
