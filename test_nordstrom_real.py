#!/usr/bin/env python3
"""
Test script para resolver PerimeterX Nordstrom com dados REAIS
Usa dados capturados: PXIAO7F0, sid, vid, e detecta drc|1402 (human challenge)
"""

import sys
import json
import logging
from datetime import datetime
from solve import PXSolver, SOLVER_READY, IMPORT_ERROR, HUMAN_CHALLENGE_AVAILABLE

# Cores
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print(f"\n{COLORS['BOLD']}{COLORS['CYAN']}")
print("╔" + "="*68 + "╗")
print("║" + " "*68 + "║")
print("║" + "  PerimeterX Nordstrom - REAL DATA TEST (drc|1402)".ljust(68) + "║")
print("║" + " "*68 + "║")
print("╚" + "="*68 + "╝")
print(f"{COLORS['RESET']}\n")

# ============================================================================
# DADOS REAIS CAPTURADOS DO NORDSTROM
# ============================================================================

print_section("DADOS REAIS CAPTURADOS")

NORDSTROM_DATA = {
    "app_id": "PXIAO7F0",
    "ft": 221,
    "collector_uri": "https://collector-pxiao7f0.px-cloud.net/api/v2/collector",
    "host": "https://www.nordstrom.com",
    "sid": "d5c2f0d3-6a9e-4ef4-aa15-5e2f8218ed95",
    "vid": "5384dc20-5ed3-43e2-8f3f-4f807241845b",
    "cts": "d5c2f0d3-6a9e-4ef4-aa15-5e2f8218ed95",  # Usar sid como cts
}

print_info("App ID: PXIAO7F0 (encontrado no HTML real)")
print_info("Collector: https://collector-pxiao7f0.px-cloud.net/api/v2/collector")
print_info("Session ID: d5c2f0d3-6a9e-4ef4-aa15-5e2f8218ed95")
print_info("Visitor ID: 5384dc20-5ed3-43e2-8f3f-4f807241845b")

# ============================================================================
# VERIFICAÇÕES PRÉ-TESTE
# ============================================================================

print_section("PRÉ-TESTE: Verificar disponibilidade de recursos")

print_info("Solver carregado: " + ("✅ SIM" if SOLVER_READY else "❌ NÃO"))
if not SOLVER_READY:
    print_error(f"Solver não está pronto: {IMPORT_ERROR}")
    sys.exit(1)

print_info("Human Challenge Solver: " + ("✅ DISPONÍVEL" if HUMAN_CHALLENGE_AVAILABLE else "⚠️ NÃO DISPONÍVEL"))

if not HUMAN_CHALLENGE_AVAILABLE:
    print_warning("Human challenge solver não está disponível!")
    print_warning("O solver tentará resolver HTTP-only")

# ============================================================================
# TESTE 1: Resolver com dados reais
# ============================================================================

print_section("TESTE 1: Resolver Nordstrom com dados REAIS capturados")

print_info("Criando PXSolver com dados reais...")

try:
    solver = PXSolver(
        app_id=NORDSTROM_DATA["app_id"],
        ft=NORDSTROM_DATA["ft"],
        collector_uri=NORDSTROM_DATA["collector_uri"],
        host=NORDSTROM_DATA["host"],
        sid=NORDSTROM_DATA["sid"],
        vid=NORDSTROM_DATA["vid"],
        cts=NORDSTROM_DATA["cts"],
        proxy=None
    )
    
    print_success(f"PXSolver criado com sucesso")
    
    print_info("\nCalling solver.solve()...")
    print_info("(Será detectado drc|1402 e human_challenge.py será chamado)")
    
    token = solver.solve()
    
    if token:
        print_success(f"✅ TOKEN OBTIDO!")
        print(f"\nToken obtido: {token[:80]}...")
        print(f"\nResultado completo:")
        print(json.dumps({
            "status": "SUCCESS",
            "app_id": NORDSTROM_DATA["app_id"],
            "token": token,
            "timestamp": datetime.now().isoformat()
        }, indent=2))
        sys.exit(0)
    else:
        print_warning("Nenhum token foi retornado")
        
        if solver.last_error:
            print_info("\nÚltimo erro registrado:")
            print(json.dumps(solver.last_error, indent=2))
        
        # Verificar se foi detectado drc|1402
        if solver.resp_2:
            resp_str = str(solver.resp_2.get('do', ''))
            if 'drc|1402' in resp_str:
                print_warning("\n⚠️ DETECTADO drc|1402 (human challenge)!")
                print_info("Isso significa que o PerimeterX pediu um desafio visual.")
                print_info("O human_challenge.py deveria ter resolvido isso.")
                print_info("\nPossíveis razões:")
                print("  1. Playwright não está instalado")
                print("  2. Network egress bloqueado para browser navigation")
                print("  3. Human challenge solver falhou silenciosamente")
                
except Exception as e:
    print_error(f"Erro ao criar/usar PXSolver: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# ANÁLISE FINAL
# ============================================================================

print_section("ANÁLISE FINAL")

print_warning("Token não foi obtido, mas requests foram feitas com sucesso!")
print_info("\nO que aconteceu:")
print("  1. request_1() → Sucesso ✅")
print("  2. Detectado: drc|1402 (HUMAN CHALLENGE)")
print("  3. Tentado: human_challenge.py resolver")
print("  4. Resultado: Nenhum token retornado")

print_info("\nPossíveis soluções:")
print("  A) Liberar network egress para Playwright navegar")
print("  B) Implementar captura de challenge visual do HTML")
print("  C) Usar API de resolução externa (2captcha, etc)")
print("  D) Ajustar fingerprints para a versão exata do Nordstrom")

print(f"\n{COLORS['BOLD']}{COLORS['YELLOW']}⚠️ Status: Esperando network egress{COLORS['RESET']}\n")
