import asyncio
from playwright.async_api import async_playwright
import logging

# Usar logger de uvicorn para que salga en los logs de EasyPanel
logger = logging.getLogger("uvicorn.error")

SRI_LOGIN_URL = "https://srienlinea.sri.gob.ec/auth/realms/Internet/protocol/openid-connect/auth?client_id=app-sri-clave-usuario&redirect_uri=https://srienlinea.sri.gob.ec/dashboard-internet/&response_type=code&scope=openid"
SRI_COMPROBANTES_URL = "https://srienlinea.sri.gob.ec/comprobantes-electronicos-internet/pages/consultas/recuperarComprobantes.jsf"

async def obtener_tokens_sri(ruc, password):
    logger.info(f"🚀 [SRI] Iniciando extracción para RUC: {ruc}")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            context.set_default_timeout(60000) # 60s timeout global
            page = await context.new_page()
            
            # 1. Login
            logger.info("⏳ [SRI] Navegando al login...")
            await page.goto(SRI_LOGIN_URL, wait_until="domcontentloaded")
            
            if not await page.query_selector("#usuario"):
                logger.error("❌ [SRI] No cargó formulario de login")
                return {"success": False, "error": "Bloqueo o error de carga en login SRI"}
            
            await page.fill("#usuario", ruc)
            await page.fill("#password", password)
            await page.click("#login-button")
            
            # 2. Esperar Dashboard
            logger.info("⏳ [SRI] Esperando redirección dashboard...")
            try:
                # Esperar hasta 45s por cualquier cambio de URL significativo
                await page.wait_for_url("**/dashboard-internet/**", timeout=45000)
            except Exception as e:
                logger.warning(f"⚠️ [SRI] Timeout esperando dashboard: {e}")
                
            # 3. Comprobantes
            logger.info("⏳ [SRI] Yendo a comprobantes...")
            await page.goto(SRI_COMPROBANTES_URL, wait_until="networkidle", timeout=60000)
            
            # 4. Extraer
            cookies = await context.cookies()
            cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            
            # ViewState
            view_state = await page.get_attribute("input[name='javax.faces.ViewState']", "value")
            
            if not view_state:
                 view_state = await page.evaluate("() => document.querySelector('input[name=\"javax.faces.ViewState\"]')?.value")

            if not view_state:
                logger.error("❌ [SRI] ViewState no encontrado")
                return {"success": False, "error": "ViewState no encontrado (posiblemente no cargó la página)"}

            logger.info("✅ [SRI] Éxito!")
            return {
                "success": True,
                "cookie_header": cookie_header,
                "view_state": view_state
            }
            
        except Exception as e:
            logger.error(f"❌ [SRI] Error crítico: {str(e)}")
            return {"success": False, "error": str(e)}
            
        finally:
            if 'browser' in locals():
                await browser.close()
