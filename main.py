import os
import asyncio
from flask import Flask, redirect
from playwright.async_api import async_playwright

app = Flask(__name__)

async def get_raw_token_url():
    browserless_token = os.environ.get("BROWSERLESS_TOKEN")
    # Adicionando flags de performance no link do Browserless
    ws_endpoint = f"wss://chrome.browserless.io?token={browserless_token}&--disable-notifications&--disable-extensions"

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(ws_endpoint)
        except Exception as e:
            print(f"Erro Browserless: {e}")
            return None
        
        # Setup de localização e IP (Fingerprint)
        context = await browser.new_context(
            permissions=['geolocation'],
            geolocation={'latitude': -22.5442, 'longitude': -44.1736}, # Barra Mansa
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        glb_id = os.environ.get("GLB_COOKIE")
        glbid = os.environ.get("GLBID_VAL")
        
        cookies = []
        if glb_id: cookies.append({'name': 'GLOBO_ID', 'value': glb_id, 'domain': '.globo.com', 'path': '/'})
        if glbid: cookies.append({'name': 'GLBID', 'value': glbid, 'domain': '.globo.com', 'path': '/'})
        
        if cookies: await context.add_cookies(cookies)

        page = await context.new_page()
        # Bloqueia coisas inúteis para o link aparecer mais rápido
        await page.route("**/*.{png,jpg,jpeg,gif,svg,css}", lambda route: route.abort())
        
        found = {"url": None}

        async def handle_request(request):
            if ".m3u8" in request.url and "/j/" in request.url:
                found["url"] = request.url

        page.on("request", handle_request)

        try:
            # Tempo maior de espera e navegação mais profunda
            await page.goto("https://globoplay.globo.com/tv-globo/ao-vivo/7832875/", wait_until="networkidle", timeout=60000)
            
            # Tenta clicar no player se ele não der play sozinho (opcional)
            await asyncio.sleep(5) 
            
            # Procura o link por até 30 segundos
            for _ in range(30):
                if found["url"]: break
                await asyncio.sleep(1)
            
            return found["url"]
        except Exception as e:
            print(f"Erro: {e}")
            return None
        finally:
            await browser.close()

@app.route('/riosul.m3u8')
def proxy():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    token_link = loop.run_until_complete(get_raw_token_url())
    if token_link:
        return redirect(token_link)
    return "Sinal não encontrado. Tente atualizar seus Cookies (GLOBO_ID e GLBID) no Render.", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
