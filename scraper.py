"""
Dominican Republic Lotteries Web Scraper & API Engine
Target source: https://loteriasdominicanas.com/
"""

import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import datetime
import re

LOTERIASDOMINICANAS_SITE_URL = "https://loteriasdominicanas.com/_site.json"
LOTERIASDOMINICANAS_BASE_URL = "https://loteriasdominicanas.com/"
CONECTATE_API_ENDPOINT = "https://api.conectate.com.do/conectate/sessions"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://loteriasdominicanas.com",
    "Referer": "https://loteriasdominicanas.com/",
    "Site-Env": "dominicana"
}

def format_lottery_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a lottery result item to be easily consumable by Android apps (Retrofit/Gson/Moshi/Kotlin).
    """
    nums = item.get("numeros", [])
    
    def fmt_num(val):
        if val is None:
            return ""
        if isinstance(val, int):
            return f"{val:02d}"
        s = str(val).strip()
        return s.zfill(2) if s.isdigit() and len(s) < 2 else s

    primero = fmt_num(nums[0]) if len(nums) > 0 else ""
    segundo = fmt_num(nums[1]) if len(nums) > 1 else ""
    tercero = fmt_num(nums[2]) if len(nums) > 2 else ""

    return {
        "id": str(item.get("id", "")),
        "sorteo_slug": item.get("sorteo_slug", ""),
        "sorteo_nombre": item.get("sorteo_nombre", ""),
        "compania": item.get("compania", ""),
        "fecha": item.get("fecha", ""),
        "hora": item.get("hora", ""),
        "numeros": [fmt_num(n) for n in nums],
        "primero": primero,
        "segundo": segundo,
        "tercero": tercero,
        "extra": item.get("extra", {}),
        "fuente": item.get("fuente", "loteriasdominicanas.com")
    }

class LotteryScraper:
    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout
        self.catalog_cache: Optional[Dict[str, Dict[str, Any]]] = None

    async def _fetch_catalog(self, client: httpx.AsyncClient) -> Dict[str, Dict[str, Any]]:
        """
        Fetch game catalog & metadata directly from https://loteriasdominicanas.com/_site.json
        """
        if self.catalog_cache and len(self.catalog_cache) > 0:
            return self.catalog_cache

        game_map = {}
        try:
            resp = await client.get(LOTERIASDOMINICANAS_SITE_URL, headers=HEADERS)
            if resp.status_code == 200:
                data = resp.json()
                for company in data.get("siteCompanies", []):
                    c_name = company.get("title", "Lotería Dominicana")
                    for game in company.get("siteGames", []):
                        g_title = game.get("title") or game.get("name")
                        seo_url = game.get("seo", {}).get("url") if isinstance(game.get("seo"), dict) else game.get("url", "")
                        
                        if not seo_url and g_title:
                            seo_url = re.sub(r'[^a-z0-9]+', '-', g_title.lower()).strip('-')

                        ids = set()
                        for key in ["game_id", "_id", "migration_game_id", "id"]:
                            v = game.get(key)
                            if v:
                                ids.add(str(v))
                        
                        if isinstance(game.get("game"), dict):
                            g_obj = game["game"]
                            for key in ["_id", "game_id", "migration_game_id"]:
                                v = g_obj.get(key)
                                if v:
                                    ids.add(str(v))

                        game_info = {
                            "game_id": list(ids)[0] if ids else "",
                            "title": g_title or "Sorteo",
                            "slug": seo_url,
                            "company": c_name
                        }

                        for gid in ids:
                            if gid not in game_map:
                                game_map[gid] = game_info

                self.catalog_cache = game_map
                return game_map
        except Exception as e:
            print(f"[Scraper Warning] Error fetching catalog from loteriasdominicanas.com: {e}")

        return {}

    async def get_latest_results(self) -> Dict[str, Any]:
        """
        Fetch latest winning numbers for all Dominican lotteries from loteriasdominicanas.com.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                catalog = await self._fetch_catalog(client)
                
                # Query today's date in ISO date-time
                now = datetime.datetime.now(datetime.timezone.utc)
                date_iso = now.strftime("%Y-%m-%dT04:00:00.000Z")
                
                url = f"{CONECTATE_API_ENDPOINT}?date={date_iso}"
                resp = await client.get(url, headers=HEADERS)
                
                # Fallback to yesterday if today is empty
                if resp.status_code == 200 and not resp.json():
                    yesterday = now - datetime.timedelta(days=1)
                    date_iso = yesterday.strftime("%Y-%m-%dT04:00:00.000Z")
                    url = f"{CONECTATE_API_ENDPOINT}?date={date_iso}"
                    resp = await client.get(url, headers=HEADERS)

                if resp.status_code == 200:
                    raw_data = resp.json()
                    formatted_list = []
                    for entry in raw_data:
                        gid = str(entry.get("game_id", ""))
                        sessions = entry.get("sessions", [])
                        if sessions:
                            last_s = sessions[0]
                            raw_scores = last_s.get("score", [])
                            
                            nums = []
                            for sub in raw_scores:
                                if isinstance(sub, list):
                                    for val in sub:
                                        if val is not None and str(val).strip():
                                            nums.append(str(val).strip())
                                elif isinstance(sub, str) and sub.strip():
                                    nums.append(sub.strip())
                                    
                            meta = catalog.get(gid, {})
                            title = meta.get("title", f"Sorteo {gid}")
                            slug = meta.get("slug")
                            if not slug:
                                slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
                                
                            company = meta.get("company", "Lotería Dominicana")
                            
                            raw_date = last_s.get("date", "")
                            formatted_date = raw_date[:10] if len(raw_date) >= 10 else raw_date
                            
                            formatted_list.append(format_lottery_item({
                                "id": gid,
                                "sorteo_slug": slug,
                                "sorteo_nombre": title,
                                "compania": company,
                                "fecha": formatted_date,
                                "hora": "",
                                "numeros": nums,
                                "extra": {
                                    "session_id": last_s.get("_id"),
                                    "createdAt": last_s.get("createdAt")
                                },
                                "fuente": "loteriasdominicanas.com"
                            }))
                            
                    if formatted_list:
                        return {
                            "status": "success",
                            "source": "loteriasdominicanas.com",
                            "count": len(formatted_list),
                            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            "data": formatted_list
                        }
        except Exception as e:
            print(f"[Scraper Warning] Primary fetch failed: {e}")

        return await self._scrape_fallback_latest()

    async def get_sorteos_catalog(self) -> Dict[str, Any]:
        """
        Fetch complete list of supported draws and companies from loteriasdominicanas.com.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                catalog = await self._fetch_catalog(client)
                if catalog:
                    data_list = [
                        {
                            "game_id": gid,
                            "sorteo_slug": meta.get("slug"),
                            "sorteo_nombre": meta.get("title"),
                            "compania": meta.get("company")
                        }
                        for gid, meta in catalog.items()
                    ]
                    return {
                        "status": "success",
                        "source": "loteriasdominicanas.com",
                        "count": len(data_list),
                        "data": data_list
                    }
        except Exception as e:
            print(f"[Scraper Warning] Sorteos catalog fetch failed: {e}")

        return {
            "status": "error",
            "message": "Could not retrieve sorteos catalog",
            "data": []
        }

    async def get_sorteo_detail(self, slug: str) -> Dict[str, Any]:
        """
        Fetch details / latest result for a specific draw slug.
        """
        latest = await self.get_latest_results()
        if latest.get("status") == "success":
            filtered = [
                it for it in latest.get("data", [])
                if it.get("sorteo_slug") == slug or slug in it.get("sorteo_slug", "") or slug in it.get("sorteo_nombre", "").lower()
            ]
            if filtered:
                return {
                    "status": "success",
                    "source": "loteriasdominicanas.com",
                    "slug": slug,
                    "count": len(filtered),
                    "data": filtered
                }
                
        return {
            "status": "error",
            "message": f"Could not retrieve details for draw slug: '{slug}'",
            "data": []
        }

    async def get_results_by_date(self, date_str: str) -> Dict[str, Any]:
        """
        Fetch winning numbers for a specific date (Format: YYYY-MM-DD).
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                catalog = await self._fetch_catalog(client)
                
                clean_date = date_str.strip()[:10]
                date_iso = f"{clean_date}T04:00:00.000Z"
                
                url = f"{CONECTATE_API_ENDPOINT}?date={date_iso}"
                resp = await client.get(url, headers=HEADERS)
                
                if resp.status_code == 200:
                    raw_data = resp.json()
                    formatted_list = []
                    for entry in raw_data:
                        gid = str(entry.get("game_id", ""))
                        sessions = entry.get("sessions", [])
                        if sessions:
                            last_s = sessions[0]
                            raw_scores = last_s.get("score", [])
                            
                            nums = []
                            for sub in raw_scores:
                                if isinstance(sub, list):
                                    for val in sub:
                                        if val is not None and str(val).strip():
                                            nums.append(str(val).strip())
                                elif isinstance(sub, str) and sub.strip():
                                    nums.append(sub.strip())
                                    
                            meta = catalog.get(gid, {})
                            title = meta.get("title", f"Sorteo {gid}")
                            slug = meta.get("slug")
                            if not slug:
                                slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
                                
                            company = meta.get("company", "Lotería Dominicana")
                            
                            formatted_list.append(format_lottery_item({
                                "id": gid,
                                "sorteo_slug": slug,
                                "sorteo_nombre": title,
                                "compania": company,
                                "fecha": clean_date,
                                "hora": "",
                                "numeros": nums,
                                "extra": {
                                    "session_id": last_s.get("_id"),
                                    "createdAt": last_s.get("createdAt")
                                },
                                "fuente": "loteriasdominicanas.com"
                            }))
                            
                    return {
                        "status": "success",
                        "source": "loteriasdominicanas.com",
                        "fecha": clean_date,
                        "count": len(formatted_list),
                        "data": formatted_list
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
        HTML scraper fallback for loteriasdominicanas.com.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(LOTERIASDOMINICANAS_BASE_URL, headers=HEADERS)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    results = []
                    for card in soup.find_all(["div", "article", "a"]):
                        text = card.get_text(" ", strip=True)
                        if any(name in text for name in ["Gana Más", "Quiniela Leidsa", "Lotería Nacional", "Lotería Real"]):
                            spans = [s.get_text(strip=True) for s in card.select("span") if s.get_text(strip=True).isdigit()]
                            if len(spans) >= 2:
                                name_match = re.search(r'(Gana Más|Quiniela Leidsa|Lotería Nacional|Quiniela Real|Loteka|La Primera|New York \w+|Florida \w+)', text)
                                name = name_match.group(1) if name_match else "Lotería Dominicana"
                                results.append(format_lottery_item({
                                    "sorteo_slug": re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'),
                                    "sorteo_nombre": name,
                                    "compania": "LoteriasDominicanas",
                                    "fecha": datetime.date.today().isoformat(),
                                    "hora": "",
                                    "numeros": spans,
                                    "extra": {},
                                    "fuente": "loteriasdominicanas.com/html"
                                }))
                                
                    if results:
                        return {
                            "status": "success",
                            "source": "loteriasdominicanas.com_html",
                            "count": len(results),
                            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            "data": results
                        }
        except Exception as e:
            print(f"[Scraper Warning] Fallback HTML scrape failed: {e}")

        return {
            "status": "error",
            "message": "All scraping mechanisms failed for loteriasdominicanas.com",
            "data": []
        }
