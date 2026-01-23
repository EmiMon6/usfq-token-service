"""
Token Extractor - Extrae cookies y tokens de USFQ usando Playwright
"""
import nest_asyncio
from playwright.async_api import async_playwright
import json
import os
from typing import Dict, Optional

nest_asyncio.apply()


async def obtener_tokens(email: str, password: str) -> Dict[str, str]:
    """
    Extrae d2lSessionVal, d2lSecureSessionVal y CSRF Token de USFQ.
    
    Args:
        email: Email de USFQ
        password: Contraseña
        
    Returns:
        Dict con los tokens extraídos
    """
    print(f"🚀 Iniciando extracción para: {email}")

    async with async_playwright() as p:
        # Chrome headless para servidor
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        result = {
            "success": False,
            "d2lSessionVal": "",
            "d2lSecureSessionVal": "",
            "csrfToken": "",
            "error": None
        }

        try:
            print("🌍 1. Entrando al portal USFQ...")
            await page.goto('https://miusfv.usfq.edu.ec/d2l/home', timeout=30000)

            # --- LOGIN ---
            print("👤 2. Iniciando login...")
            await page.wait_for_selector('input[type="email"]', timeout=20000)
            await page.fill('input[type="email"]', email)
            await page.keyboard.press('Enter')

            await page.wait_for_selector('input[type="password"]', state='visible', timeout=20000)
            await page.fill('input[type="password"]', password)
            await page.wait_for_timeout(1500)
            await page.keyboard.press('Enter')

            # --- VERIFICACIÓN ---
            print("⏳ 3. Esperando autenticación...")
            try:
                await page.wait_for_url("https://miusfv.usfq.edu.ec/d2l/home", timeout=35000)
                print("✅ Login exitoso!")
            except:
                # Intenta aceptar 2FA si aparece
                if await page.is_visible("text=Yes") or await page.is_visible("input[type='submit']"):
                    await page.keyboard.press('Enter')
                    await page.wait_for_url("**/d2l/home", timeout=20000)

            # --- EXTRACCIÓN ---
            print("🕵️ 4. Extrayendo cookies y tokens...")

            # Obtener todas las cookies
            cookies = await context.cookies()

            # Filtrar las cookies relevantes
            result["d2lSessionVal"] = next(
                (c['value'] for c in cookies if c['name'] == 'd2lSessionVal'), 
                ""
            )
            result["d2lSecureSessionVal"] = next(
                (c['value'] for c in cookies if c['name'] == 'd2lSecureSessionVal'), 
                ""
            )

            # Buscar CSRF Token en localStorage
            local_storage = await page.evaluate("() => JSON.stringify(localStorage)")
            ls_data = json.loads(local_storage)

            # Buscar tokens en localStorage
            posibles_tokens = {k: v for k, v in ls_data.items() if 'Token' in k or 'csrf' in k.lower()}
            if posibles_tokens:
                result["csrfToken"] = list(posibles_tokens.values())[0]

            result["success"] = True
            print("✅ Tokens extraídos exitosamente!")

        except Exception as e:
            result["error"] = str(e)
            print(f"❌ Error: {e}")
            
            # Guardar screenshot para debug
            try:
                await page.screenshot(path='/app/data/error_screenshot.png')
            except:
                pass

        finally:
            await browser.close()

        return result
