"""
Dominican Republic Lotteries Scraper API
Framework: FastAPI
Ready for Render deployment & Android App Integration
"""

from fastapi import FastAPI, Query, HTTPException, Path
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from scraper import LotteryScraper
import datetime
import uvicorn

app = FastAPI(
    title="Loterías RD Scraper API",
    description="API REST en Python para scraping y consulta en tiempo real de los resultados de las loterías de República Dominicana desde https://loteriasdominicanas.com/. Ideal para apps Android / iOS.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for cross-origin integration (Android apps, Web frontends, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scraper = LotteryScraper()

@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de estado del servicio para Render / Uptime Monitors."""
    return {
        "status": "online",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "service": "Loterias RD Scraper API",
        "target_source": "https://loteriasdominicanas.com/"
    }

@app.get("/api/loterias", tags=["Android Direct Endpoints"])
async def get_loterias_direct_json():
    """
    [Android Direct Endpoint]
    Retorna directamente la Lista (Array) JSON de los últimos resultados de las loterías dominicanas.
    Ideal para mapear en Android con Retrofit / Gson / Kotlin Serialization (`List<LoteriaItem>`).
    """
    results = await scraper.get_latest_results()
    data_list = results.get("data", [])
    return JSONResponse(content=data_list)

@app.get("/api/latest", tags=["Loterías"])
async def get_latest_results(
    raw: bool = Query(False, description="Si es True, retorna directamente la lista de elementos en JSON ([...]) sin envoltorio.")
):
    """
    Obtiene los últimos números ganadores publicados de todas las loterías dominicanas.
    """
    results = await scraper.get_latest_results()
    if raw:
        return JSONResponse(content=results.get("data", []))
    return JSONResponse(content=results)

@app.get("/api/sorteos", tags=["Loterías"])
async def get_sorteos_catalog(
    raw: bool = Query(False, description="Si es True, retorna directamente la lista de sorteos ([...]).")
):
    """
    Obtiene el catálogo completo de todos los sorteos dominicanos soportados (23+ sorteos).
    """
    catalog = await scraper.get_sorteos_catalog()
    if raw:
        return JSONResponse(content=catalog.get("data", []))
    return JSONResponse(content=catalog)

@app.get("/api/sorteo/{slug}", tags=["Loterías"])
async def get_sorteo_detail(
    slug: str = Path(..., description="Slug del sorteo (ej: 'gana-mas', 'loteria-nacional', 'leidsa-loto-mas', 'ny-noche', 'anguila-mananera')"),
    raw: bool = Query(False, description="Si es True, retorna directamente la lista de historial ([...]).")
):
    """
    Obtiene el historial de los últimos 30 días de un sorteo en específico por su slug.
    """
    detail = await scraper.get_sorteo_detail(slug)
    if detail.get("status") == "error":
        raise HTTPException(status_code=404, detail=detail.get("message"))
    if raw:
        return JSONResponse(content=detail.get("data", []))
    return JSONResponse(content=detail)

@app.get("/api/fecha/{date_str}", tags=["Loterías"])
async def get_results_by_date(
    date_str: str = Path(..., description="Fecha en formato YYYY-MM-DD (ej: '2026-08-21')"),
    raw: bool = Query(False, description="Si es True, retorna directamente la lista de resultados ([...]).")
):
    """
    Obtiene todos los resultados correspondientes a una fecha específica.
    """
    results = await scraper.get_results_by_date(date_str)
    if raw:
        return JSONResponse(content=results.get("data", []))
    return JSONResponse(content=results)

@app.get("/api/scrape", tags=["Scraper Engine"])
async def trigger_scrape(
    raw: bool = Query(False, description="Si es True, retorna directamente la lista ([...]).")
):
    """
    Ejecuta el scraper en tiempo real contra la fuente oficial y retorna el dataset actualizado.
    """
    results = await scraper.get_latest_results()
    if raw:
        return JSONResponse(content=results.get("data", []))
    return JSONResponse(content=results)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def homepage():
    """
    Interfaz Web Interactiva de Inicio & Documentación Visual de la API.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Loterías RD - Scraper & API REST</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        fontFamily: {
                            sans: ['Plus Jakarta Sans', 'sans-serif'],
                            mono: ['JetBrains Mono', 'monospace'],
                        },
                        colors: {
                            brand: {
                                50: '#eef2ff',
                                500: '#6366f1',
                                600: '#4f46e5',
                                700: '#4338ca',
                                900: '#1e1b4b',
                            }
                        }
                    }
                }
            }
        </script>
        <style>
            body {
                background: #090d16;
                color: #f1f5f9;
            }
            .ball-gradient {
                background: radial-gradient(circle at 30% 30%, #38bdf8, #0284c7 60%, #0369a1);
                box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4), inset 0 2px 4px rgba(255, 255, 255, 0.4);
            }
            .ball-gradient-2 {
                background: radial-gradient(circle at 30% 30%, #f472b6, #db2777 60%, #be185d);
                box-shadow: 0 4px 12px rgba(219, 39, 119, 0.4), inset 0 2px 4px rgba(255, 255, 255, 0.4);
            }
            .ball-gradient-3 {
                background: radial-gradient(circle at 30% 30%, #fbbf24, #d97706 60%, #b45309);
                box-shadow: 0 4px 12px rgba(217, 119, 6, 0.4), inset 0 2px 4px rgba(255, 255, 255, 0.4);
            }
            .glass-card {
                background: rgba(15, 23, 42, 0.75);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            .glass-card:hover {
                border-color: rgba(99, 102, 241, 0.4);
                box-shadow: 0 8px 30px rgba(79, 70, 229, 0.15);
            }
        </style>
    </head>
    <body class="min-h-screen flex flex-col font-sans">
        <!-- Top Nav -->
        <header class="border-b border-slate-800 bg-slate-950/80 sticky top-0 z-50 backdrop-blur-md">
            <div class="max-w-7xl mx-w mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-extrabold text-white text-lg shadow-lg shadow-indigo-500/30">
                        🇩🇴
                    </div>
                    <div>
                        <h1 class="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                            Loterías RD <span class="text-xs bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 px-2 py-0.5 rounded-full font-mono">v1.0 Scraper</span>
                        </h1>
                        <p class="text-xs text-slate-400">Scraping en tiempo real optimizado para Android</p>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Render Ready
                    </span>
                    <a href="/docs" target="_blank" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-lg shadow-indigo-600/20">
                        Documentación Swagger (/docs) ↗
                    </a>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
            <!-- Hero Banner -->
            <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/50 to-slate-900 border border-indigo-500/20 p-6 sm:p-8">
                <div class="relative z-10 max-w-3xl space-y-4">
                    <div class="inline-flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-mono text-indigo-300 bg-indigo-950/80 border border-indigo-800/50">
                        <span>Android JSON Endpoint:</span> <code class="text-emerald-400 font-bold">/api/loterias</code>
                    </div>
                    <h2 class="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
                        Resultados Actualizados de Loterías Dominicanas
                    </h2>
                    <p class="text-sm sm:text-base text-slate-300">
                        API REST en Python lista para conectar directamente con tu app de <strong class="text-emerald-400">Android (Retrofit/Gson/Kotlin)</strong>. Retorna el JSON directo en formato limpio con campos individuales <code class="text-indigo-300">primero</code>, <code class="text-indigo-300">segundo</code> y <code class="text-indigo-300">tercero</code>.
                    </p>
                    <div class="flex flex-wrap items-center gap-3 pt-2">
                        <button onclick="fetchLatest()" class="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/25 transition-all flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                            Actualizar Resultados Ahora
                        </button>
                        <a href="/api/loterias" target="_blank" class="px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/25 transition-all flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path></svg>
                            Ver Directo JSON Android (/api/loterias) ↗
                        </a>
                    </div>
                </div>
            </div>

            <!-- Search & Controls -->
            <div class="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-900/50 p-4 rounded-xl border border-slate-800">
                <div class="relative w-full sm:w-80">
                    <input type="text" id="searchInput" onkeyup="filterLoterias()" placeholder="Buscar lotería (ej: Gana Más, Leidsa, NY)..." 
                           class="w-full bg-slate-950 border border-slate-800 text-white placeholder-slate-500 text-xs rounded-lg pl-9 pr-4 py-2.5 focus:outline-none focus:border-indigo-500 transition-all">
                    <svg class="w-4 h-4 text-slate-500 absolute left-3 top-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                </div>
                <div class="flex items-center gap-2 text-xs text-slate-400">
                    <span>Sorteos detectados:</span>
                    <strong id="lotteryCount" class="text-indigo-400 font-mono text-sm">--</strong>
                </div>
            </div>

            <!-- Live Lottery Results Cards Grid -->
            <div id="resultsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                <div class="col-span-full py-12 text-center text-slate-500">
                    <svg class="w-8 h-8 animate-spin mx-auto mb-3 text-indigo-500" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    Cargando sorteos en tiempo real...
                </div>
            </div>

            <!-- Interactive Endpoint Explorer -->
            <div class="space-y-4 pt-6 border-t border-slate-800">
                <h3 class="text-lg font-bold text-white flex items-center gap-2">
                    <svg class="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path></svg>
                    Endpoints JSON para tu App de Android
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="p-4 rounded-xl bg-slate-900 border border-emerald-500/30 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded">GET (Direct JSON Array)</span>
                            <a href="/api/loterias" target="_blank" class="text-xs text-emerald-400 font-bold hover:underline font-mono">/api/loterias ↗</a>
                        </div>
                        <p class="text-xs text-white font-bold">Android Direct JSON Array</p>
                        <p class="text-xs text-slate-400">Retorna directamente la lista JSON <code class="text-emerald-400">[ {...}, {...} ]</code> para mapear con Retrofit / Gson.</p>
                    </div>

                    <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded">GET</span>
                            <a href="/api/latest" target="_blank" class="text-xs text-indigo-400 hover:underline font-mono">/api/latest ↗</a>
                        </div>
                        <p class="text-xs text-slate-300 font-semibold">Últimos Resultados (Objeto envuelto)</p>
                        <p class="text-xs text-slate-400">Retorna el objeto con metadata <code class="text-indigo-300">{"status": "success", "data": [...]}</code>.</p>
                    </div>

                    <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded">GET</span>
                            <a href="/api/sorteo/gana-mas?raw=true" target="_blank" class="text-xs text-indigo-400 hover:underline font-mono">/api/sorteo/{slug}?raw=true ↗</a>
                        </div>
                        <p class="text-xs text-slate-300 font-semibold">Historial Directo por Sorteo</p>
                        <p class="text-xs text-slate-400">Retorna la lista directa de los últimos 30 días de un sorteo (ej: `gana-mas`).</p>
                    </div>

                    <div class="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded">GET</span>
                            <a href="/api/sorteos?raw=true" target="_blank" class="text-xs text-indigo-400 hover:underline font-mono">/api/sorteos?raw=true ↗</a>
                        </div>
                        <p class="text-xs text-slate-300 font-semibold">Catálogo Directo de Sorteos</p>
                        <p class="text-xs text-slate-400">Lista simple de los 23+ sorteos con nombre, hora y slug.</p>
                    </div>
                </div>
            </div>
        </main>

        <footer class="border-t border-slate-800 bg-slate-950 py-6 mt-12">
            <div class="max-w-7xl mx-auto px-4 text-center text-xs text-slate-500 space-y-1">
                <p>Loterías RD Scraper API • Diseñada para integración directa con Android & Render</p>
                <p class="text-slate-600">Fuente: <a href="https://dgiiapicloud.com/api/loterias" target="_blank" class="hover:underline">https://dgiiapicloud.com/api/loterias</a></p>
            </div>
        </footer>

        <script>
            let allResults = [];

            async function fetchLatest() {
                const grid = document.getElementById('resultsGrid');
                grid.innerHTML = `<div class="col-span-full py-12 text-center text-slate-500">
                    <svg class="w-8 h-8 animate-spin mx-auto mb-3 text-indigo-500" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    Obteniendo resultados...
                </div>`;
                
                try {
                    const res = await fetch('/api/loterias');
                    const json = await res.json();
                    if (Array.isArray(json)) {
                        allResults = json;
                        renderCards(allResults);
                    }
                } catch (e) {
                    grid.innerHTML = `<div class="col-span-full py-8 text-center text-rose-400">Error al cargar datos: ${e}</div>`;
                }
            }

            function renderCards(items) {
                const grid = document.getElementById('resultsGrid');
                document.getElementById('lotteryCount').innerText = items.length;

                if (items.length === 0) {
                    grid.innerHTML = `<div class="col-span-full py-8 text-center text-slate-400">No se encontraron loterías.</div>`;
                    return;
                }

                grid.innerHTML = items.map(item => {
                    const nums = item.numeros || [];
                    const ballsHtml = nums.map((num, i) => {
                        const bgClass = i === 0 ? 'ball-gradient' : (i === 1 ? 'ball-gradient-2' : 'ball-gradient-3');
                        const formatted = typeof num === 'number' ? (num < 10 ? '0' + num : num) : num;
                        return `<div class="w-12 h-12 rounded-full ${bgClass} flex items-center justify-center text-white font-extrabold text-lg tracking-wider">${formatted}</div>`;
                    }).join('');

                    return `
                        <div class="glass-card rounded-2xl p-5 flex flex-col justify-between space-y-4 transition-all duration-200" data-name="${item.sorteo_nombre.toLowerCase()}">
                            <div class="flex items-start justify-between">
                                <div>
                                    <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">${item.compania || 'Dominicana'}</span>
                                    <h3 class="text-base font-bold text-white mt-1">${item.sorteo_nombre}</h3>
                                </div>
                                <div class="text-right text-xs text-slate-400">
                                    <div class="font-mono text-slate-300">${item.fecha || ''}</div>
                                    <div class="text-[11px] text-slate-500">${item.hora || ''}</div>
                                </div>
                            </div>

                            <div class="flex items-center justify-center gap-3 py-2">
                                ${ballsHtml || '<span class="text-xs text-slate-500">Sin números</span>'}
                            </div>

                            <div class="grid grid-cols-3 gap-2 text-center text-xs bg-slate-950/60 p-2 rounded-xl border border-slate-800/60">
                                <div>
                                    <span class="text-[10px] text-slate-500 block uppercase">1ro</span>
                                    <strong class="text-sky-400 font-mono text-sm">${item.primero || '--'}</strong>
                                </div>
                                <div>
                                    <span class="text-[10px] text-slate-500 block uppercase">2do</span>
                                    <strong class="text-pink-400 font-mono text-sm">${item.segundo || '--'}</strong>
                                </div>
                                <div>
                                    <span class="text-[10px] text-slate-500 block uppercase">3ro</span>
                                    <strong class="text-amber-400 font-mono text-sm">${item.tercero || '--'}</strong>
                                </div>
                            </div>

                            <div class="flex items-center justify-between pt-1 text-xs">
                                <span class="text-slate-500 font-mono text-[11px]">slug: ${item.sorteo_slug}</span>
                                <button onclick='copyJSON(${JSON.stringify(JSON.stringify(item))})' class="text-slate-400 hover:text-indigo-400 transition-colors flex items-center gap-1">
                                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
                                    JSON
                                </button>
                            </div>
                        </div>
                    `;
                }).join('');
            }

            function filterLoterias() {
                const query = document.getElementById('searchInput').value.toLowerCase();
                const filtered = allResults.filter(item => item.sorteo_nombre.toLowerCase().includes(query) || (item.compania && item.compania.toLowerCase().includes(query)));
                renderCards(filtered);
            }

            function copyJSON(jsonStr) {
                navigator.clipboard.writeText(jsonStr);
                alert("JSON copiado al portapapeles");
            }

            // Initial fetch
            fetchLatest();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
