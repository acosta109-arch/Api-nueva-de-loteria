# 🇩🇴 API Scraper de Loterías de República Dominicana

API REST desarrollada en **Python + FastAPI** para scraping y consulta en tiempo real de las loterías dominicanas, apuntando a `https://loterias.conectate.com.do/`. Diseñada y configurada para despliegue automático e instantáneo en **Render** (Plan Gratuito disponible).

---

## 🚀 Características
- **Scraping en tiempo real**: Cobertura de los **78+ sorteos** de las loterías más jugadas en RD (*Lotería Nacional, Leidsa, Loteka, La Primera, Lotería Real, Anguila, King Lottery, New York, Florida, Lotedom, La Suerte*).
- **Fallback Automático**: Scraper secundario por HTML para garantización de alta disponibilidad.
- **Ready for Render**: Archivos de configuración listos (`render.yaml`, `Procfile`, `Dockerfile`, `requirements.txt`).
- **Dashboard Visual**: Interfaz web interactiva en la raíz `/` para visualizar los sorteos en tarjetas elegantes con modo oscuro y copiar JSON con un clic.
- **Documentación OpenAPI**: Documentación interactiva en `/docs` (Swagger UI) y `/redoc`.

---

## 🛠️ Estructura del Proyecto

```text
├── main.py              # Aplicación FastAPI con endpoints y UI Dashboard
├── scraper.py           # Motor de Scraping (HTTP Async Client + HTML Fallback)
├── requirements.txt     # Dependencias del proyecto Python
├── render.yaml          # Blueprint de despliegue para Render
├── Procfile            # Comando de inicio del servidor Uvicorn para Render
├── Dockerfile          # Contenedor opcional para despliegue Docker en Render
└── README.md           # Guía completa de uso y despliegue
```

---

## ⚡ Ejecución Local

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Iniciar el servidor local**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

3. **Acceder en el navegador**:
   - Dashboard Interactivo: [http://localhost:8000](http://localhost:8000)
   - Documentación Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🌐 Despliegue en Render (Paso a Paso)

### Opción 1: Despliegue desde GitHub (Recomendado)
1. Crea un repositorio en GitHub y sube todos los archivos de este proyecto.
2. Inicia sesión en [Render.com](https://render.com).
3. Haz clic en **New +** -> **Web Service**.
4. Conecta tu repositorio de GitHub.
5. Render detectará automáticamente la configuración:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Haz clic en **Create Web Service** y ¡listo! Render compilará y desplegará tu API.

### Opción 2: Despliegue con Blueprint (`render.yaml`)
1. En el panel de Render, selecciona **New +** -> **Blueprint**.
2. Conecta tu repositorio. Render leerá automáticamente el archivo `render.yaml` e instanciará el servicio.

---

## 📡 Endpoints de la API

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/` | Dashboard web visual interactivo |
| `GET` | `/health` | Verificación de estado de la API (Healthcheck) |
| `GET` | `/api/latest` | Últimos números ganadores de todas las loterías |
| `GET` | `/api/sorteos` | Catálogo completo de sorteos disponibles |
| `GET` | `/api/sorteo/{slug}` | Historial de los últimos 30 días de un sorteo (ej: `gana-mas`) |
| `GET | `/api/fecha/{YYYY-MM-DD}` | Resultados de una fecha específica |
| `GET` | `/api/scrape` | Trigger de scraping directo en tiempo real |

---

## 📄 Ejemplo de Respuesta JSON (`/api/latest`)

```json
{
  "status": "success",
  "source": "dgiiapicloud.com",
  "count": 23,
  "timestamp": "2026-08-21T13:45:00.000Z",
  "data": [
    {
      "id": "434920df-1b04-4e7d-9ebf-9b2a5a4764a5",
      "sorteo_slug": "gana-mas",
      "sorteo_nombre": "Gana Más",
      "compania": "Lotería Nacional",
      "fecha": "2026-08-21",
      "hora": "14:30",
      "numeros": [40, 72, 18],
      "extra": {},
      "fuente": "firecrawl:multi"
    }
  ]
}
```

---

## 🛡️ Licencia & Términos
Desarrollado para uso libre y libre integración en aplicaciones móviles o web.
