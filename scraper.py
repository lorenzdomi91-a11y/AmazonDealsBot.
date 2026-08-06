import requests
import json
import time
from datetime import datetime
from config import CRAWLORA_API_KEY, SCONTO_MINIMO, CATEGORIE, MAX_PAGINE

class AmazonOfferBot:
    def __init__(self):
        self.api_key = CRAWLORA_API_KEY
        self.sconto_minimo = SCONTO_MINIMO
        self.offerte = []
        
    def cerca_offerte(self, keyword):
        """Cerca prodotti su Amazon usando Crawlora API"""
        print(f"🔍 Cerco offerte per: {keyword}")
        
        try:
            # Chiamata all'API di Crawlora
            response = requests.get(
                'https://api.crawlora.net/api/v1/amazon/search',
                params={
                    'query': keyword,
                    'page': 1,
                    'country': 'IT'  # Amazon Italia
                },
                headers={'x-api-key': self.api_key},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Errore API: {response.status_code}")
                return []
            
            data = response.json()
            prodotti = data.get('data', {}).get('results', [])
            
            offerte_trovate = []
            for p in prodotti:
                # Estrai i prezzi
                prezzo_attuale = self._estrai_prezzo(p.get('price'))
                prezzo_originale = self._estrai_prezzo(p.get('list_price'))
                
                if prezzo_attuale and prezzo_originale:
                    sconto = ((prezzo_originale - prezzo_attuale) / prezzo_originale) * 100
                    
                    if sconto >= self.sconto_minimo:
                        offerta = {
                            'titolo': p.get('title', ''),
                            'prezzo_attuale': prezzo_attuale,
                            'prezzo_originale': prezzo_originale,
                            'sconto': round(sconto, 2),
                            'rating': p.get('rating', 0),
                            'recensioni': p.get('reviews_count', 0),
                            'url': p.get('url', ''),
                            'immagine': p.get('image_url', ''),
                            'categoria': keyword,
                            'timestamp': datetime.now().isoformat()
                        }
                        offerte_trovate.append(offerta)
                        print(f"✅ Offerta trovata: {offerta['titolo'][:50]}... {offerta['sconto']}%")
            
            return offerte_trovate
            
        except Exception as e:
            print(f"❌ Errore durante la ricerca: {e}")
            return []
    
    def _estrai_prezzo(self, testo):
        """Estrae il numero da una stringa di prezzo"""
        if not testo:
            return None
        try:
            # Rimuovi simboli e converti
            import re
            numeri = re.findall(r'[\d,\.]+', testo.replace('.', '').replace(',', '.'))
            if numeri:
                return float(numeri[0])
        except:
            pass
        return None
    
    def esegui_scan(self):
        """Scansiona tutte le categorie"""
        tutte_offerte = []
        
        for categoria in CATEGORIE:
            print(f"\n📂 Categoria: {categoria}")
            offerte = self.cerca_offerte(categoria)
            tutte_offerte.extend(offerte)
            
            # Pausa per non sovraccaricare l'API
            time.sleep(2)
        
        # Salva su JSON
        with open('offerte.json', 'w', encoding='utf-8') as f:
            json.dump(tutte_offerte, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎯 Trovate {len(tutte_offerte)} offerte con almeno il {self.sconto_minimo}% di sconto!")
        return tutte_offerte

if __name__ == "__main__":
    bot = AmazonOfferBot()
    bot.esegui_scan()
