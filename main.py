import os
import asyncio
from flask import Flask, redirect
from playwright.async_api import async_playwright

app = Flask(__name__)

async def get_raw_token_url():
    async with async_playwright() as p:
        # Launch com argumentos para economizar MUITA RAM
        browser = await p.chromium.launch(
            headless=True, 
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage", 
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--no-first-run",
                "--no-zygote",
                "--single-process" # Ajuda a manter tudo em um processo só
            ]
        )
        
        context = await browser.new_context(
            permissions=['geolocation'],
            geolocation={'latitude': -22.5442, 'longitude': -44.1736},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        
        # Bloqueio de imagens e CSS para economizar memória
        page = await context.new_page()
        await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,pdf}", lambda route: route.abort())

        glb_id = os.environ.get("GLB_COOKIE")
        glbid = os.environ.get("GLBID_VAL")
        
        cookies = []
        if glb_id: cookies.append({'name': 'GLOBO_ID', 'value': glb_id, 'domain': '.globo.com', 'path': '/'})
        if glbid: cookies.append({'name': 'GLBID', 'value': glbid, 'domain': '.globo.com', 'path': '/'})
        
        if cookies: await context.add_cookies(cookies)

        found = {"url": None}

        async def handle_request(request):
            if ".m3u8" in request.url and "/j/" in request.url:
                found["url"] = request.url

        page.on("request", handle_request)

        try:
            # Tempo de timeout menor para não estourar a memória esperando demais
            await page.goto("https://globoplay.globo.com/tv-globo/ao-vivo/7832875/", wait_until="commit", timeout=45000)
            
            for _ in range(15):
                if found["url"]: break
                await asyncio.sleep(1)
            
            return found["url"]
        except Exception as e:
            print(f"Erro no bot: {e}")
            return None
        finally:
            await browser.close()

@app.route('/riosul.m3u8')
def proxy():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        token_link = loop.run_until_complete(get_raw_token_url())
        
        if token_link:
            return redirect(token_link)
        return "Sinal não encontrado ou timeout de memória.", 404
    except Exception as e:
        return f"Erro: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
