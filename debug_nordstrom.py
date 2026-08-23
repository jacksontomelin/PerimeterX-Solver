#!/usr/bin/env python3
"""
Debug script para testar /api/test-px?site=nordstrom
Simula o que acontece no Coolify sem precisar acessar a URL
"""

import requests as req
import re
import json
from datetime import datetime
import sys

# Cores para output
COLORS = {
    'GREEN': '\033[92m',
    'RED': '\033[91m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'CYAN': '\033[96m',
    'RESET': '\033[0m',
    'BOLD': '\033[1m',
}

def print_section(title):
    print(f"\n{COLORS['BOLD']}{COLORS['BLUE']}{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}{COLORS['RESET']}\n")

def print_success(text):
    print(f"{COLORS['GREEN']}✅ {text}{COLORS['RESET']}")

def print_error(text):
    print(f"{COLORS['RED']}❌ {text}{COLORS['RESET']}")

def print_info(text):
    print(f"{COLORS['CYAN']}ℹ️  {text}{COLORS['RESET']}")

def print_warning(text):
    print(f"{COLORS['YELLOW']}⚠️  {text}{COLORS['RESET']}")

# IDs conhecidos do PerimeterX para Nordstrom
KNOWN_PX_IDS = {
    "nordstrom": ["PXRQG2AQ", "PX49ZQ8Z", "PXASN0T4", "PXAMQADJ8"],
}

print(f"\n{COLORS['BOLD']}{COLORS['CYAN']}")
print("╔" + "="*68 + "╗")
print("║" + " "*68 + "║")
print("║" + "  PerimeterX Nordstrom - Debug Script".ljust(68) + "║")
print("║" + " "*68 + "║")
print("╚" + "="*68 + "╝")
print(f"{COLORS['RESET']}\n")

# Teste 1: Detectar PerimeterX no Nordstrom
print_section("TESTE 1: Detectar PerimeterX no Nordstrom")

url = "https://www.nordstrom.com"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

print_info(f"Acessando {url}...")

try:
    resp = req.get(url, headers=headers, timeout=15, allow_redirects=True)
    print_success(f"Status: {resp.status_code}")
    print_info(f"Final URL: {resp.url}")
    
    html = resp.text
    resp_headers = dict(resp.headers)
    
    # Verificar cookies
    print_section("TESTE 1.1: Procurar cookies do PerimeterX")
    set_cookie = resp_headers.get("Set-Cookie", "") + resp_headers.get("set-cookie", "")
    px_cookies = []
    for cookie_name in ["_pxhd", "_pxvid", "_px3", "_px2", "_pxde", "_pxff"]:
        if cookie_name in set_cookie:
            px_cookies.append(cookie_name)
            print_success(f"Cookie encontrado: {cookie_name}")
    
    if not px_cookies:
        print_warning("Nenhum cookie PerimeterX encontrado nos headers")
    
    # Verificar scripts
    print_section("TESTE 1.2: Procurar scripts do PerimeterX")
    px_scripts = re.findall(r'(?:src|href)\s*=\s*["\']([^"\']*px-cloud[^"\']*)["\']', html, re.I)
    px_scripts += re.findall(r'(?:src|href)\s*=\s*["\']([^"\']*px-cdn[^"\']*)["\']', html, re.I)
    
    if px_scripts:
        print_success(f"Scripts encontrados ({len(px_scripts)}):")
        for script in px_scripts[:3]:  # Mostrar até 3
            print(f"  • {script[:80]}...")
    else:
        print_warning("Nenhum script PerimeterX encontrado")
    
    # Extrair app_id
    print_section("TESTE 1.3: Extrair App ID")
    app_id = None
    
    # Tentar padrões
    for pat in [
        r'"appId"\s*:\s*"(PX[^"]+)"',
        r"'appId'\s*:\s*'(PX[^']+)'",
        r'_pxAppId\s*=\s*["\']([^"\']+)',
        r'appId:\s*["\']?(PX[0-9A-Za-z]+)',
        r'client\.px-cloud\.net/(PX[^/]+)/',
    ]:
        m = re.search(pat, html)
        if m:
            app_id = m.group(1)
            print_success(f"App ID encontrado: {app_id}")
            break
    
    if not app_id:
        # Procurar qualquer ID PX
        all_px_ids = list(set(re.findall(r'PX[0-9A-Z]{6,12}', html)))
        if all_px_ids:
            print_info(f"IDs PX encontrados no HTML: {all_px_ids}")
            app_id = all_px_ids[0]
            print_success(f"Usando primeiro ID: {app_id}")
        else:
            print_warning("Nenhum ID PerimeterX encontrado no HTML")
    
    # Procurar referências gerais
    print_section("TESTE 1.4: Procurar referências de PerimeterX")
    px_refs = []
    patterns = {
        "px-cloud.net": r'px-cloud\.net',
        "px-cdn.net": r'px-cdn\.net',
        "_pxAppId": r'_pxAppId',
        "human-challenge": r'human-challenge',
        "px_cookie": r'_px[23hv]',
        "pxConfig": r'_?px[Cc]onfig',
        "px-captcha": r'px-captcha',
    }
    
    for name, pat in patterns.items():
        if re.search(pat, html):
            px_refs.append(name)
            print_success(f"Referência encontrada: {name}")
    
    if not px_refs:
        print_warning("Nenhuma referência de PerimeterX encontrada")
    
except Exception as e:
    print_error(f"Erro ao acessar Nordstrom: {e}")
    sys.exit(1)

# Teste 2: Usar IDs conhecidos
print_section("TESTE 2: Usar IDs conhecidos de PerimeterX")

if not app_id:
    print_info("App ID não foi detectado, usando IDs conhecidos...")
    app_id = KNOWN_PX_IDS["nordstrom"][0]
    print_success(f"Usando ID conhecido: {app_id}")
else:
    print_success(f"App ID detectado: {app_id}")

# Teste 3: Construir collector URI
print_section("TESTE 3: Construir Collector URI")

collector_uri = f"https://collector-{app_id.lower()}.px-cloud.net/api/v2/collector"
print_success(f"Collector URI: {collector_uri}")

# Teste 4: Resumo
print_section("RESUMO DO DEBUG")

print(json.dumps({
    "site": "nordstrom",
    "url": url,
    "status": "OK",
    "app_id": app_id,
    "collector_uri": collector_uri,
    "px_detected": bool(px_cookies or px_scripts or px_refs or app_id),
    "px_cookies_found": px_cookies,
    "px_scripts_found": len(px_scripts),
    "px_references": px_refs,
    "http_status": resp.status_code,
    "timestamp": datetime.now().isoformat()
}, indent=2))

print_section("PRÓXIMAS ETAPAS")
print_info("Para resolver o desafio PerimeterX, você precisa de:")
print("  1. Session ID (sid)")
print("  2. Visitor ID (vid)")
print("  3. Client Timestamp (cts)")
print("")
print_warning("Esses valores mudam a cada requisição - precisam ser capturados ao acessar o site")

print(f"\n{COLORS['BOLD']}{COLORS['GREEN']}✅ Debug completo!{COLORS['RESET']}\n")
