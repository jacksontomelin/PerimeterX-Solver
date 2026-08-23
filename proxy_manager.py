"""
Proxy Detection and Management Module
Detecta e usa automaticamente proxies disponíveis no ambiente:
- Variáveis de ambiente (HTTP_PROXY, HTTPS_PROXY, etc)
- Coolify internal proxies
- Sistema proxy nativo
- Fallback para proxy público gratuito
"""

import os
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)


class ProxyManager:
    """Gerencia detecção e uso automático de proxies"""
    
    # Proxies públicos gratuitos confiáveis (fallback)
    FALLBACK_PROXIES = [
        "http://proxy.example.com:8080",  # Placeholder
        # Nota: Proxies públicos são unreliáveis - melhor não usar
        # Mas mantemos aqui como last resort
    ]
    
    # Variáveis de ambiente que Coolify pode injetar
    PROXY_ENV_VARS = [
        'HTTP_PROXY',
        'http_proxy',
        'HTTPS_PROXY',
        'https_proxy',
        'ALL_PROXY',
        'all_proxy',
        # Coolify specific
        'COOLIFY_HTTP_PROXY',
        'COOLIFY_PROXY',
    ]
    
    def __init__(self):
        self.detected_proxy = None
        self.proxy_source = None
        self.available_proxies = []
        self._detect_proxies()
    
    def _detect_proxies(self) -> None:
        """Detectar proxies disponíveis no ambiente"""
        
        logger.info("Detectando proxies disponíveis...")
        
        # 1. Verificar variáveis de ambiente
        env_proxy = self._detect_env_proxy()
        if env_proxy:
            self.detected_proxy = env_proxy
            self.proxy_source = "Environment Variable"
            logger.info(f"✅ Proxy detectado em variável de ambiente: {env_proxy}")
            self.available_proxies.append((env_proxy, "env"))
            return
        
        # 2. Tentar detectar Coolify proxy (mais específico)
        coolify_proxy = self._detect_coolify_proxy()
        if coolify_proxy:
            self.detected_proxy = coolify_proxy
            self.proxy_source = "Coolify Internal"
            logger.info(f"✅ Proxy Coolify detectado: {coolify_proxy}")
            self.available_proxies.append((coolify_proxy, "coolify"))
            return
        
        # 3. Tentar detectar proxy do sistema
        system_proxy = self._detect_system_proxy()
        if system_proxy:
            self.detected_proxy = system_proxy
            self.proxy_source = "System Proxy"
            logger.info(f"✅ Proxy do sistema detectado: {system_proxy}")
            self.available_proxies.append((system_proxy, "system"))
            return
        
        logger.warning("⚠️ Nenhum proxy detectado. Conexão direto será tentado.")
        self.detected_proxy = None
        self.proxy_source = "None (Direct Connection)"
    
    def _detect_env_proxy(self) -> Optional[str]:
        """Detectar proxy em variáveis de ambiente"""
        
        for var in self.PROXY_ENV_VARS:
            proxy = os.getenv(var)
            if proxy:
                logger.debug(f"Found proxy in {var}: {proxy}")
                return self._normalize_proxy(proxy)
        
        return None
    
    def _detect_coolify_proxy(self) -> Optional[str]:
        """Detectar proxy interno do Coolify"""
        
        # Coolify geralmente fornece proxy em variáveis específicas
        # ou pode ser configurado em settings
        
        # Tentar detectar por padrão conhecido
        known_coolify_vars = [
            'COOLIFY_PROXY_URL',
            'INTERNAL_PROXY',
            'CONTAINER_PROXY',
        ]
        
        for var in known_coolify_vars:
            proxy = os.getenv(var)
            if proxy:
                logger.debug(f"Found Coolify proxy in {var}: {proxy}")
                return self._normalize_proxy(proxy)
        
        return None
    
    def _detect_system_proxy(self) -> Optional[str]:
        """Detectar proxy do sistema"""
        
        try:
            # Verificar se há proxy detectado pelo urllib
            proxy_handler = urllib.request.ProxyHandler()
            opener = urllib.request.build_opener(proxy_handler)
            
            # Tentar resolver via urllib (detecta proxy do sistema)
            proxy = os.getenv('http_proxy') or os.getenv('HTTP_PROXY')
            if proxy:
                return self._normalize_proxy(proxy)
        
        except Exception as e:
            logger.debug(f"Could not detect system proxy: {e}")
        
        return None
    
    @staticmethod
    def _normalize_proxy(proxy_url: str) -> str:
        """Normalizar URL do proxy"""
        
        if not proxy_url:
            return None
        
        proxy_url = proxy_url.strip()
        
        # Adicionar protocolo se não houver
        if not proxy_url.startswith(('http://', 'https://', 'socks://', 'socks5://')):
            proxy_url = f'http://{proxy_url}'
        
        return proxy_url
    
    def get_proxy_dict(self) -> Dict[str, str]:
        """Retornar dicionário de proxies para requests/tls_client"""
        
        if not self.detected_proxy:
            return {}
        
        return {
            'http': self.detected_proxy,
            'https': self.detected_proxy,
        }
    
    def get_proxy_url(self) -> Optional[str]:
        """Retornar URL do proxy (para tls_client)"""
        return self.detected_proxy
    
    def test_proxy(self) -> Tuple[bool, Optional[str]]:
        """Testar se o proxy está funcionando"""
        
        if not self.detected_proxy:
            logger.info("Nenhum proxy para testar")
            return True, "No proxy configured"
        
        try:
            import requests
            
            # Testar conexão via proxy
            proxies = self.get_proxy_dict()
            response = requests.get(
                'https://httpbin.org/ip',
                proxies=proxies,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Proxy funcionando: {response.json()}")
                return True, response.json().get('origin')
            else:
                logger.warning(f"⚠️ Proxy retornou status {response.status_code}")
                return False, None
        
        except Exception as e:
            logger.warning(f"❌ Proxy test failed: {e}")
            return False, None
    
    def __str__(self) -> str:
        """String representation"""
        return f"ProxyManager(proxy={self.detected_proxy}, source={self.proxy_source})"
    
    def __repr__(self) -> str:
        return self.__str__()


class ProxyConfig:
    """Configuração de proxy para uso em PXSolver"""
    
    def __init__(self, explicit_proxy: Optional[str] = None):
        """
        Inicializar com proxy explícito ou detectar automaticamente
        
        Args:
            explicit_proxy: Se fornecido, usa este proxy em vez de detectar
        """
        
        if explicit_proxy:
            self.proxy = ProxyManager._normalize_proxy(explicit_proxy)
            self.auto_detected = False
            logger.info(f"Using explicit proxy: {self.proxy}")
        else:
            manager = ProxyManager()
            self.proxy = manager.get_proxy_url()
            self.auto_detected = True
            logger.info(f"Auto-detected proxy: {self.proxy} (from {manager.proxy_source})")
    
    def get_for_tls_client(self) -> Optional[str]:
        """Formato para tls_client (sem protocolo na maioria dos casos)"""
        if not self.proxy:
            return None
        
        # tls_client aceita proxy com protocolo
        return self.proxy
    
    def get_for_requests(self) -> Dict[str, str]:
        """Formato para requests library"""
        if not self.proxy:
            return {}
        
        return {
            'http': self.proxy,
            'https': self.proxy,
        }
    
    def get_for_playwright(self) -> Dict[str, str]:
        """Formato para Playwright"""
        if not self.proxy:
            return {}
        
        return {
            'server': self.proxy,
        }


# Singleton para uso global
_proxy_manager = None

def get_proxy_manager() -> ProxyManager:
    """Obter instância global do ProxyManager"""
    global _proxy_manager
    if _proxy_manager is None:
        _proxy_manager = ProxyManager()
    return _proxy_manager


def test_network_egress(target_url: str = "https://collector-pxiao7f0.px-cloud.net/api/v2/collector") -> Tuple[bool, Optional[str]]:
    """
    Testar se consegue acessar URL alvo (PerimeterX collector)
    
    Args:
        target_url: URL para testar (default: Nordstrom PerimeterX collector)
    
    Returns:
        (success: bool, error_message: Optional[str])
    """
    
    try:
        import requests
        
        manager = get_proxy_manager()
        proxies = manager.get_proxy_dict()
        
        logger.info(f"Testing network egress to {target_url}")
        
        response = requests.head(
            target_url,
            proxies=proxies if proxies else None,
            timeout=10,
            allow_redirects=True
        )
        
        logger.info(f"Network test - Status: {response.status_code}")
        
        if response.status_code < 500:
            logger.info("✅ Network egress OK")
            return True, None
        else:
            return False, f"Server error: {response.status_code}"
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Connection error: {e}")
        return False, f"Connection blocked: {str(e)}"
    
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout - connection might be blocked")
        return False, "Connection timeout"
    
    except Exception as e:
        logger.error(f"❌ Network test failed: {e}")
        return False, str(e)


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*70)
    print("Proxy Manager Demo")
    print("="*70 + "\n")
    
    manager = get_proxy_manager()
    print(f"Manager: {manager}")
    print(f"Detected Proxy: {manager.detected_proxy}")
    print(f"Source: {manager.proxy_source}")
    print()
    
    # Test proxy
    print("Testing proxy connectivity...")
    success, info = manager.test_proxy()
    if success:
        print(f"✅ Proxy OK - IP: {info}")
    else:
        print(f"❌ Proxy failed")
    print()
    
    # Test network egress
    print("Testing network egress to PerimeterX collector...")
    success, error = test_network_egress()
    if success:
        print(f"✅ Network egress OK")
    else:
        print(f"❌ Network egress blocked: {error}")
