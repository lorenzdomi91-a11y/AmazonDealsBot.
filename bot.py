import os
import sys
import time
import random
import json
import subprocess
from datetime import datetime

# ===== VERIFICA CHE CHROME SIA INSTALLATO =====
def verifica_chrome():
    try:
        result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Chrome trovato: {result.stdout.strip()}")
            return True
    except:
        pass
    
    try:
        result = subprocess.run(['chromium-browser', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Chromium trovato: {result.stdout.strip()}")
            return True
    except:
        pass
    
    print("❌ Chrome/Chromium NON TROVATO!")
    print("📥 Installa Chrome con: sudo apt install google-chrome-stable")
    print("   Oppure esegui: ./install.sh")
    return False

# ===== VERIFICA CHE LE LIBRERIE SIANO INSTALLATE =====
def verifica_librerie():
    try:
        import undetected_chromedriver
        import selenium
        import bs4
        import flask
        print("✅ Tutte le librerie sono installate")
        return True
    except ImportError as e:
        print(f"❌ Libreria mancante: {e}")
        print("📥 Installa con: pip install -r requirements.txt")
        return False

# ===== MAIN CON VERIFICHE =====
if __name__ == "__main__":
    print("=" * 60)
    print("🛡️ AMAZON OFFERTE BOT - VERIFICA SISTEMA")
    print("=" * 60)
    
    if not verifica_chrome():
        sys.exit(1)
    
    if not verifica_librerie():
        sys.exit(1)
    
    print("✅ Sistema pronto!")
    print("=" * 60)
    
    # Avvia il bot vero e proprio
    from bot import AmazonStealthBot
    bot = AmazonStealthBot()
    bot.esegui_scansione()
    
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time
import random
import os
from datetime import datetime
from proxy_manager import proxy_manager
from fake_useragent import UserAgent
import logging

# Disabilita log di selenium
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

class AmazonStealthBot:
    def __init__(self):
        self.sconto_minimo = 15
        self.categorie = [
            'elettronica', 'informatica', 'casa', 'moda',
            'giocattoli', 'libri', 'beauty', 'sport'
        ]
        self.max_pagine = 2
        self.offerte_trovate = []
        self.ua = UserAgent()
        self.driver = None
        
    def avvia_browser(self):
        """Avvia Chrome con massimo stealth"""
        print("🚀 Avvio browser stealth...")
        
        options = uc.ChromeOptions()
        
        # ====== STRATEGIE STEALTH ======
        
        # 1. Nascondi automazione
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        
        # 2. Disabilita cose inutili
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        
        # 3. User Agent casuale
        user_agent = self.ua.random
        options.add_argument(f'--user-agent={user_agent}')
        
        # 4. Proxy (se disponibile)
        proxy = proxy_manager.ottieni_proxy()
        if proxy:
            options.add_argument(f'--proxy-server={proxy["http"]}')
            print(f"🌐 Usando proxy: {proxy['http']}")
        
        # 5. Headless opzionale (se vuoi che non si veda)
        # options.add_argument('--headless')
        
        # 6. Configurazioni per evitare rilevamento
        options.add_argument('--disable-features=ChromeWhatsNewUI')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-features=OptimizationGuideModelDownloading')
        options.add_argument('--disable-features=MediaRouter')
        
        # 7. Imposta risoluzione casuale
        larghezza = random.randint(1200, 1920)
        altezza = random.randint(800, 1080)
        options.add_argument(f'--window-size={larghezza},{altezza}')
        
        # 8. Disabilita WebRTC (evita leak IP)
        options.add_argument('--disable-webrtc')
        
        try:
            self.driver = uc.Chrome(options=options, version_main=120)
            
            # ====== INIEZIONE SCRIPTS ======
            # Rimuovi la proprietà webdriver
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    // Rimuovi webdriver
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Fai sembrare Chrome normale
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['it-IT', 'it', 'en-US', 'en']
                    });
                    
                    // Aggiungi window.chrome
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };
                    
                    // Fai sembrare che ci sia WebGL
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) {
                            return 'Intel Inc.';
                        }
                        if (parameter === 37446) {
                            return 'Intel Iris OpenGL Engine';
                        }
                        return getParameter(parameter);
                    };
                '''
            })
            
            print("✅ Browser pronto in modalità stealth")
            return True
            
        except Exception as e:
            print(f"❌ Errore avvio browser: {e}")
            return False
    
    def cerca_offerta(self, keyword, pagina=1):
        """Cerca offerte per una keyword"""
        print(f"🔍 Cerco '{keyword}' - Pagina {pagina}")
        
        try:
            # URL con parametri per evitare cache
            url = f"https://www.amazon.it/s?k={keyword.replace(' ', '+')}&page={pagina}&ref=nb_sb_noss"
            
            self.driver.get(url)
            
            # Aspetta il caricamento
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']")))
            
            # Scroll lento e casuale
            altezza_pagina = self.driver.execute_script("return document.body.scrollHeight")
            for _ in range(random.randint(2, 4)):
                scroll = random.randint(300, 800)
                self.driver.execute_script(f"window.scrollBy(0, {scroll});")
                time.sleep(random.uniform(0.5, 2))
            
            # Parsing
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            prodotti = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            if not prodotti:
                print(f"⚠️ Nessun prodotto trovato per '{keyword}'")
                return []
            
            offerte_pagina = []
            
            for prodotto in prodotti:
                try:
                    # Titolo
                    titolo_elem = prodotto.find('h2', class_='a-size-mini') or prodotto.find('h2')
                    titolo = titolo_elem.text.strip() if titolo_elem else 'Titolo non disponibile'
                    
                    # Prezzo attuale
                    prezzo_elem = prodotto.find('span', class_='a-price')
                    prezzo_attuale = None
                    if prezzo_elem:
                        prezzo_text = prezzo_elem.find('span', class_='a-offscreen')
                        if prezzo_text:
                            try:
                                prezzo_attuale = float(prezzo_text.text.replace('€', '').replace(',', '.').strip())
                            except:
                                pass
                    
                    # Prezzo originale (scontato)
                    prezzo_orig_elem = prodotto.find('span', class_='a-text-price')
                    prezzo_originale = None
                    if prezzo_orig_elem:
                        try:
                            testo = prezzo_orig_elem.text.replace('€', '').replace(',', '.').strip()
                            if testo:
                                prezzo_originale = float(testo)
                        except:
                            pass
                    
                    # Rating
                    rating_elem = prodotto.find('span', class_='a-icon-alt')
                    rating = rating_elem.text.split()[0] if rating_elem else '0'
                    
                    # Link
                    link_elem = prodotto.find('a', class_='a-link-normal')
                    link = 'https://www.amazon.it' + link_elem.get('href') if link_elem else ''
                    
                    # Controlla sconto
                    if prezzo_originale and prezzo_attuale:
                        sconto = ((prezzo_originale - prezzo_attuale) / prezzo_originale) * 100
                        
                        if sconto >= self.sconto_minimo:
                            offerta = {
                                'titolo': titolo[:100],
                                'prezzo_attuale': prezzo_attuale,
                                'prezzo_originale': prezzo_originale,
                                'sconto': round(sconto, 2),
                                'rating': rating,
                                'url': link,
                                'categoria': keyword,
                                'timestamp': datetime.now().isoformat()
                            }
                            offerte_pagina.append(offerta)
                            print(f"🎯 {sconto:.1f}% - {titolo[:40]}...")
                            
                except Exception as e:
                    continue
            
            return offerte_pagina
            
        except Exception as e:
            print(f"❌ Errore ricerca '{keyword}': {e}")
            return []
    
    def esegui_scansione(self):
        """Scansiona tutte le categorie"""
        print("=" * 60)
        print("🛡️ AMAZON OFFERTE BOT - SCANSIONE COMPLETA")
        print("=" * 60)
        
        if not self.avvia_browser():
            return []
        
        tutte_offerte = []
        
        try:
            for categoria in self.categorie:
                print(f"\n📂 CATEGORIA: {categoria.upper()}")
                print("-" * 40)
                
                for pagina in range(1, self.max_pagine + 1):
                    offerte = self.cerca_offerta(categoria, pagina)
                    tutte_offerte.extend(offerte)
                    
                    # Pausa tra le pagine
                    time.sleep(random.uniform(3, 7))
                
                # Pausa tra le categorie
                time.sleep(random.uniform(5, 10))
                
        except KeyboardInterrupt:
            print("\n⏹️ Scansione interrotta dall'utente")
        finally:
            self.driver.quit()
            print("\n🧹 Browser chiuso")
        
        # Salva risultati
        if tutte_offerte:
            with open('offerte.json', 'w', encoding='utf-8') as f:
                json.dump(tutte_offerte, f, ensure_ascii=False, indent=2)
            
            print("\n" + "=" * 60)
            print(f"✅ SCANSIONE COMPLETATA!")
            print(f"📊 Trovate {len(tutte_offerte)} offerte con almeno {self.sconto_minimo}% di sconto")
            print(f"💾 Salvate in offerte.json")
            print("=" * 60)
        else:
            print("\n⚠️ Nessuna offerta trovata. Riprova tra qualche ora.")
        
        return tutte_offerte
    
    def aggiungi_categoria(self, categoria):
        """Aggiungi una categoria personalizzata"""
        if categoria not in self.categorie:
            self.categorie.append(categoria)
            print(f"✅ Aggiunta categoria: {categoria}")
    
    def rimuovi_categoria(self, categoria):
        """Rimuovi una categoria"""
        if categoria in self.categorie:
            self.categorie.remove(categoria)
            print(f"❌ Rimossa categoria: {categoria}")

if __name__ == "__main__":
    bot = AmazonStealthBot()
    
    # Puoi personalizzare qui
    # bot.aggiungi_categoria('smartphone')
    # bot.rimuovi_categoria('libri')
    
    bot.esegui_scansione()
