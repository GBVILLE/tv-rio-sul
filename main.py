import os
import time
from flask import Flask, redirect
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

def capturar_m3u8():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Injeta Barra Mansa via GPS
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    params = {"latitude": -22.5442, "longitude": -44.1736, "accuracy": 100}
    driver.execute_cdp_cmd("Emulation.setGeolocationOverride", params)

    try:
        driver.get("https://globoplay.globo.com/tv-globo/ao-vivo/7832875/")
        time.sleep(15) # Tempo para o token ser gerado
        
        # O Bot vasculha o tráfego de rede em busca do arquivo .m3u8
        logs = driver.get_log('performance')
        for entry in logs:
            if '.m3u8' in entry['message'] and 'playlist' in entry['message']:
                import json
                log = json.loads(entry['message'])['message']
                url = log['params'].get('request', {}).get('url')
                if url: return url
        return driver.current_url # Fallback se não achar o bruto
    except:
        return None
    finally:
        driver.quit()

@app.route('/riosul.m3u8')
def streaming():
    link_real = capturar_m3u8()
    if link_real:
        return redirect(link_real)
    return "Erro ao extrair sinal", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
