#!/usr/bin/env python3
"""
Test script para verificar proxy detection e network egress
"""

import sys
import logging
from proxy_manager import ProxyManager, test_network_egress

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

print(f"\n{COLORS['BOLD']}{COLORS['CYAN']}")
print("╔" + "="*68 + "╗")
print("║" + " "*68 + "║")
print("║" + "  Proxy Manager & Network Egress Test".ljust(68) + "║")
print("║" + " "*68 + "║")
print("╚" + "="*68 + "╝")
print(f"{COLORS['RESET']}\n")

# ============================================================================
# TESTE 1: Detectar Proxies
# ============================================================================

print_section("TESTE 1: Detectar Proxies Disponíveis")

manager = ProxyManager()

print_info(f"Manager Status: {manager}")
print_info(f"Detected Proxy: {manager.detected_proxy or 'None'}")
print_info(f"Proxy Source: {manager.proxy_source}")

if manager.detected_proxy:
    print_success(f"Proxy detectado: {manager.detected_proxy}")
else:
    print_warning("Nenhum proxy detectado - usando conexão direta")

# ============================================================================
# TESTE 2: Testar Proxy
# ============================================================================

print_section("TESTE 2: Testar Conectividade do Proxy")

if manager.detected_proxy:
    print_info("Testando conexão via proxy...")
    success, info = manager.test_proxy()
    
    if success:
        print_success(f"Proxy funcionando!")
        print_info(f"IP detectado via proxy: {info}")
    else:
        print_error(f"Proxy não está funcionando")
        print_warning("Tentando conexão direta...")
else:
    print_warning("Nenhum proxy para testar")

# ============================================================================
# TESTE 3: Testar Network Egress
# ============================================================================

print_section("TESTE 3: Testar Network Egress para PerimeterX")

print_info("Testando acesso a collector-pxiao7f0.px-cloud.net...")

success, error = test_network_egress()

if success:
    print_success("✅ Network egress OK - Pode acessar PerimeterX collectors!")
    print_info("Próximo passo: Executar test_nordstrom_real.py")
else:
    print_error(f"Network egress bloqueado: {error}")
    
    print_warning("\nPossíveis soluções:")
    print("  1. Configurar proxy no Coolify")
    print("  2. Usar variável de ambiente HTTP_PROXY")
    print("  3. Liberar firewall para *.px-cloud.net")

# ============================================================================
# TESTE 4: Testar com PXSolver
# ============================================================================

print_section("TESTE 4: Verificar Integração com PXSolver")

try:
    from solve import PXSolver, PROXY_MANAGER_AVAILABLE
    
    if PROXY_MANAGER_AVAILABLE:
        print_success("Proxy manager integrado com PXSolver ✅")
        print_info("Auto-detection está ativo por padrão")
        print_info("Basta usar: PXSolver(...) sem especificar proxy")
    else:
        print_warning("Proxy manager não está disponível")

except ImportError as e:
    print_error(f"Não consegue importar PXSolver: {e}")

# ============================================================================
# RESUMO
# ============================================================================

print_section("RESUMO")

print_info("Proxy Detection Summary:")
print(f"  • Status: {manager.detected_proxy and '✅ Configurado' or '⚠️ Não configurado'}")
print(f"  • Proxy: {manager.detected_proxy or 'None (conexão direta)'}")
print(f"  • Source: {manager.proxy_source}")

print_info("\nNetwork Egress Summary:")
success, error = test_network_egress()
print(f"  • Status: {success and '✅ OK' or '❌ Bloqueado'}")
if not success:
    print(f"  • Erro: {error}")

print_info("\nNext Steps:")
if success:
    print("  1. ✅ Proxy e network OK")
    print("  2. Execute: python test_nordstrom_real.py")
    print("  3. Deve obter _px3 token")
else:
    print("  1. ❌ Network egress está bloqueado")
    print("  2. Configure proxy OU libere firewall")
    print("  3. Re-execute este teste")

print(f"\n{COLORS['BOLD']}{COLORS['GREEN']}Teste concluído!{COLORS['RESET']}\n")
