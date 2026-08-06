#!/bin/bash

echo "========================================="
echo "🛠️ INSTALLAZIONE AMAZON OFFERTE BOT"
echo "========================================="

# 1. Installa Python e pip
echo "📦 Installando Python..."
sudo apt update
sudo apt install -y python3 python3-pip

# 2. Installa Chrome (ESSENZIALE)
echo "🌐 Installando Google Chrome..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt install -y google-chrome-stable

# 3. Installa dipendenze Python
echo "📚 Installando librerie Python..."
pip3 install -r requirements.txt

# 4. Crea file offerte.json vuoto
echo "📄 Creando database offerte..."
echo '[]' > offerte.json

# 5. Rendi eseguibili i file
chmod +x bot.py server.py

echo "========================================="
echo "✅ INSTALLAZIONE COMPLETATA!"
echo "========================================="
echo ""
echo "Per avviare il bot:"
echo "  python3 bot.py"
echo ""
echo "Per avviare il server API:"
echo "  python3 server.py"
echo ""
echo "La tua app può chiamare:"
echo "  http://localhost:5000/api/offerte"
echo "========================================="
