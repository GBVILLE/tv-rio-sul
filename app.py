import requests
import os
from flask import Flask, redirect, Response

app = Flask(__name__)

# Token de Sessão (Mantenha sincronizado com o horário de Brasília UTC-3)
GLBID = '15bb8cfbffddc9e02868eb40619b4d57544694c753876437335656751364244316e48635336416d5f3062794434686f61596d393575566f477957397a6b586a705249586d366b4a4e61736b5849627536526f7a356e72766f61526f444b4a4f695a4a784159513d3d3a303a75747171726d3831757977787373676f76657232'

@app.route('/live/globo-res.m3u8')
def proxy_globo_res():
    auth_api = "https://playback.video.globo.com/v5/video-session"
    
    payload = {
        "player_type": "desktop",
        "video_id": "4452349",
        "quality": "max",
        "content_protection": "widevine",
        "vsid": "45a762f4-3c67-1280-9209-8976f7c721d0",
        "tz": "-03:00",
        "capabilities": {
            "low_latency": True,
            "smart_mosaic": True,
            "max_frame_rate": "60",
            "dvr": True
        },
        "consumption": "streaming",
        "metadata": {
            "name": "web",
            "device": {"type": "desktop", "os": {}}
        },
        "version": 2
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'Referer': 'https://globoplay.globo.com/',
        'Origin': 'https://globoplay.globo.com',
        'X-Forwarded-For': '177.71.182.114',
        'True-Client-IP': '177.71.182.114'
    }

    try:
        response = requests.post(auth_api, json=payload, headers=headers, cookies={'GLBID': GLBID}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            stream_url = data['sources'][0]['url']
            return redirect(stream_url, code=302)
        return Response(response.text, status=response.status_code)
    
    except Exception as e:
        return Response(f"Erro na Bridge: {str(e)}", status=500)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5080))
    app.run(host='0.0.0.0', port=port, threaded=True)
