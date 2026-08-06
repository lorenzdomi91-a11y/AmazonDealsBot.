from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
import subprocess

app = Flask(__name__)
CORS(app)

# ===== ENDPOINT PRINCIPALI =====

@app.route('/api/offerte', methods=['GET'])
def get_offerte():
    """Restituisce tutte le offerte"""
    try:
        with open('offerte.json', 'r', encoding='utf-8') as f:
            offerte = json.load(f)
        
        # Filtri
        categoria = request.args.get('categoria')
        min_sconto = request.args.get('min_sconto', type=int)
        max_prezzo = request.args.get('max_prezzo', type=float)
        
        if categoria:
            offerte = [o for o in offerte if o.get('categoria', '').lower() == categoria.lower()]
        
        if min_sconto:
            offerte = [o for o in offerte if o.get('sconto', 0) >= min_sconto]
        
        if max_prezzo:
            offerte = [o for o in offerte if o.get('prezzo_attuale', 0) <= max_prezzo]
        
        # Ordina per sconto
        offerte.sort(key=lambda x: x.get('sconto', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'count': len(offerte),
            'data': offerte,
            'timestamp': datetime.now().isoformat()
        })
        
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': 'Nessuna offerta. Esegui /api/scan per avviare la ricerca.'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/categorie', methods=['GET'])
def get_categorie():
    """Restituisce tutte le categorie disponibili"""
    try:
        with open('offerte.json', 'r', encoding='utf-8') as f:
            offerte = json.load(f)
        
        categorie = list(set([o.get('categoria', '') for o in offerte]))
        categorie.sort()
        
        return jsonify({
            'success': True,
            'categorie': categorie
        })
        
    except:
        return jsonify({
            'success': False,
            'error': 'Nessuna categoria disponibile'
        }), 404

@app.route('/api/migliori', methods=['GET'])
def get_migliori():
    """Restituisce le 10 migliori offerte"""
    try:
        with open('offerte.json', 'r', encoding='utf-8') as f:
            offerte = json.load(f)
        
        # Ordina per sconto e prendi le prime 10
        offerte.sort(key=lambda x: x.get('sconto', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'count': min(10, len(offerte)),
            'data': offerte[:10],
            'timestamp': datetime.now().isoformat()
        })
        
    except:
        return jsonify({
            'success': False,
            'error': 'Nessuna offerta disponibile'
        }), 404

@app.route('/api/scan', methods=['POST'])
def avvia_scan():
    """Avvia una nuova scansione"""
    try:
        print("🔄 Avvio scansione in background...")
        
        # Avvia lo scraper in un processo separato
        subprocess.Popen(['python', 'bot.py'])
        
        return jsonify({
            'success': True,
            'message': 'Scansione avviata. Controlla tra 5-10 minuti.',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/statistiche', methods=['GET'])
def get_statistiche():
    """Statistiche delle offerte"""
    try:
        with open('offerte.json', 'r', encoding='utf-8') as f:
            offerte = json.load(f)
        
        if not offerte:
            return jsonify({
                'success': True,
                'data': {
                    'totale': 0,
                    'sconto_medio': 0,
                    'sconto_massimo': 0,
                    'prezzo_medio': 0
                }
            })
        
        sconti = [o.get('sconto', 0) for o in offerte]
        prezzi = [o.get('prezzo_attuale', 0) for o in offerte]
        
        return jsonify({
            'success': True,
            'data': {
                'totale': len(offerte),
                'sconto_medio': round(sum(sconti) / len(sconti), 2),
                'sconto_massimo': max(sconti),
                'prezzo_medio': round(sum(prezzi) / len(prezzi), 2),
                'categorie': len(set([o.get('categoria', '') for o in offerte]))
            }
        })
        
    except:
        return jsonify({
            'success': False,
            'error': 'Nessun dato disponibile'
        }), 404

@app.route('/api/refresh', methods=['GET'])
def refresh():
    """Forza il refresh del file"""
    try:
        # Ricarica il file per forzare l'aggiornamento
        with open('offerte.json', 'r', encoding='utf-8') as f:
            offerte = json.load(f)
        
        return jsonify({
            'success': True,
            'message': 'Dati aggiornati',
            'count': len(offerte)
        })
        
    except:
        return jsonify({
            'success': False,
            'error': 'File non trovato'
        }), 404

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 SERVER API AMAZON OFFERTE BOT")
    print("=" * 60)
    print("📡 Endpoint disponibili:")
    print("   GET  /api/offerte       - Tutte le offerte")
    print("   GET  /api/offerte?categoria=elettronica")
    print("   GET  /api/migliori      - Top 10 offerte")
    print("   GET  /api/categorie     - Lista categorie")
    print("   GET  /api/statistiche   - Statistiche")
    print("   POST /api/scan          - Avvia nuova scansione")
    print("=" * 60)
    print("🌐 Server in ascolto su http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
