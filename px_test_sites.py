#!/usr/bin/env python3
"""
PX Test Sites - Sites conhecidos que usam PerimeterX para testar o solver
Use com sua API: POST http://seu-coolify/api/solve
"""

# Sites que usam PerimeterX (HUMAN Security) em 2026
PX_TEST_SITES = {
    "zillow": {
        "name": "Zillow (Imóveis EUA)",
        "url": "https://www.zillow.com",
        "description": "Site de imóveis dos EUA, usa PX pesado",
        "difficulty": "HARD"
    },
    "crunchbase": {
        "name": "Crunchbase (Startups)",
        "url": "https://www.crunchbase.com",
        "description": "Base de dados de empresas/startups",
        "difficulty": "MEDIUM"
    },
    "stockx": {
        "name": "StockX (Sneakers/Streetwear)",
        "url": "https://stockx.com",
        "description": "Marketplace de tênis e streetwear",
        "difficulty": "HARD"
    },
    "fiverr": {
        "name": "Fiverr (Freelancers)",
        "url": "https://www.fiverr.com",
        "description": "Plataforma de freelancers",
        "difficulty": "MEDIUM"
    },
    "booking": {
        "name": "Booking.com (Hotéis)",
        "url": "https://www.booking.com",
        "description": "Reserva de hotéis",
        "difficulty": "HARD"
    },
    "airtable": {
        "name": "Airtable (Original do solver)",
        "url": "https://airtable.com/login",
        "description": "Planilhas online - site original do solver",
        "difficulty": "MEDIUM",
        "app_id": "PX0OZADU9K",
        "note": "App ID pode estar desatualizado"
    }
}

COMO_TESTAR = """
╔════════════════════════════════════════════════════════════════════════╗
║            COMO TESTAR SEU PX SOLVER                                 ║
╚════════════════════════════════════════════════════════════════════════╝

PASSO 1: Escolha um site da lista acima

PASSO 2: Abra o site no Chrome e F12 > Network tab

PASSO 3: Procure por requisições para "collector" ou "px-cloud"

PASSO 4: Extraia: app_id, collector_uri, sid, vid, cts

PASSO 5: Chame sua API:

curl -X POST "http://SEU-COOLIFY/api/solve" \\
  -H "Content-Type: application/json" \\
  -d '{
    "app_id": "PX_APP_ID_DO_SITE",
    "ft": 221,
    "collector_uri": "https://collector-XXXX.px-cloud.net/api/v2/collector",
    "host": "https://URL_DO_SITE",
    "sid": "SID_EXTRAIDO",
    "vid": "VID_EXTRAIDO",
    "cts": "CTS_EXTRAIDO"
  }'

PASSO 6: Se retornar token = SOLVER FUNCIONA! ✅
"""

if __name__ == "__main__":
    print("\n🔒 SITES COM PERIMETER X PARA TESTAR SEU SOLVER\n")
    for key, site in PX_TEST_SITES.items():
        diff = site["difficulty"]
        emoji = {"EASY": "🟢", "MEDIUM": "🟡", "HARD": "🔴"}[diff]
        print(f"  {emoji} {site['name']}")
        print(f"     URL: {site['url']}")
        print(f"     Dificuldade: {diff}")
        print()
    print(COMO_TESTAR)
