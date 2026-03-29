import os
import requests
from flask import Flask, redirect

app = Flask(__name__)

def get_live_link():
    # ID da TV Rio Sul no Globoplay
    video_id = "7832875"
    api_url = f"https://playback.video.globo.com/v1/videos/{video_id}/details"
    
    # Puxa os cookies que voce colou no Render
    glb_id = os.environ.get("GLB_COOKIE")
    glbid = os.environ.get("GLBID_VAL")
    
    headers = {
        "Cookie": f"GLOBO_ID={glb_id}; GLBID={glbid};",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        # Faz a requisição direta para a API de Playback da Globo
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Erro na API Globo: {response.status_code}")
            return None
            
        data = response.json()
        
        # Procura o link de manifesto m3u8 nos pontos de entrada
        entrypoints = data.get("entrypoints", [])
        for link in entrypoints:
            if "playlist.m3u8" in link:
                return link
        
        return None
    except Exception as e:
        print(f"Erro no script: {e}")
        return None

@app.route('/riosul.m3u8')
def proxy():
    link = get_live_link()
    if link:
        # Redireciona sua TV para o link fresco com o Token JWT
        return redirect(link)
    return "Erro: Cookies expirados ou sinal indisponivel. Atualize o GLOBO_ID no Render.", 403

@app.route('/')
def home():
    return "Bot TV Rio Sul Online - Use /riosul.m3u8"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
