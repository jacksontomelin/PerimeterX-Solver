"""
Human Challenge Solver para PerimeterX using Playwright
Resolve visual challenges (hold and release) quando drc|1402 é retornado

O drc|1402 significa que o servidor quer um human challenge:
- "Pressione e segure" por X segundos
- Swipe/drag gesture
- Click em local específico
- Outros gestos visuais

Este módulo usa Playwright para automatizar o navegador real resolvendo o challenge.
"""

import asyncio
import logging
import time
import json
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Tentar importar Playwright - se não estiver instalado, graceful fallback
try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Human challenges will fail.")


class ChallengeType(Enum):
    """Tipos de human challenges do PerimeterX"""
    HOLD_AND_RELEASE = "hold_and_release"  # Pressionar e segurer barra
    SWIPE = "swipe"  # Deslizar gesture
    CLICK = "click"  # Clique em local específico
    ROTATE = "rotate"  # Rotação de imagem
    UNKNOWN = "unknown"


@dataclass
class ChallengeData:
    """Dados do challenge visual extraído do PerimeterX"""
    challenge_type: ChallengeType
    duration_ms: int = 3000  # Duração do hold em ms
    target_selector: Optional[str] = None
    start_x: int = 0
    start_y: int = 0
    end_x: int = 0
    end_y: int = 0
    html_content: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.challenge_type.value,
            "duration_ms": self.duration_ms,
            "target_selector": self.target_selector,
            "start": (self.start_x, self.start_y),
            "end": (self.end_x, self.end_y),
        }


