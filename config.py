import os
from dotenv import load_dotenv

load_dotenv()

# ============ OPZIONE 1: PROXY (per evitare ban) ============
# Compra proxy residenziali da: smartproxy.com, oxylabs.io, or webshare.io
PROXY_HOST = os.getenv('PROXY_HOST', '')
PROXY_PORT = os.getenv('PROXY_PORT', '')
PROXY_USER = os.getenv('PROXY_USER', '')
PROXY_PASS = os.getenv('PROXY_PASS', '')

# ============ OPZIONE 2: API CRAWLORA (la migliore) ============
CRAWLORA_API_KEY = os.getenv('CRAWLORA_API_KEY', '')

# ============ GENERALE ============
SCONTO_MINIMO = 15  # Percentuale minima di sconto
CATEGORIE = ['elettronica', 'informatica', 'casa', 'moda', 'libri']
MAX_PAGINE = 3
