import asyncio
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger("uvicorn.error")

SRI_LOGIN_URL = "https://srienlinea.sri.gob.ec/auth/realms/Internet/protocol/openid-connect/auth?client_id=app-sri-clave-usuario&redirect_uri=https://srienlinea.sri.gob.ec/dashboard-internet/&response_type=code&scope=openid"
SRI_COMPROBANTES_URL = "https://srienlinea.sri.gob.ec/comprobantes-electronicos-internet/pages/consultas/recuperarComprobantes.jsf"

async def obtener_tokens_sri(ruc, password):
    """
    Inicia sesión en el SRI y extrae las cookies y ViewState.
    """
    logger.info(f"Iniciando SRI extractor para RUC: {ruc}")
    
    async with async_playwright() as p:
        # Lanzar navegador
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage', # Importante para contenedores
                '--disable-gpu'
            ]
        )
        
        # Contexto con User Agent normal para evitar bloqueos
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # 1. Login
            logger.info("Navegando al login del SRI...")
            # Timeout largo porque a veces SRI es lento
            await page.goto(SRI_LOGIN_URL, timeout=60000)
            
            # Verificar si existe el campo de usuario
            if not await page.query_selector("#usuario"):
                return {"success": False, "error": "No cargó el formulario de login (bloqueo o error SRI)"}
            
            # Llenar
            await page.fill("#usuario", ruc)
            await page.fill("#password", password)
            await page.click("#login-button")
            
            # 2. Esperar Dashboard
            logger.info("Esperando login...")
            try:
                # Esperar navegación o elemento clave
                await page.wait_for_url("**/dashboard-internet/**", timeout=30000)
            except:
                # Si falló, verificar error en pantalla
                error_msg = await page.query_selector(".alert-error")
                if error_msg:
                    text = await error_msg.inner_text()
                    return {"success": False, "error": f"Login fallido: {text}"}
                
                # Verificar captcha
                if await page.query_selector("iframe[src*='recaptcha']"):
                    return {"success": False, "error": "CAPTCHA detectado - No se puede automatizar"}

                return {"success": False, "error": "Timeout esperando login (posible credenciales mal o sistema lento)"}

            # 3. Ir a Comprobantes
            logger.info("Navegando a Comprobantes Recibidos...")
            await page.goto(SRI_COMPROBANTES_URL, timeout=45000)
            
            # 4. Extraer Cookies
            cookies = await context.cookies()
            cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            
            # 5. Extraer ViewState
            # Intentar selector estándar JSF
            view_state = await page.get_attribute("input[name='javax.faces.ViewState']", "value")
            
            if not view_state:
                # Intento por JS directo
                view_state = await page.evaluate("() => document.querySelector('input[name=\"javax.faces.ViewState\"]')?.value")
            
            if not view_state or not cookie_header:
                return {"success": False, "error": "No se encontraron tokens (ViewState o Cookies vacíos)"}
            
            logger.info("Extracción SRI exitosa")
            return {
                "success": True,
                "cookie_header": cookie_header,
                "view_state": view_state
            }
            
        except Exception as e:
            logger.error(f"Error SRI: {str(e)}")
            return {"success": False, "error": str(e)}
            
        finally:
            await browser.close()