class HumanChallengeSolver:
    """Resolver para human challenges visuais do PerimeterX v6.7.9+"""
    
    def __init__(
        self,
        headless: bool = True,
        timeout_ms: int = 30000,
        proxy: Optional[str] = None,
        slow_motion_ms: int = 0,
    ):
        """
        Args:
            headless: Rodar navegador em headless mode
            timeout_ms: Timeout para resolver challenge (ms)
            proxy: Proxy URL (ex: "http://proxy:port")
            slow_motion_ms: Adicionar delay entre ações (útil para debug)
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright not installed. "
                "Install with: pip install playwright && playwright install chromium"
            )
        
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.proxy = proxy
        self.slow_motion_ms = slow_motion_ms
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def launch_browser(self) -> None:
        """Iniciar navegador Chromium"""
        playwright = await async_playwright().start()
        
        launch_args = {
            "headless": self.headless,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                # Chrome 127 - mesmo que PXSolver usa
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            ]
        }
        
        if self.proxy:
            launch_args["proxy"] = {"server": self.proxy}
        
        self.browser = await playwright.chromium.launch(**launch_args)
        logger.info("Browser launched successfully")
    
    async def create_context(self) -> None:
        """Criar novo context com cookies/headers"""
        if not self.browser:
            await self.launch_browser()
        
        context_args = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
            "extra_http_headers": {
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
            }
        }
        
        self.context = await self.browser.new_context(**context_args)
        self.page = await self.context.new_page()
        logger.info("Context created successfully")
    
    async def close(self) -> None:
        """Fechar browser e context"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        logger.info("Browser closed")
    
    async def solve_challenge(
        self,
        url: str,
        challenge_html: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Navegar até URL e resolver human challenge
        """
        try:
            if not self.page:
                await self.create_context()
            
            logger.info(f"Navigating to {url}")
            
            # Interceptar responses para capturar _px3 token direto
            px3_token_from_response = []
            
            async def handle_response(response):
                try:
                    resp_url = response.url
                    if "px-cloud" in resp_url or "px-cdn" in resp_url or "captcha" in resp_url:
                        logger.info(f"PX response intercepted: {resp_url} [{response.status}]")
                    # Capturar _px3 de Set-Cookie headers
                    headers = response.headers
                    set_cookie = headers.get("set-cookie", "")
                    if "_px3=" in set_cookie:
                        import re
                        m = re.search(r'_px3=([^;]+)', set_cookie)
                        if m:
                            px3_token_from_response.append(m.group(1))
                            logger.info(f"Captured _px3 from response header!")
                except:
                    pass
            
            self.page.on("response", handle_response)
            
            # Navegar
            await self.page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            
            # Esperar um pouco para scripts PX carregarem
            await asyncio.sleep(3)
            
            # Checar se já temos token via interceptação
            if px3_token_from_response:
                return True, px3_token_from_response[0]
            
            # Tentar encontrar e resolver o challenge no DOM
            challenge_data = await self._extract_challenge_data()
            
            if challenge_data:
                logger.info(f"Challenge detected: {challenge_data.challenge_type.value}")
                success = await self._solve_by_type(challenge_data)
                
                if success:
                    # Esperar response do servidor
                    await asyncio.sleep(3)
                    
                    # Checar token interceptado
                    if px3_token_from_response:
                        return True, px3_token_from_response[0]
            else:
                logger.info("No specific challenge element found, trying press-and-hold on page center")
                
                # Fallback: tentar press-and-hold no centro da página (common PX pattern)
                viewport = self.page.viewport_size
                cx = viewport["width"] // 2
                cy = viewport["height"] // 2
                
                # Procurar botão/div clicável de challenge
                hold_btn = await self.page.query_selector(
                    'button, [role="button"], .challenge, #px-captcha, '
                    '#px-challenge, [class*="challenge"], [class*="captcha"], '
                    '[class*="human"], [data-testid*="challenge"]'
                )
                
                if hold_btn:
                    box = await hold_btn.bounding_box()
                    if box:
                        cx = int(box["x"] + box["width"] / 2)
                        cy = int(box["y"] + box["height"] / 2)
                        logger.info(f"Found challenge button at ({cx}, {cy})")
                
                # Executar press-and-hold
                logger.info(f"Performing press-and-hold at ({cx}, {cy}) for 3s")
                await self.page.mouse.move(cx, cy)
                await self.page.mouse.down()
                await asyncio.sleep(3.5)
                await self.page.mouse.up()
                
                await asyncio.sleep(3)
                
                if px3_token_from_response:
                    return True, px3_token_from_response[0]
            
            # Última tentativa: extrair _px3 dos cookies
            token = await self._extract_px3_token()
            if token:
                return True, token
            
            # Dump do HTML para debug (logar o que tem na página)
            page_title = await self.page.title()
            page_url = self.page.url
            body_text = await self.page.evaluate("() => document.body ? document.body.innerText.substring(0, 500) : 'no body'")
            logger.warning(f"Challenge page debug: title='{page_title}', url='{page_url}', body='{body_text[:200]}'")
            
            return False, None
        
        except Exception as e:
            logger.error(f"Error solving challenge: {e}", exc_info=True)
            return False, None
    
    async def _extract_challenge_data(self) -> Optional[ChallengeData]:
        """Extrair dados do challenge visual do DOM - seletores reais do PerimeterX"""
        try:
            challenge_data = await self.page.evaluate("""
            () => {
                // === Seletores REAIS do PerimeterX ===
                
                // 1. px-captcha (widget oficial do PX)
                let el = document.querySelector('#px-captcha');
                if (el) {
                    const rect = el.getBoundingClientRect();
                    return {
                        type: 'hold_and_release',
                        duration_ms: 3500,
                        target_selector: '#px-captcha',
                        start_x: Math.floor(rect.left + rect.width / 2),
                        start_y: Math.floor(rect.top + rect.height / 2),
                        end_x: Math.floor(rect.left + rect.width / 2),
                        end_y: Math.floor(rect.top + rect.height / 2),
                        html: el.outerHTML.substring(0, 300),
                        source: 'px-captcha'
                    };
                }
                
                // 2. Iframe do PerimeterX challenge
                let iframe = document.querySelector('iframe[src*="captcha"]') ||
                             document.querySelector('iframe[src*="challenge"]') ||
                             document.querySelector('iframe[src*="perimeterx"]') ||
                             document.querySelector('iframe[src*="px-cloud"]') ||
                             document.querySelector('iframe[src*="px-cdn"]');
                if (iframe) {
                    const rect = iframe.getBoundingClientRect();
                    return {
                        type: 'hold_and_release',
                        duration_ms: 3500,
                        target_selector: 'iframe',
                        start_x: Math.floor(rect.left + rect.width / 2),
                        start_y: Math.floor(rect.top + rect.height / 2),
                        end_x: Math.floor(rect.left + rect.width / 2),
                        end_y: Math.floor(rect.top + rect.height / 2),
                        html: iframe.outerHTML.substring(0, 300),
                        source: 'px-iframe'
                    };
                }
                
                // 3. Divs com "press and hold" text
                const allElements = document.querySelectorAll('div, span, p, button');
                for (const elem of allElements) {
                    const text = (elem.innerText || '').toLowerCase();
                    if (text.includes('press') || text.includes('hold') || 
                        text.includes('human') || text.includes('verify') ||
                        text.includes('challenge') || text.includes('segure') ||
                        text.includes('pressione')) {
                        const rect = elem.getBoundingClientRect();
                        if (rect.width > 50 && rect.height > 20) {
                            return {
                                type: 'hold_and_release',
                                duration_ms: 3500,
                                target_selector: null,
                                start_x: Math.floor(rect.left + rect.width / 2),
                                start_y: Math.floor(rect.top + rect.height / 2),
                                end_x: Math.floor(rect.left + rect.width / 2),
                                end_y: Math.floor(rect.top + rect.height / 2),
                                html: elem.outerHTML.substring(0, 300),
                                source: 'text-match: ' + text.substring(0, 50)
                            };
                        }
                    }
                }
                
                return null;
            }
            """)
            
            if not challenge_data:
                logger.debug("No challenge data extracted from page")
                return None
            
            logger.info(f"Challenge found via: {challenge_data.get('source', 'unknown')}")
            
            challenge_type_str = challenge_data.get('type', 'unknown')
            try:
                challenge_type = ChallengeType[challenge_type_str.upper()]
            except KeyError:
                challenge_type = ChallengeType.UNKNOWN
            
            return ChallengeData(
                challenge_type=challenge_type,
                duration_ms=challenge_data.get('duration_ms', 3000),
                target_selector=challenge_data.get('target_selector'),
                start_x=challenge_data.get('start_x', 0),
                start_y=challenge_data.get('start_y', 0),
                end_x=challenge_data.get('end_x', 0),
                end_y=challenge_data.get('end_y', 0),
                html_content=challenge_data.get('html'),
            )
        
        except Exception as e:
            logger.error(f"Error extracting challenge data: {e}")
            return None
    
    async def _solve_by_type(self, challenge: ChallengeData) -> bool:
        """Resolver challenge baseado no tipo"""
        logger.info(f"Solving {challenge.challenge_type.value} challenge")
        
        if challenge.challenge_type == ChallengeType.HOLD_AND_RELEASE:
            return await self._solve_hold_and_release(challenge)
        elif challenge.challenge_type == ChallengeType.SWIPE:
            return await self._solve_swipe(challenge)
        elif challenge.challenge_type == ChallengeType.CLICK:
            return await self._solve_click(challenge)
        elif challenge.challenge_type == ChallengeType.ROTATE:
            return await self._solve_rotate(challenge)
        else:
            logger.warning(f"Unknown challenge type: {challenge.challenge_type}")
            return False
    
    async def _solve_hold_and_release(self, challenge: ChallengeData) -> bool:
        """Resolver 'Hold and Release' challenge"""
        try:
            x, y = challenge.start_x, challenge.start_y
            duration = challenge.duration_ms
            
            logger.info(f"Pressing and holding at ({x}, {y}) for {duration}ms")
            
            # Pressionar
            await self.page.mouse.move(x, y)
            await self.page.mouse.down()
            
            # Segurar pelo tempo necessário
            await asyncio.sleep(duration / 1000.0)
            
            # Soltar
            await self.page.mouse.up()
            
            logger.info("Hold and release completed")
            return True
        
        except Exception as e:
            logger.error(f"Error in hold_and_release: {e}")
            return False
    
    async def _solve_swipe(self, challenge: ChallengeData) -> bool:
        """Resolver Swipe challenge"""
        try:
            start_x, start_y = challenge.start_x, challenge.start_y
            end_x, end_y = challenge.end_x, challenge.end_y
            
            logger.info(f"Swiping from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            
            # Swipe usando drag
            await self.page.mouse.move(start_x, start_y)
            await self.page.mouse.down()
            
            # Drag para o ponto final em passos pequenos
            steps = 10
            for i in range(steps):
                progress = (i + 1) / steps
                x = start_x + (end_x - start_x) * progress
                y = start_y + (end_y - start_y) * progress
                await self.page.mouse.move(int(x), int(y))
                await asyncio.sleep(0.05)
            
            await self.page.mouse.up()
            
            logger.info("Swipe completed")
            return True
        
        except Exception as e:
            logger.error(f"Error in swipe: {e}")
            return False
    
    async def _solve_click(self, challenge: ChallengeData) -> bool:
        """Resolver Click challenge"""
        try:
            x, y = challenge.start_x, challenge.start_y
            
            logger.info(f"Clicking at ({x}, {y})")
            
            await self.page.mouse.click(x, y)
            await asyncio.sleep(0.5)
            
            logger.info("Click completed")
            return True
        
        except Exception as e:
            logger.error(f"Error in click: {e}")
            return False
    
    async def _solve_rotate(self, challenge: ChallengeData) -> bool:
        """Resolver Rotate challenge (não implementado - placeholder)"""
        logger.warning("Rotate challenges not yet implemented")
        return False
    
    async def _extract_px3_token(self) -> Optional[str]:
        """Extrair _px3 cookie da página"""
        try:
            # Tentar extrair do cookie
            cookies = await self.context.cookies()
            for cookie in cookies:
                if cookie['name'] == '_px3':
                    logger.info(f"Found _px3 cookie: {cookie['value'][:50]}...")
                    return cookie['value']
            
            # Tentar extrair do localStorage/sessionStorage
            px3_from_storage = await self.page.evaluate("""
            () => {
                return localStorage.getItem('_px3') || 
                       sessionStorage.getItem('_px3') ||
                       null;
            }
            """)
            
            if px3_from_storage:
                logger.info(f"Found _px3 in storage: {px3_from_storage[:50]}...")
                return px3_from_storage
            
            return None
        
        except Exception as e:
            logger.error(f"Error extracting _px3 token: {e}")
            return None


async def solve_human_challenge(
    url: str,
    proxy: Optional[str] = None,
    headless: bool = True,
    timeout_ms: int = 30000,
) -> Tuple[bool, Optional[str]]:
    """
    Função helper para resolver human challenge em uma URL
    
    Args:
        url: URL com o challenge
        proxy: Proxy URL
        headless: Rodar em headless
        timeout_ms: Timeout em ms
        
    Returns:
        (success, _px3_token)
        
    Example:
        success, token = await solve_human_challenge("https://example.com")
        if success:
            print(f"Token: {token}")
    """
    solver = HumanChallengeSolver(
        headless=headless,
        timeout_ms=timeout_ms,
        proxy=proxy,
    )
    
    try:
        success, token = await solver.solve_challenge(url)
        return success, token
    finally:
        await solver.close()


# Wrapper síncrono para usar em código não-async
def solve_human_challenge_sync(
    url: str,
    proxy: Optional[str] = None,
    headless: bool = True,
    timeout_ms: int = 30000,
) -> Tuple[bool, Optional[str]]:
    """Versão síncrona do solver (para compatibilidade)"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        solve_human_challenge(url, proxy, headless, timeout_ms)
    )
