#!/usr/bin/env python3
"""
Webmotors Scraper - Extrai dados de veículos do webmotors.com.br
Não precisa de PerimeterX - dados vêm no HTML (SSR)
"""

import requests
import re
import json
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

class WebmotorsScraper:
    BASE_URL = "https://www.webmotors.com.br"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
    }

    def search(self, estado="sc", marca=None, ano_min=None, ano_max=None, 
               preco_min=None, preco_max=None, tipo="carros", page=1) -> List[Dict]:
        """
        Busca veículos no Webmotors
        
        Args:
            estado: UF (sc, sp, rj, etc)
            marca: Marca do veículo (chevrolet, fiat, etc)
            ano_min/ano_max: Filtro de ano
            preco_min/preco_max: Filtro de preço
            tipo: carros ou motos
            page: Página de resultados
        
        Returns:
            Lista de veículos encontrados
        """
        # Construir URL
        path = f"/{tipo}/{estado}"
        if marca:
            path = f"/{tipo}/{marca}/{estado}"
        
        params = {
            "tipoveiculo": tipo,
            "page": page
        }
        if ano_min:
            params["anominimo"] = ano_min
        if ano_max:
            params["anomaximo"] = ano_max
        
        url = f"{self.BASE_URL}{path}"
        
        try:
            resp = requests.get(url, headers=self.HEADERS, params=params, timeout=15)
            resp.raise_for_status()
            return self._parse_listings(resp.text)
        except Exception as e:
            print(f"Erro ao buscar: {e}")
            return []

    def _parse_listings(self, html: str) -> List[Dict]:
        """Extrai veículos do HTML"""
        soup = BeautifulSoup(html, "html.parser")
        vehicles = []
        
        # Buscar links de veículos no padrão /comprar/marca/modelo/.../id
        links = soup.find_all("a", href=re.compile(r"/comprar/"))
        seen_ids = set()
        
        for link in links:
            href = link.get("href", "")
            # Extrair ID do anúncio
            match = re.search(r"/(\d{7,9})$", href)
            if not match or match.group(1) in seen_ids:
                continue
            
            ad_id = match.group(1)
            seen_ids.add(ad_id)
            
            # Extrair dados do card
            card = link.find_parent("div") or link
            text = card.get_text(" ", strip=True)
            
            vehicle = {"id": ad_id, "url": f"{self.BASE_URL}{href}"}
            
            # Extrair marca/modelo do href
            parts = href.replace("/comprar/", "").split("/")
            if len(parts) >= 2:
                vehicle["marca"] = parts[0].upper()
                vehicle["modelo"] = parts[1].upper().replace("-", " ")
            
            # Extrair preço
            price_match = re.search(r"R\$\s*([\d.]+)", text)
            if price_match:
                vehicle["preco"] = int(price_match.group(1).replace(".", ""))
            
            # Extrair ano
            year_match = re.search(r"(20\d{2})[/\-](20\d{2})", text)
            if year_match:
                vehicle["ano_fab"] = int(year_match.group(1))
                vehicle["ano_mod"] = int(year_match.group(2))
            
            # Extrair km
            km_match = re.search(r"([\d.]+)\s*[Kk]m", text)
            if km_match:
                vehicle["km"] = int(km_match.group(1).replace(".", ""))
            
            # Extrair cidade
            city_match = re.search(r"([A-Za-záàãéêíóôúç\s]+)\s*\(([A-Z]{2})\)", text)
            if city_match:
                vehicle["cidade"] = city_match.group(1).strip()
                vehicle["uf"] = city_match.group(2)
            
            # Abaixo da FIPE?
            vehicle["abaixo_fipe"] = "abaixo da fipe" in text.lower()
            
            # Imagem
            img = link.find("img")
            if img and img.get("src") and "image.webmotors" in img.get("src", ""):
                vehicle["imagem"] = img["src"]
            
            vehicles.append(vehicle)
        
        return vehicles

    def get_details(self, url: str) -> Optional[Dict]:
        """Busca detalhes de um anúncio específico"""
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            
            details = {"url": url}
            text = soup.get_text(" ", strip=True)
            
            # Extrair dados estruturados (JSON-LD)
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        details["structured_data"] = data
                except:
                    pass
            
            return details
        except Exception as e:
            print(f"Erro ao buscar detalhes: {e}")
            return None


def main():
    """Exemplo de uso"""
    scraper = WebmotorsScraper()
    
    print("Buscando carros em SC...")
    veiculos = scraper.search(estado="sc", page=1)
    
    print(f"\nEncontrados: {len(veiculos)} veículos\n")
    
    for v in veiculos[:10]:
        marca = v.get("marca", "?")
        modelo = v.get("modelo", "?")
        preco = v.get("preco", 0)
        ano = f"{v.get('ano_fab','?')}/{v.get('ano_mod','?')}"
        km = v.get("km", "?")
        cidade = v.get("cidade", "?")
        fipe = " [ABAIXO FIPE]" if v.get("abaixo_fipe") else ""
        
        print(f"  {marca} {modelo} | {ano} | {km}km | R${preco:,} | {cidade}{fipe}")
    
    print(f"\n{'='*70}")
    print(json.dumps(veiculos[:3], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
