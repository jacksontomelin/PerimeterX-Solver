#!/usr/bin/env python3
"""
Test script para resolver PerimeterX desafios do Nordstrom
Simula o que o /api/test-px?site=nordstrom faria
"""

import sys
import json
import logging
from datetime import datetime
from solve import PXSolver, SOLVER_READY, IMPORT_ERROR

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
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print(f"\n{COLORS['BOLD']}{COLORS['CYAN']}")
print("╔" + "="*68 + "╗")
print("║" + " "*68 + "║")
print("║" + "  PerimeterX Nordstrom Solver - Test".ljust(68) + "║")
print("║" + " "*68 + "║")
print("╚" + "="*68 + "╝")
print(f"{COLORS['RESET']}\n")

# Verificar se solver está pronto
print_section("TESTE 0: Verificar solver")

if not SOLVER_READY:
    print_error(f"Solver não está pronto: {IMPORT_ERROR}")
    sys.exit(1)

print_success("Todos os módulos do solver carregados")

# ============================================================================
# TESTE 1: Tentar resolver com IDs conhecidos
# ============================================================================

print_section("TESTE 1: Resolver Nordstrom com IDs conhecidos")

KNOWN_PX_IDS = {
    "nordstrom": ["PXRQG2AQ", "PX49ZQ8Z", "PXASN0T4", "PXAMQADJ8"],
}

# Dados gerais do site
host = "https://www.nordstrom.com"
site_name = "nordstrom"

# Tentar cada ID conhecido
for idx, known_id in enumerate(KNOWN_PX_IDS["nordstrom"], 1):
    print_section(f"TESTE 1.{idx}: Tentando com ID {known_id}")
    
    collector_uri = f"https://collector-{known_id.lower()}.px-cloud.net/api/v2/collector"
    
    print_info(f"Criando PXSolver com:")
    print(f"  • app_id: {known_id}")
    print(f"  • ft: 221")
    print(f"  • collector_uri: {collector_uri}")
    print(f"  • host: {host}")
    print(f"  • sid/vid/cts: [teste-valores]")
    
    try:
        solver = PXSolver(
            app_id=known_id,
            ft=221,
            collector_uri=collector_uri,
            host=host,
            sid=f"test-sid-{known_id}",
            vid=f"test-vid-{known_id}",
            cts=f"test-cts-{known_id}",
            proxy=None
        )
        
        print_info("Chamando solver.solve()...")
        token = solver.solve()
        
        if token:
            print_success(f"✅ TOKEN OBTIDO com {known_id}!")
            print(f"\nToken: {token[:50]}...")
            print(f"\nResultado completo:")
            print(json.dumps({
                "status": "SUCCESS",
                "app_id": known_id,
                "token": token,
                "timestamp": datetime.now().isoformat()
            }, indent=2))
            sys.exit(0)
        else:
            if solver.last_error:
                print_warning(f"Falha com {known_id}:")
                print(json.dumps(solver.last_error, indent=2))
            else:
                print_warning(f"Nenhum token obtido com {known_id}")
    
    except Exception as e:
        print_error(f"Erro ao tentar {known_id}: {e}")
        import traceback
        traceback.print_exc()

# ============================================================================
# Fim: Resumo
# ============================================================================

print_section("RESUMO")

print_warning("Nenhum dos IDs conhecidos funcionou")
print_info("Possíveis razões:")
print("  1. Nordstrom pode estar usando um novo ID de PerimeterX")
print("  2. A API do collector pode estar rejeitando valores de teste")
print("  3. Os valores sid/vid/cts de teste podem ser inválidos")
print("  4. Pode ser necessário drc|1402 (human challenge) para resolver")

print(f"\n{COLORS['BOLD']}{COLORS['YELLOW']}⚠️  Para debug mais profundo, adicione logging ao solver{COLORS['RESET']}\n")
