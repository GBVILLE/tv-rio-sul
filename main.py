import os
import asyncio
from flask import Flask, redirect
from playwright.async_api import async_playwright

app = Flask(__name__)

async def get_stream_url():
    async with async_playwright() as p:
        # Abre o navegador em modo invisível
        browser = await p.chromium.launch(headless=True)
        # Configura as coordenadas de Barra Mansa e permissão de GPS
        context = await browser.new_context(
            permissions=['geolocation'],
            geolocation={'latitude': -22.5442, 'longitude': -44.1736},
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()

        stream_url = []

        # Monitora o tráfego de rede para capturar o link .m3u8
        page.on("request", lambda request: stream_url.append(request.url) if ".m3u8" in request.url and "playlist" in request.url else None)

        try:
            # ID da TV Rio Sul que você passou
            await page.goto("https://globoplay.globo.com/tv-globo/ao-vivo/7832875/", wait_until="networkidle", timeout=60000)
            await asyncio.sleep(15) # Tempo para o player carregar o sinal
            
            # Filtra os links capturados para pegar o mais provável
            for url in stream_url:
                if "live" in url or "playback" in url:
                    return url
            return stream_url[0] if stream_url else None
        except:
            return None
        finally:
            await browser.close()

@app.route('/riosul.m3u8')
def riosul():
    # Executa a função assíncrona para pegar o link
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    link = loop.run_until_complete(get_stream_url())
    
    if link:
        return redirect(link)
    return "Erro ao extrair sinal. Verifique se a conta está logada.", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
