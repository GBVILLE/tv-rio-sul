import os
import requests
from flask import Flask, redirect

app = Flask(__name__)

def get_live_link():
    video_id = "7832875"
    # Mudamos para o endpoint global de assets que é menos rigoroso com IP
    api_url = f"https://playback.video.globo.com/v1/videos/{video_id}/details"
    
    glb_id = os.environ.get("GLB_COOKIE")
    glbid = os.environ.get("GLBID_VAL")
    
    headers = {
        "Cookie": f"GLOBO_ID={glb_id}; GLBID={glbid};",
        "Content-Type": "application/json",
        # User-Agent idêntico ao que você usou para pegar o cookie
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Origin": "https://globoplay.globo.com",
        "Referer": "https://globoplay.globo.com/"
    }

    try:
        # Usamos uma sessão para manter os headers persistentes
        session = requests.Session()
        response = session.get(api_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"DEBUG: Status {response.status_code} - Talvez o IP do Render foi bloqueado.")
            return None
            
        data = response.json()
        entrypoints = data.get("entrypoints", [])
        
        # Filtramos o link que contém o token de autorização
        for link in entrypoints:
            if "playlist.m3u8" in link and "authorized" in link.lower() or "jwt" in link.lower():
                return link
            # Fallback para o primeiro link m3u8 se o acima não aparecer
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
        # Redirecionamento 302 direto para o servidor de borda da Globo
        return redirect(link)
    return "Erro: Cookies expirados ou bloqueio de IP. Tente renovar o GLOBO_ID.", 403

@app.route('/')
def home():
    return "Servidor Rio Sul Ativo. Use /riosul.m3u8"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
