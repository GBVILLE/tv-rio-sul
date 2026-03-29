import os
import requests
from flask import Flask, redirect, Response

app = Flask(__name__)

# Configurações vindas do seu Environment no Render
GLOBO_ID = os.environ.get("GLB_COOKIE")
GLBID = os.environ.get("GLBID_VAL")

def get_live_link():
    # Endpoint da API de Playback da Globo para a TV Rio Sul
    # O ID 7832875 é o código interno da Rio Sul no Globoplay
    api_url = "https://playback.video.globo.com/v1/videos/7832875/details"
    
    headers = {
        "Cookie": f"GLOBO_ID={GLOBO_ID}; GLBID={GLBID};",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        # 1. Pedimos os detalhes do vídeo para a API
        response = requests.get(api_url, headers=headers, timeout=10)
        data = response.json()
        
        # 2. Extraímos o link de transmissão (m3u8)
        # A API retorna várias opções, pegamos a principal de live
        for entry in data.get("entrypoints", []):
            if "playlist.m3u8" in entry:
                return entry
        
        return None
    except Exception as e:
        print(f"Erro ao pescar link: {e}")
        return None

@app.route('/riosul.m3u8')
def proxy():
    link = get_live_link()
    if link:
        # Redireciona para o link fresco gerado pela API
        return redirect(link)
    else:
        return "Erro: Cookies expirados ou API da Globo mudou.", 403

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
