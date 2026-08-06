import requests
import random
import time
from fake_useragent import UserAgent

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.ua = UserAgent()
        self.ultimo_aggiornamento = 0
        
    def ottieni_proxy(self):
        """Restituisce un proxy funzionante"""
        # Aggiorna la lista ogni 5 minuti
        if time.time() - self.ultimo_aggiornamento > 300:
            self.aggiorna_proxy()
        
        if not self.proxies:
            return None
            
        proxy = random.choice(self.proxies)
        return {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
    
    def aggiorna_proxy(self):
        """Scarica proxy gratuiti da vari siti"""
        print("🔄 Aggiorno lista proxy...")
        self.proxies = []
        
        # Fonte 1: Free Proxy List
        try:
            response = requests.get(
                'https://free-proxy-list.net/',
                timeout=10,
                headers={'User-Agent': self.ua.random}
            )
            # Parsing semplice della tabella
            lines = response.text.split('\n')
            for line in lines:
                if ':' in line and 'yes' in line.lower():
                    parts = line.strip().split(':')
                    if len(parts) >= 2:
                        ip = parts[0].strip()
                        if ip.replace('.', '').isdigit():
                            porta = parts[1].split()[0].strip()
                            self.proxies.append(f'{ip}:{porta}')
        except:
            pass
        
        # Fonte 2: Proxy List Download
        try:
            response = requests.get(
                'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all',
                timeout=10
            )
            for proxy in response.text.strip().split('\n'):
                if proxy:
                    self.proxies.append(proxy.strip())
        except:
            pass
        
        # Fonte 3: PubProxy
        try:
            response = requests.get(
                'https://pubproxy.com/api/proxy?limit=20&format=txt&http=true&https=true',
                timeout=10
            )
            for proxy in response.text.strip().split('\n'):
                if proxy:
                    self.proxies.append(proxy.strip())
        except:
            pass
        
        # Rimuovi duplicati
        self.proxies = list(set(self.proxies))
        
        # Filtra proxy validi
        self.proxies = [p for p in self.proxies if ':' in p]
        
        self.ultimo_aggiornamento = time.time()
        print(f"✅ Trovati {len(self.proxies)} proxy gratuiti")
    
    def testa_proxy(self, proxy):
        """Verifica se un proxy funziona"""
        try:
            test = requests.get(
                'http://httpbin.org/ip',
                proxies={'http': f'http://{proxy}', 'https': f'http://{proxy}'},
                timeout=5
            )
            return test.status_code == 200
        except:
            return False

# Singleton
proxy_manager = ProxyManager()
