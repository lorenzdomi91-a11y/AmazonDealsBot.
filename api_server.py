from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Permetti alla tua app di chiamare l'API

@app.route('/api/offerte', methods=['GET'])
def get_offerte():
    """Endpoint per la tua app - restituisce tutte le offerte"""
    try:
        with open('offerte.json', 'r', encoding='utf-8') as f:
            offerte = json.load(f)
        
        # Filtri opzionali dalla tua app
        categoria = request.args.get('categoria')
        min_sconto = request.args.get('min_sconto', type=int)
        
        if categoria:
            offerte = [o for o in offerte if o.get('categoria', '').lower() == categoria.lower()]
        
        if min_sconto:
            offerte = [o for o in offerte if o.get('sconto', 0) >= min_sconto]
        
        # Ordina per sconto (più alto prima)
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
            'error': 'Nessuna offerta trovata. Esegui prima lo scraper.'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/offerte/<categoria>', methods=['GET'])
def get_offerte_categoria(categoria):
    """Offerte per categoria specifica"""
    try:
        with open('offerte.json', 'r', encoding='utf-8') as f:
            tutte = json.load(f)
        
        offerte = [o for o in tutte if o.get('categoria', '').lower() == categoria.lower()]
        
        return jsonify({
            'success': True,
            'count': len(offerte),
            'data': offerte,
            'categoria': categoria
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica che il server sia attivo"""
    return jsonify({
        'status': 'online',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
