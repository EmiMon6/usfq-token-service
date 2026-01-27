"""
SRI Token Extractor - Código proporcionado por usuario
Navega por el menú del SRI para obtener cookies y ViewState
"""
import asyncio
import re
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger("uvicorn.error")

LOGIN_URL = (
    "https://srienlinea.sri.gob.ec/auth/realms/Internet/protocol/openid-connect/auth"
    "?client_id=app-sri-claves-angular"
    "&redirect_uri=https%3A%2F%2Fsrienlinea.sri.gob.ec%2Fsri-en-linea%2F%2Fcontribuyente%2Fperfil"
    "&response_mode=fragment&response_type=code&scope=openid"
)

PERFIL_URL = "https://srienlinea.sri.gob.ec/sri-en-linea/contribuyente/perfil"


async def get_viewstate(page) -> str | None:
    sel = "input[name='javax.faces.ViewState']"
    
    # Página principal
    try:
        loc = page.locator(sel).first
        if await loc.count():
            v = await loc.input_value(timeout=5000)
            if v:
                return v
    except:
        pass

    # Frames
    for fr in page.frames:
        try:
            loc = fr.locator(sel).first
            if await loc.count():
                v = await loc.input_value(timeout=5000)
                if v:
                    return v
        except:
            pass

    return None


async def click_text_anywhere(page, text: str, timeout=30000) -> bool:
    pat = re.compile(rf"^{re.escape(text)}$", re.I)

    candidates = [
        page.get_by_role("button", name=pat),
        page.get_by_role("link", name=pat),
        page.get_by_role("menuitem", name=pat),
        page.get_by_text(pat, exact=True),
        page.locator(f"text={text}").first,
    ]

    for loc in candidates:
        try:
            if await loc.count():
                await loc.first.scroll_into_view_if_needed(timeout=timeout)
                await loc.first.click(timeout=timeout)
                await page.wait_for_load_state("networkidle", timeout=30000)
                return True
        except:
            pass

    for fr in page.frames:
        fr_candidates = [
            fr.get_by_role("button", name=pat),
            fr.get_by_role("link", name=pat),
            fr.get_by_role("menuitem", name=pat),
            fr.get_by_text(pat, exact=True),
            fr.locator(f"text={text}").first,
        ]
        for loc in fr_candidates:
            try:
                if await loc.count():
                    await loc.first.scroll_into_view_if_needed(timeout=timeout)
                    await loc.first.click(timeout=timeout)
                    await page.wait_for_load_state("networkidle", timeout=30000)
                    return True
            except:
                pass

    return False


async def open_left_menu(page) -> bool:
    try:
        if await page.get_by_text(re.compile(r"Facturación electrónica", re.I)).first.is_visible(timeout=1200):
            return True
    except:
        pass

    await page.wait_for_timeout(800)

    selectors = [
        "button[aria-label*='Menú' i]",
        "button[aria-label*='Menu' i]",
        "button[title*='Menú' i]",
        "button[title*='Menu' i]",
        "button.mat-icon-button",
        "button:has(mat-icon)",
        "header button:has(svg)",
        "button:has(svg)",
        ".hamburger",
        ".menu-button",
        "[data-testid*='menu' i]",
        "[id*='menu' i]",
    ]

    for sel in selectors:
        try:
            loc = page.locator(sel)
            count = await loc.count()
            if not count:
                continue
            for i in range(min(count, 8)):
                el = loc.nth(i)
                try:
                    if await el.is_visible(timeout=800):
                        await el.click(timeout=3000, force=True)
                        await page.wait_for_timeout(900)
                        try:
                            if await page.get_by_text(re.compile(r"Facturación electrónica", re.I)).first.is_visible(timeout=1200):
                                return True
                        except:
                            pass
                except:
                    pass
        except:
            pass

    # JS click como último recurso
    try:
        clicked = await page.evaluate(
            """
            () => {
              const els = Array.from(document.querySelectorAll('button, a, div[role="button"]'));
              const cands = els.filter(el => {
                const a = (el.getAttribute('aria-label') || '').toLowerCase();
                const t = (el.getAttribute('title') || '').toLowerCase();
                return a.includes('menu') || a.includes('menú') || t.includes('menu') || t.includes('menú');
              });
              const el = cands.find(x => x.offsetParent !== null) || cands[0];
              if (el) { el.click(); return true; }
              return false;
            }
            """
        )
        if clicked:
            await page.wait_for_timeout(900)
            try:
                if await page.get_by_text(re.compile(r"Facturación electrónica", re.I)).first.is_visible(timeout=1200):
                    return True
            except:
                pass
    except:
        pass

    return False


