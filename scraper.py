"""
Dominican Republic Lotteries Web Scraper & API Engine
Target source: https://loterias.conectate.com.do/
"""

import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import datetime
import re

CONECTATE_API_ENDPOINT = "https://api.conectate.com.do/conectate/sessions"
CONECTATE_PAYLOAD_URL = "https://loterias.conectate.com.do/_payload.json"
CONECTATE_BASE_URL = "https://loterias.conectate.com.do/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://loterias.conectate.com.do",
    "Referer": "https://loterias.conectate.com.do/"
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
        "fuente": item.get("fuente", "loterias.conectate.com.do")
    }

class LotteryScraper:
    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout
        self.catalog_cache: Optional[Dict[str, Dict[str, Any]]] = None
        self.company_cache: Optional[Dict[str, str]] = None

    async def _fetch_catalog(self, client: httpx.AsyncClient) -> Dict[str, Dict[str, Any]]:
        """Fetch game metadata & mapping from loterias.conectate.com.do _payload.json"""
        if self.catalog_cache and len(self.catalog_cache) > 0:
            return self.catalog_cache
            
        try:
            resp = await client.get(CONECTATE_PAYLOAD_URL, headers=HEADERS)
            if resp.status_code == 200:
                payload = resp.json()
                
                def deref(obj, depth=0):
                    if depth > 6:
                        return str(obj)
                    if isinstance(obj, int) and 0 <= obj < len(payload):
                        val = payload[obj]
                        if isinstance(val, (dict, list)):
                            return deref(val, depth + 1)
                        return val
                    elif isinstance(obj, dict):
                        return {k: deref(v, depth + 1) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [deref(v, depth + 1) for v in obj]
                    return obj
        
                company_map = {}
                for item in payload:
                    if isinstance(item, dict) and item.get("siteGames") and item.get("title"):
                        d_item = deref(item)
                        cid = d_item.get("_id")
                        title = d_item.get("title")
                        if cid and title:
                            company_map[cid] = title

                game_map = {}
                for item in payload: 
                    if isinstance(item, dict):
                        d_item = deref(item)
                        # Grab any ID: game_id (primary), _id (company page objects), migration_game_id (legacy mapping)
                        ids_to_map = []
                        g_id = d_item.get("game_id") or d_item.get("_id")
                        mig_id = d_item.get("migration_game_id")
                        if g_id:
                            ids_to_map.append(g_id)
                        if mig_id and mig_id not in ids_to_map:
                            ids_to_map.append(mig_id)

                        # Only proceed if item has a human-readable title
                        title = d_item.get("title") or d_item.get("mobile_title") or d_item.get("name")
                        if not ids_to_map or not title or not isinstance(title, str):
                            continue

                        slug = d_item.get("seo", {}).get("url") if isinstance(d_item.get("seo"), dict) else d_item.get("url", "")
                        if not slug:
                            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

                        scid = d_item.get("site_company_id") or d_item.get("company_id")
                        company = company_map.get(scid, "Lotería Dominicana")

                        game_info = {
                            "game_id": ids_to_map[0],
                            "title": title,
                            "slug": slug,
                            "company": company
                        }
                        for gid in ids_to_map:
                            # Don't overwrite an entry that already has a specific game_id match
                            if gid not in game_map:
                                game_map[gid] = game_info

                self.catalog_cache = game_map
                self.company_cache = company_map
                return game_map
        except Exception as e:
            print(f"[Scraper Warning] Error fetching catalog payload: {e}")
            
        return {}

    async def get_latest_results(self) -> Dict[str, Any]:
        """
        Fetch latest winning numbers for all Dominican lotteries from loterias.conectate.com.do.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                catalog = await self._fetch_catalog(client)
                
                # Query today's date in ISO date-time
                now = datetime.datetime.now(datetime.timezone.utc)
                date_iso = now.strftime("%Y-%m-%dT04:00:00.000Z")
                
                url = f"{CONECTATE_API_ENDPOINT}?date={date_iso}"
                resp = await client.get(url, headers=HEADERS)
                
                # If today has no results yet, fallback to yesterday's date
                if resp.status_code == 200 and not resp.json():
                    yesterday = now - datetime.timedelta(days=1)
                    date_iso = yesterday.strftime("%Y-%m-%dT04:00:00.000Z")
                    url = f"{CONECTATE_API_ENDPOINT}?date={date_iso}"
                    resp = await client.get(url, headers=HEADERS)
                    
                if resp.status_code == 200:
                    raw_data = resp.json()
                    formatted_list = []
                    for entry in raw_data:
                        gid = entry.get("game_id")
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
                            slug = meta.get("slug", title.lower().replace(" ", "-"))
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
                                "fuente": "loterias.conectate.com.do"
                            }))
                            
                    if formatted_list:
                        return {
                            "status": "success",
                            "source": "loterias.conectate.com.do",
                            "count": len(formatted_list),
                            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            "data": formatted_list
                        }
        except Exception as e:
            print(f"[Scraper Warning] Primary fetch failed: {e}")

        return await self._scrape_fallback_latest()

    async def get_sorteos_catalog(self) -> Dict[str, Any]:
        """
        Fetch complete list of supported draws and companies from loterias.conectate.com.do.
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
                        "source": "loterias.conectate.com.do",
                        "count": len(data_list),
                        "data": data_list
                    }
        except Exception as e:
            print(f"[Scraper Warning] Sorteos catalog fetch failed: {e}")

        default_sorteos = [
            {"sorteo_slug": "gana-mas", "sorteo_nombre": "Gana Más", "compania": "Nacional", "hora": "14:30"},
            {"sorteo_slug": "quiniela-nacional", "sorteo_nombre": "Lotería Nacional Noche", "compania": "Nacional", "hora": "21:00"},
            {"sorteo_slug": "quiniela-pale", "sorteo_nombre": "Quiniela Leidsa", "compania": "Leidsa", "hora": "20:55"},
            {"sorteo_slug": "loto-mas", "sorteo_nombre": "Loto Leidsa", "compania": "Leidsa", "hora": "20:55"},
            {"sorteo_slug": "quiniela-loteka", "sorteo_nombre": "Quiniela Loteka", "compania": "Loteka", "hora": "19:55"},
            {"sorteo_slug": "la-primera-dia", "sorteo_nombre": "La Primera Día", "compania": "Primera", "hora": "12:00"},
            {"sorteo_slug": "quiniela-real", "sorteo_nombre": "Quiniela Real", "compania": "Real", "hora": "12:55"},
            {"sorteo_slug": "new-york-tarde", "sorteo_nombre": "New York Tarde", "compania": "Americanas", "hora": "14:30"},
            {"sorteo_slug": "new-york-noche", "sorteo_nombre": "New York Noche", "compania": "Americanas", "hora": "22:30"}
        ]
        return {
            "status": "success",
            "source": "fallback_catalog",
            "count": len(default_sorteos),
            "data": default_sorteos
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
                    "source": "loterias.conectate.com.do",
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
                
                # Format to ISO date-time required by Conectate API
                clean_date = date_str.strip()[:10]
                date_iso = f"{clean_date}T04:00:00.000Z"
                
                url = f"{CONECTATE_API_ENDPOINT}?date={date_iso}"
                resp = await client.get(url, headers=HEADERS)
                
                if resp.status_code == 200:
                    raw_data = resp.json()
                    formatted_list = []
                    for entry in raw_data:
                        gid = entry.get("game_id")
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
                            slug = meta.get("slug", title.lower().replace(" ", "-"))
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
                                "fuente": "loterias.conectate.com.do"
                            }))
                            
                    return {
                        "status": "success",
                        "source": "loterias.conectate.com.do",
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
        HTML scraper fallback for loterias.conectate.com.do.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(CONECTATE_BASE_URL, headers=HEADERS)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    results = []
                    # Fallback HTML parser for card elements
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
                                    "compania": "Conectate",
                                    "fecha": datetime.date.today().isoformat(),
                                    "hora": "",
                                    "numeros": spans,
                                    "extra": {},
                                    "fuente": "loterias.conectate.com.do/html"
                                }))
                                
                    if results:
                        return {
                            "status": "success",
                            "source": "loterias.conectate.com.do_html",
                            "count": len(results),
                            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            "data": results
                        }
        except Exception as e:
            print(f"[Scraper Error] Fallback HTML parsing failed: {e}")

        return {
            "status": "error",
            "message": "Failed to retrieve results from loterias.conectate.com.do",
            "data": []
        }
