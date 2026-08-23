#!/usr/bin/env python3
"""
Exemplos de uso do Human Challenge Solver

O drc|1402 significa que o PerimeterX está pedindo um "human challenge" visual:
- Hold and Release (pressione e segure uma barra)
- Swipe (deslize com o mouse)
- Click em local específico
- Rotate uma imagem

Este script demonstra como usar o solver.
"""

import asyncio
import logging
from human_challenge import (
    HumanChallengeSolver,
    solve_human_challenge,
    solve_human_challenge_sync,
    ChallengeType
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# EXEMPLO 1: Uso síncrono (mais simples)
# ============================================================================

def example_sync():
    """Exemplo síncrono - mais fácil para scripts simples"""
    print("\n" + "="*70)
    print("EXEMPLO 1: Uso Síncrono")
    print("="*70 + "\n")
    
    url = "https://example.com/login"  # Replace com URL real
    
    logger.info(f"Resolvendo human challenge em {url}")
    
    success, token = solve_human_challenge_sync(
        url=url,
        proxy=None,  # Seu proxy se tiver
        headless=True,
        timeout_ms=30000
    )
    
    if success:
        logger.info(f"✅ Challenge resolvido!")
        logger.info(f"Token obtido: {token[:50] if token else 'None'}...")
    else:
        logger.error(f"❌ Falha ao resolver challenge")


# ============================================================================
# EXEMPLO 2: Uso assíncrono com controle total
# ============================================================================

async def example_async():
    """Exemplo assíncrono - para aplicações que precisam de controle fino"""
    print("\n" + "="*70)
    print("EXEMPLO 2: Uso Assíncrono")
    print("="*70 + "\n")
    
    url = "https://example.com/protected"  # Replace com URL real
    proxy = None  # "proxy.example.com:8080" se tiver
    
    solver = HumanChallengeSolver(
        headless=True,
        timeout_ms=30000,
        proxy=proxy,
        slow_motion_ms=500  # Adiciona 500ms delay entre ações (útil para debug)
    )
    
    try:
        logger.info(f"Iniciando navegador...")
        await solver.launch_browser()
        
        logger.info(f"Navegando para {url}")
        success, token = await solver.solve_challenge(url)
        
        if success:
            logger.info(f"✅ Challenge resolvido!")
            logger.info(f"Token: {token[:50] if token else 'None'}...")
        else:
            logger.error(f"❌ Falha ao resolver challenge")
    
    finally:
        logger.info("Fechando navegador...")
        await solver.close()


# ============================================================================
# EXEMPLO 3: Múltiplas requisições com reutilização de contexto
# ============================================================================

async def example_reuse_context():
    """Reutilizar contexto para múltiplas navegações"""
    print("\n" + "="*70)
    print("EXEMPLO 3: Reutilizar Contexto")
    print("="*70 + "\n")
    
    urls = [
        "https://site1.com/login",
        "https://site2.com/protected",
        "https://site3.com/checkout",
    ]
    
    solver = HumanChallengeSolver(
        headless=True,
        timeout_ms=30000,
    )
    
    try:
        await solver.launch_browser()
        
        for url in urls:
            logger.info(f"\nProcessando {url}")
            success, token = await solver.solve_challenge(url)
            
            if success:
                logger.info(f"✅ Resolvido: {url}")
                logger.info(f"Token: {token[:30] if token else 'None'}...")
            else:
                logger.error(f"❌ Falha: {url}")
            
            # Aguardar um pouco entre requisições
            await asyncio.sleep(2)
    
    finally:
        await solver.close()


# ============================================================================
# EXEMPLO 4: Integração com PXSolver
# ============================================================================

def example_with_pxsolver():
    """Usar o human challenge solver dentro do PXSolver"""
    print("\n" + "="*70)
    print("EXEMPLO 4: Integração com PXSolver")
    print("="*70 + "\n")
    
    from solve import PXSolver
    
    # Criar solver com parâmetros reais
    solver = PXSolver(
        app_id="PX0OZADU9K",
        ft=221,
        collector_uri="https://collector-px0ozadu9k.px-cloud.net/api/v2/collector",
        host="https://example.com",
        sid="sid-value",
        vid="vid-value",
        cts="cts-value",
        proxy=None
    )
    
    # Resolver (detecta automaticamente drc|1402 e usa human challenge solver)
    token = solver.solve()
    
    if token:
        logger.info(f"✅ PerimeterX token obtido: {token[:50]}...")
    else:
        if solver.last_error:
            logger.error(f"Erro durante resolver: {solver.last_error}")


# ============================================================================
# EXEMPLO 5: Custom challenge data (debug)
# ============================================================================

async def example_debug_challenge_data():
    """Extrair e analisar dados do challenge"""
    print("\n" + "="*70)
    print("EXEMPLO 5: Debug Challenge Data")
    print("="*70 + "\n")
    
    url = "https://example.com/login"
    
    solver = HumanChallengeSolver(
        headless=True,
        timeout_ms=30000,
    )
    
    try:
        await solver.launch_browser()
        await solver.create_context()
        
        logger.info(f"Navegando para {url}")
        import asyncio
        # Usar timeout para não travar
        try:
            await asyncio.wait_for(
                solver.page.goto(url, wait_until="networkidle"),
                timeout=30
            )
        except:
            logger.warning("Timeout ao navegar, continuando...")
        
        # Extrair dados do challenge
        challenge_data = await solver._extract_challenge_data()
        
        if challenge_data:
            logger.info(f"Challenge data extraído:")
            logger.info(f"  Tipo: {challenge_data.challenge_type.value}")
            logger.info(f"  Duração: {challenge_data.duration_ms}ms")
            logger.info(f"  Posição: ({challenge_data.start_x}, {challenge_data.start_y})")
            logger.info(f"  Target: {challenge_data.target_selector}")
        else:
            logger.warning("Nenhum challenge encontrado na página")
    
    finally:
        await solver.close()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "🚀 " * 20)
    print("PerimeterX Human Challenge Solver - Exemplos")
    print("🚀 " * 20)
    
    # Descomente o exemplo que deseja executar:
    
    # Síncrono (mais simples):
    # example_sync()
    
    # Assíncrono:
    # asyncio.run(example_async())
    
    # Reutilizar contexto:
    # asyncio.run(example_reuse_context())
    
    # Com PXSolver:
    # example_with_pxsolver()
    
    # Debug challenge data:
    # asyncio.run(example_debug_challenge_data())
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║  ❓ COMO USAR:                                                             ║
║                                                                            ║
║  1. Instalar Playwright:                                                  ║
║     bash install-playwright.sh                                            ║
║                                                                            ║
║  2. Usar no seu código:                                                   ║
║     from human_challenge import solve_human_challenge_sync                ║
║                                                                            ║
║     success, token = solve_human_challenge_sync(                          ║
║         url="https://site.com",                                           ║
║         proxy=None,                                                       ║
║         headless=True                                                     ║
║     )                                                                      ║
║                                                                            ║
║  3. No PXSolver, drc|1402 é detectado automaticamente!                   ║
║                                                                            ║
║  📝 Exemplos de desafios resolvidos:                                       ║
║     • Hold and Release (pressione e segure)                               ║
║     • Swipe (deslize com mouse)                                           ║
║     • Click em local específico                                           ║
║     • Rotate (não implementado ainda)                                     ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
