"""
Dominican Republic Lotteries Web Scraper & API Engine
Target source: https://dgiiapicloud.com/api/loterias
"""

import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import datetime
import re

DGII_API_ENDPOINT = "https://pptonanntevatndjyzmk.supabase.co/functions/v1/loterias-api"
FALLBACK_LOTERIAS_URL = "https://loteriasdominicanas.com/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Referer": "https://dgiiapicloud.com/api/loterias"
}

class LotteryScraper:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def get_latest_results(self) -> Dict[str, Any]:
        """
        Fetch latest winning numbers for all Dominican lotteries.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                # Primary attempt: Supabase endpoint powering dgiiapicloud.com
                url = f"{DGII_API_ENDPOINT}/latest"
                resp = await client.get(url, headers=HEADERS)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("ok") and "resultados" in data:
                        return {
                            "status": "success",
                            "source": "dgiiapicloud.com",
                            "count": len(data["resultados"]),
                            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            "data": data["resultados"]
                        }
        except Exception as e:
            print(f"[Scraper Warning] Primary fetch failed: {e}")

        # Fallback to direct HTML scrape of loteriasdominicanas
        return await self._scrape_fallback_latest()

    async def get_sorteos_catalog(self) -> Dict[str, Any]:
        """
        Fetch complete list of supported draws and companies.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                url = DGII_API_ENDPOINT
                payload = {"op": "sorteos"}
                resp = await client.post(url, json=payload, headers=HEADERS)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("ok") and "sorteos" in data:
                        return {
                            "status": "success",
                            "source": "dgiiapicloud.com",
                            "count": len(data["sorteos"]),
                            "data": data["sorteos"]
                        }
        except Exception as e:
            print(f"[Scraper Warning] Sorteos catalog fetch failed: {e}")

        # Fallback catalog
        default_sorteos = [
            {"sorteo_slug": "gana-mas", "sorteo_nombre": "Gana Más", "compania": "Lotería Nacional", "hora": "14:30"},
            {"sorteo_slug": "loteria-nacional", "sorteo_nombre": "Lotería Nacional Noche", "compania": "Lotería Nacional", "hora": "21:00"},
            {"sorteo_slug": "leidsa-quiniela", "sorteo_nombre": "Leidsa Quiniela Pale", "compania": "Leidsa", "hora": "20:55"},
            {"sorteo_slug": "leidsa-loto-mas", "sorteo_nombre": "Leidsa Loto Más", "compania": "Leidsa", "hora": "20:55"},
            {"sorteo_slug": "loteka-quiniela", "sorteo_nombre": "Loteka Quiniela", "compania": "Loteka", "hora": "19:55"},
            {"sorteo_slug": "primera-quiniela", "sorteo_nombre": "La Primera Día", "compania": "La Primera", "hora": "12:00"},
            {"sorteo_slug": "real-quiniela", "sorteo_nombre": "Lotería Real", "compania": "Lotería Real", "hora": "12:55"},
            {"sorteo_slug": "ny-tarde", "sorteo_nombre": "New York Tarde", "compania": "New York", "hora": "14:30"},
            {"sorteo_slug": "ny-noche", "sorteo_nombre": "New York Noche", "compania": "New York", "hora": "22:30"},
            {"sorteo_slug": "florida-day", "sorteo_nombre": "Florida Day", "compania": "Florida", "hora": "13:30"},
            {"sorteo_slug": "florida-night", "sorteo_nombre": "Florida Night", "compania": "Florida", "hora": "21:30"},
            {"sorteo_slug": "anguila-mananera", "sorteo_nombre": "Anguila Mañana", "compania": "Anguila", "hora": "10:00"},
            {"sorteo_slug": "king-lottery-tarde", "sorteo_nombre": "King Lottery Tarde", "compania": "King Lottery", "hora": "12:30"}
        ]
        return {
            "status": "success",
            "source": "fallback_catalog",
            "count": len(default_sorteos),
            "data": default_sorteos
        }

    async def get_sorteo_detail(self, slug: str) -> Dict[str, Any]:
        """
        Fetch history / detail for a specific draw slug.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                url = DGII_API_ENDPOINT
                payload = {"op": "sorteo", "slug": slug}
                resp = await client.post(url, json=payload, headers=HEADERS)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("ok"):
                        return {
                            "status": "success",
                            "source": "dgiiapicloud.com",
                            "slug": slug,
                            "count": len(data.get("historico", [])),
                            "data": data.get("historico", [])
                        }
        except Exception as e:
            print(f"[Scraper Warning] Sorteo detail fetch failed for '{slug}': {e}")

        return {
            "status": "error",
            "message": f"Could not retrieve history for draw: {slug}",
            "data": []
        }

    async def get_results_by_date(self, date_str: str) -> Dict[str, Any]:
        """
        Fetch winning numbers for a specific date (Format: YYYY-MM-DD).
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                url = DGII_API_ENDPOINT
                payload = {"op": "fecha", "fecha": date_str}
                resp = await client.post(url, json=payload, headers=HEADERS)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("ok"):
                        return {
                            "status": "success",
                            "source": "dgiiapicloud.com",
                            "fecha": date_str,
                            "count": len(data.get("resultados", [])),
                            "data": data.get("resultados", [])
                        }
        except Exception as e:
            print(f"[Scraper Warning] Fetch by date failed for '{date_str}': {e}")

        return {
            "status": "error",
            "message": f"Could not retrieve results for date: {date_str}",
            "data": []
        }

    async def _scrape_fallback_latest(self) -> Dict[str, Any]:
        """
        HTML Web scraper fallback for Dominican Lotteries.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(FALLBACK_LOTERIAS_URL, headers=HEADERS)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    results = []
                    # Parse lottery cards from HTML
                    cards = soup.select('.game-block, .lottery-block, div.block-game')
                    for card in cards:
                        title_el = card.select_one('.game-title, .title, h3, h4')
                        nums_els = card.select('.score span, .ball, .num')
                        if title_el and nums_els:
                            name = title_el.get_text(strip=True)
                            nums = []
                            for el in nums_els:
                                text = el.get_text(strip=True)
                                if text.isdigit():
                                    nums.append(int(text))
                            if nums:
                                results.append({
                                    "sorteo_slug": re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'),
                                    "sorteo_nombre": name,
                                    "compania": "Desconocida",
                                    "fecha": datetime.date.today().isoformat(),
                                    "hora": "12:00",
                                    "numeros": nums,
                                    "extra": {},
                                    "fuente": "html_scraper"
                                })
                    if results:
                        return {
                            "status": "success",
                            "source": "loteriasdominicanas_html",
                            "count": len(results),
                            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            "data": results
                        }
        except Exception as e:
            print(f"[Scraper Error] Fallback HTML parsing failed: {e}")

        return {
            "status": "error",
            "message": "Failed to scrape lottery results from primary and secondary sources",
            "data": []
        }
