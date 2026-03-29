import os
import asyncio
from flask import Flask, redirect
from playwright.async_api import async_playwright

app = Flask(__name__)

async def get_raw_token_url():
    browserless_token = os.environ.get("BROWSERLESS_TOKEN")
    user = os.environ.get("GLOBO_USER")
    password = os.environ.get("GLOBO_PASS")
    
    ws_endpoint = f"wss://chrome.browserless.io?token={browserless_token}"

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ws_endpoint)
        # Forçamos uma janela maior para o layout de login aparecer corretamente
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            permissions=['geolocation'],
            geolocation={'latitude': -22.5442, 'longitude': -44.1736},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        found = {"url": None}

        async def handle_request(request):
            if ".m3u8" in request.url and "/j/" in request.url:
                found["url"] = request.url

        page.on("request", handle_request)

        try:
            # 1. Vai para a página de login
            await page.goto("https://login.globo.com/login/438", wait_until="networkidle")
            
            # 2. Preenche e-mail e senha
            await page.fill("input[name='login']", user)
            await page.fill("input[name='password']", password)
            await page.click("button[type='submit']")
            
            # 3. Espera o login processar e vai para o canal
            await page.wait_for_timeout(5000) 
            await page.goto("https://globoplay.globo.com/tv-globo/ao-vivo/7832875/", wait_until="networkidle")
            
            # 4. Espera o link do vídeo aparecer nos requests
            for _ in range(30):
                if found["url"]: break
                await asyncio.sleep(1)
            
            return found["url"]
        except Exception as e:
            print(f"Erro na automação: {e}")
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
    return "Erro: Não foi possível logar ou encontrar o sinal automaticamente.", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