async def click_real_consultar(page) -> bool:
    await page.wait_for_timeout(900)

    selectors = [
        "button:has-text('Consultar'):not([role='menuitem']):visible",
        "input[type='submit'][value*='Consultar' i]:visible",
        "input[type='button'][value*='Consultar' i]:visible",
        "a.ui-commandlink:has-text('Consultar'):visible",
        "button.ui-button:has-text('Consultar'):visible",
        "form button:has-text('Consultar'):visible",
    ]

    for sel in selectors:
        try:
            loc = page.locator(sel)
            if await loc.count():
                for i in range(await loc.count()):
                    el = loc.nth(i)
                    try:
                        if await el.is_visible(timeout=1200):
                            try:
                                where = await el.evaluate(
                                    "el => el.closest('nav, .menu, .sidebar, [role=\"navigation\"]') ? 'menu' : 'form'"
                                )
                                if where == "menu":
                                    continue
                            except:
                                pass

                            await el.scroll_into_view_if_needed(timeout=5000)
                            await el.click(timeout=10000, force=True)
                            await page.wait_for_load_state("networkidle", timeout=45000)
                            await page.wait_for_timeout(800)
                            return True
                    except:
                        pass
        except:
            pass

    for fr in page.frames:
        for sel in selectors:
            try:
                loc = fr.locator(sel)
                if await loc.count():
                    for i in range(await loc.count()):
                        el = loc.nth(i)
                        try:
                            if await el.is_visible(timeout=1200):
                                await el.scroll_into_view_if_needed(timeout=5000)
                                await el.click(timeout=10000, force=True)
                                await page.wait_for_load_state("networkidle", timeout=45000)
                                await page.wait_for_timeout(800)
                                return True
                        except:
                            pass
            except:
                pass

    return False


def build_cookie_header_dedup(cookies: list[dict]) -> str:
    last_by_name = {}
    last_pos = {}
    for i, c in enumerate(cookies):
        last_by_name[c["name"]] = c["value"]
        last_pos[c["name"]] = i

    names_in_order = [name for name, _ in sorted(last_pos.items(), key=lambda kv: kv[1])]
    return "; ".join(f"{name}={last_by_name[name]}" for name in names_in_order)


async def obtener_tokens_sri(ruc: str, password: str) -> dict:
    """
    Función principal para obtener tokens del SRI.
    Retorna dict con success, cookie_header, view_state, error
    """
    logger.info(f"🚀 [SRI] Iniciando extracción para RUC: {ruc}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled"
            ],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="es-ES",
            timezone_id="America/Guayaquil",
        )
        context.set_default_timeout(90000)
        page = await context.new_page()

        try:
            # 1) Login
            logger.info("⏳ [SRI] Navegando al login...")
            await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=120000)
            await page.wait_for_selector("#usuario", state="visible", timeout=30000)
            await page.fill("#usuario", ruc)
            await page.fill("#password", password)
            await page.keyboard.press("Enter")
            await page.wait_for_load_state("networkidle", timeout=60000)

            # Error Keycloak
            err = await page.query_selector("#kc-error-message")
            if err and await err.is_visible():
                error_text = (await err.inner_text()).strip()
                logger.error(f"❌ [SRI] Error login: {error_text}")
                return {"success": False, "error": f"Login fallido: {error_text}"}

            # 2) Perfil
            logger.info("⏳ [SRI] Yendo a perfil...")
            await page.goto(PERFIL_URL, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=30000)
            await page.wait_for_timeout(900)

            # 3) Menú
            logger.info("⏳ [SRI] Abriendo menú...")
            await open_left_menu(page)

            # 4) Navegar por menú
            menu_items = [
                "Facturación electrónica",
                "Producción",
                "Consultas",
                "Comprobantes electrónicos emitidos",
                "Consultar",
            ]
            for t in menu_items:
                logger.info(f"⏳ [SRI] Clickeando: {t}")
                if not await click_text_anywhere(page, t):
                    return {"success": False, "error": f"No se pudo hacer click en: {t}"}
                await page.wait_for_timeout(600)

            # 5) Consultar (acción)
            logger.info("⏳ [SRI] Ejecutando Consultar...")
            if not await click_real_consultar(page):
                return {"success": False, "error": "No se encontró el botón de ACCIÓN 'Consultar'"}

            # 6) Extraer datos
            await page.wait_for_load_state("networkidle", timeout=45000)
            await page.wait_for_timeout(800)

            viewstate = await get_viewstate(page)
            cookies = await context.cookies([page.url])
            cookie_header = build_cookie_header_dedup(cookies)

            logger.info(f"✅ [SRI] Éxito! Cookies: {len(cookie_header)} chars, ViewState: {len(viewstate) if viewstate else 0} chars")

            return {
                "success": True,
                "cookie_header": cookie_header,
                "view_state": viewstate or "",
                "final_url": page.url
            }

        except Exception as e:
            logger.error(f"❌ [SRI] Error crítico: {str(e)}")
            return {"success": False, "error": str(e)}

        finally:
            await browser.close()
