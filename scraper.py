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

KNOWN_CONECTATE_GAMES = {
    "6966a6d1ea7015c3b8a3d44d": {
        "title": "Loto - Loto Más",
        "company": "Lotería Dominicana"
    },
    "6966a6d1ea7015c3b8a3d453": {
        "title": "Quiniela Leidsa",
        "company": "Leidsa"
    },
    "6966a6d1ea7015c3b8a3d459": {
        "title": "Super Kino TV",
        "company": "Leidsa"
    },
    "6966a6d1ea7015c3b8a3d45f": {
        "title": "Loto Pool",
        "company": "Leidsa"
    },
    "6966a6d1ea7015c3b8a3d465": {
        "title": "Super Palé",
        "company": "Lotería Dominicana"
    },
    "6966a6d1ea7015c3b8a3d471": {
        "title": "Pega 3 Más",
        "company": "Leidsa"
    },
    "6966a6d1ea7015c3b8a3d47c": {
        "title": "Lotería Nacional",
        "company": "Nacional"
    },
    "6966a6d1ea7015c3b8a3d482": {
        "title": "Gana Más",
        "company": "Nacional"
    },
    "6966a6d2ea7015c3b8a3d488": {
        "title": "Billetes Domingo",
        "company": "Nacional"
    },
    "6966a6d2ea7015c3b8a3d48e": {
        "title": "Juega + Pega +",
        "company": "Nacional"
    },
    "6966a6d2ea7015c3b8a3d4a8": {
        "title": "Loto Real",
        "company": "Real"
    },
    "6966a6d2ea7015c3b8a3d4ae": {
        "title": "Quiniela Real",
        "company": "Real"
    },
    "6966a6d2ea7015c3b8a3d4b4": {
        "title": "Super Palé",
        "company": "Lotería Dominicana"
    },
    "6966a6d2ea7015c3b8a3d4ba": {
        "title": "Tu Fecha Real",
        "company": "Real"
    },
    "6966a6d2ea7015c3b8a3d4c0": {
        "title": "Pega 4 Real",
        "company": "Real"
    },
    "6966a6d2ea7015c3b8a3d4c6": {
        "title": "Loto Pool",
        "company": "Leidsa"
    },
    "6966a6d2ea7015c3b8a3d4cc": {
        "title": "Nueva Yol Real",
        "company": "Real"
    },
    "69fd98465e76585b602695be": {
        "title": "Chance Real",
        "company": "Real"
    },
    "69fd98465e76585b602695c5": {
        "title": "Repartidera Real",
        "company": "Real"
    },
    "69fd98465e76585b602695cc": {
        "title": "Loto Pool Noche",
        "company": "Leidsa"
    },
    "6966a6d2ea7015c3b8a3d4d7": {
        "title": "Quiniela Loteka",
        "company": "Loteka"
    },
    "6966a6d2ea7015c3b8a3d4dd": {
        "title": "Mega Chances",
        "company": "Loteka"
    },
    "6966a6d2ea7015c3b8a3d4e6": {
        "title": "MegaLotto",
        "company": "Lotería Dominicana"
    },
    "6966a6d2ea7015c3b8a3d4ec": {
        "title": "Mega Chances Repartidera",
        "company": "Loteka"
    },
    "6966a6d2ea7015c3b8a3d4f2": {
        "title": "Toca 3",
        "company": "Loteka"
    },
    "6966a6d2ea7015c3b8a3d4fd": {
        "title": "Mega Millions",
        "company": "Americanas"
    },
    "6966a6d2ea7015c3b8a3d503": {
        "title": "PowerBall",
        "company": "Americanas"
    },
    "6966a6d2ea7015c3b8a3d509": {
        "title": "New York Tarde",
        "company": "Americanas"
    },
    "6966a6d2ea7015c3b8a3d50f": {
        "title": "New York Noche",
        "company": "Americanas"
    },
    "6966a6d2ea7015c3b8a3d515": {
        "title": "Florida Día",
        "company": "Americanas"
    },
    "6966a6d2ea7015c3b8a3d51b": {
        "title": "Florida Noche",
        "company": "Americanas"
    },
    "6966a6d2ea7015c3b8a3d521": {
        "title": "Cash 4 Life",
        "company": "Lotería Dominicana"
    },
    "6966a6d2ea7015c3b8a3d527": {
        "title": "Powerball Double Play",
        "company": "Americanas"
    },
    "6966a6d2ea7015c3b8a3d5c0": {
        "title": "La Primera Día",
        "company": "Primera"
    },
    "6966a6d2ea7015c3b8a3d5c6": {
        "title": "Primera Noche",
        "company": "Primera"
    },
    "6966a6d2ea7015c3b8a3d5cc": {
        "title": "Loto 5",
        "company": "Primera"
    },
    "6966a6d2ea7015c3b8a3d5d2": {
        "title": "El Quinielón Día",
        "company": "Primera"
    },
    "6966a6d2ea7015c3b8a3d5d8": {
        "title": "Quinielón Noche",
        "company": "Primera"
    },
    "6966a6d3ea7015c3b8a3d5e3": {
        "title": "La Suerte Día",
        "company": "La Suerte"
    },
    "6966a6d3ea7015c3b8a3d5e9": {
        "title": "La Suerte Tarde",
        "company": "La Suerte"
    },
    "6966a6d3ea7015c3b8a3d5f4": {
        "title": "LoteDom",
        "company": "LoteDom"
    },
    "6966a6d3ea7015c3b8a3d5fa": {
        "title": "El Quemaito Mayor",
        "company": "LoteDom"
    },
    "6966a6d3ea7015c3b8a3d600": {
        "title": "Super Palé",
        "company": "Lotería Dominicana"
    },
    "6966a6d3ea7015c3b8a3d606": {
        "title": "Agarra 4",
        "company": "LoteDom"
    },
    "6966a6d3ea7015c3b8a3d611": {
        "title": "Anguila 1:00 PM",
        "company": "Anguila"
    },
    "6966a6d3ea7015c3b8a3d617": {
        "title": "Anguila 6:00 PM",
        "company": "Anguila"
    },
    "6966a6d3ea7015c3b8a3d61d": {
        "title": "Anguila 9:00 PM",
        "company": "Anguila"
    },
    "6966a6d3ea7015c3b8a3d635": {
        "title": "Anguila 10:00 AM",
        "company": "Anguila"
    },
    "6a5114d907d516b9c5101dd5": {
        "title": "Anguila 8:00  AM",
        "company": "Anguila"
    },
    "6a3e91bd5036a431f5f3e801": {
        "title": "Anguila 9:00 AM",
        "company": "Anguila"
    },
    "6966a6d3ea7015c3b8a3d63b": {
        "title": "La Cuarteta 10:00 AM",
        "company": "Anguila"
    },
    "6a3e935d5036a431f5f3e8b2": {
        "title": "Anguila 11:00 AM",
        "company": "Anguila"
    },
    "6a3e94f85036a431f5f407b0": {
        "title": "Anguila 12:00 PM",
        "company": "Anguila"
    },
    "6966a6d3ea7015c3b8a3d623": {
        "title": "La Cuarteta 1:00 PM",
        "company": "Anguila"
    },
    "6a3e96e25036a431f5f40c87": {
        "title": "Anguila 2:00 PM",
        "company": "Anguila"
    },
    "6a3e97a25036a431f5f41eef": {
        "title": "Anguila 3:00 PM",
        "company": "Anguila"
    },
    "6a5116a607d516b9c5102db7": {
        "title": "Anguila 4:00 PM",
        "company": "Anguila"
    },
    "6a5116f607d516b9c510302f": {
        "title": "Anguila 5:00 PM",
        "company": "Anguila"
    },
    "6966a6d3ea7015c3b8a3d629": {
        "title": "La Cuarteta 6:00 PM",
        "company": "Anguila"
    },
    "6a51185b07d516b9c5104c69": {
        "title": "Anguila 7:00 PM",
        "company": "Anguila"
    },
    "6966a6d3ea7015c3b8a3d62f": {
        "title": "La Cuarteta 9:00 PM",
        "company": "Anguila"
    },
    "6a511ab407d516b9c510788d": {
        "title": "Anguila 8:00 PM",
        "company": "Anguila"
    },
    "6a511b0a07d516b9c5107d05": {
        "title": "Anguila 10:00 PM",
        "company": "Anguila"
    },
    "6966a6d3ea7015c3b8a3d646": {
        "title": "Loto Pool Día",
        "company": "Leidsa"
    },
    "6966a6d3ea7015c3b8a3d64c": {
        "title": "Loto Pool Noche",
        "company": "Leidsa"
    },
    "6966a6d3ea7015c3b8a3d652": {
        "title": "Pick 3 Día",
        "company": "King Lottery"
    },
    "6966a6d3ea7015c3b8a3d658": {
        "title": "Pick 3 Noche",
        "company": "King Lottery"
    },
    "6966a6d3ea7015c3b8a3d65e": {
        "title": "Pick 4 Día",
        "company": "King Lottery"
    },
    "6966a6d3ea7015c3b8a3d664": {
        "title": "Pick 4 Noche",
        "company": "King Lottery"
    },
    "6966a6d3ea7015c3b8a3d66a": {
        "title": "King Lottery Día",
        "company": "King Lottery"
    },
    "6966a6d3ea7015c3b8a3d670": {
        "title": "King Lottery Noche",
        "company": "King Lottery"
    },
    "6966a6d3ea7015c3b8a3d676": {
        "title": "Philipsburg Día",
        "company": "King Lottery"
    },
    "6966a6d3ea7015c3b8a3d67c": {
        "title": "Philipsburg Noche",
        "company": "King Lottery"
    },
    "6a4411b07f178816db959f3d": {
        "title": "Haiti Bolet 9:30 AM",
        "company": "Haiti Bolet"
    },
    "6a44125c7f178816db95a378": {
        "title": "Haiti Bolet 10:30 AM",
        "company": "Haiti Bolet"
    },
    "6a4414807f178816db95ac68": {
        "title": "Haiti Bolet 11:30 AM",
        "company": "Haiti Bolet"
    },
    "6a4414ae7f178816db95ac7e": {
        "title": "Haiti Bolet 5:30 PM",
        "company": "Haiti Bolet"
    },
    "6a4414d17f178816db95aca1": {
        "title": "Haiti Bolet 6:30 PM",
        "company": "Haiti Bolet"
    },
    "6a4414fc7f178816db95acb7": {
        "title": "Haiti Bolet 7:30 PM",
        "company": "Haiti Bolet"
    }
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
                            title = meta.get("title")
                            company = meta.get("company")
                            
                            # Fallback to KNOWN_CONECTATE_GAMES if catalog entry is missing or invalid
                            if not title or title.startswith("Sorteo "):
                                known_info = KNOWN_CONECTATE_GAMES.get(str(gid), {})
                                title = known_info.get("title", title or f"Sorteo {gid}")
                                if not company or company == "Lotería Dominicana":
                                    company = known_info.get("company", "Lotería Dominicana")
                            
                            if not company:
                                company = "Lotería Dominicana"
                                
                            slug = meta.get("slug")
                            if not slug or slug.startswith("sorteo-"):
                                slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
                            
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
                            title = meta.get("title")
                            company = meta.get("company")
                            
                            if not title or title.startswith("Sorteo "):
                                known_info = KNOWN_CONECTATE_GAMES.get(str(gid), {})
                                title = known_info.get("title", title or f"Sorteo {gid}")
                                if not company or company == "Lotería Dominicana":
                                    company = known_info.get("company", "Lotería Dominicana")
                            
                            if not company:
                                company = "Lotería Dominicana"
                                
                            slug = meta.get("slug")
                            if not slug or slug.startswith("sorteo-"):
                                slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
                            
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
