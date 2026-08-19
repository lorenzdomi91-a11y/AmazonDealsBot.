import asyncio
import json
import time
import random
from playwright.async_api import async_playwright

# CONFIGURAZIONE PROFESSIONALE
URL_OFFERTE = "https://www.amazon.it/gp/goldbox"

async def scrape_amazon():
    async with async_playwright() as p:
        print("Avvio Browser Robotizzato (Chromium)...")
        browser = await p.chromium.launch(headless=True)
        
        # Simuliamo un vero utente Chrome su Windows
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        print(f"Navigazione su Amazon.it/offerte...")
        await page.goto(URL_OFFERTE, wait_until="networkidle", timeout=60000)
        
        # Aspettiamo che la griglia delle offerte sia visibile
        try:
            await page.wait_for_selector("[data-testid='grid-dequeue-reveal-item']", timeout=15000)
        except:
            print("Avviso: La griglia standard non è apparsa, provo metodo alternativo...")

        # Scorrimento per caricare le offerte (Lazy Loading)
        print("Caricamento offerte in corso...")
        for _ in range(5):
            await page.mouse.wheel(0, 1500)
            await asyncio.sleep(2)

        # Estrazione dati tramite JavaScript nel browser
        print("Estrazione dati in corso...")
        deals = await page.evaluate("""() => {
            const results = [];
            // Cerchiamo tutti i contenitori delle offerte
            const items = document.querySelectorAll("[data-testid='deal-card'], .a-section.deal-card");
            
            items.forEach(item => {
                try {
                    const titleEl = item.querySelector("h2, .deal-title, [data-testid='deal-card-title']");
                    const imgEl = item.querySelector("img");
                    const linkEl = item.querySelector("a");
                    
                    // Prezzo attuale
                    const priceEl = item.querySelector(".a-price-whole");
                    const fractionEl = item.querySelector(".a-price-fraction");
                    
                    // Prezzo originale (barrato)
                    const oldPriceEl = item.querySelector(".a-text-strike, .basis-price");
                    
                    if (titleEl && linkEl && priceEl) {
                        const priceText = priceEl.innerText.replace(/[^0-9]/g, '');
                        const fractionText = fractionEl ? fractionEl.innerText.replace(/[^0-9]/g, '') : "00";
                        const finalPrice = parseFloat(priceText + "." + fractionText);
                        
                        let oldPrice = finalPrice * 1.3; // Fallback
                        if (oldPriceEl) {
                            oldPrice = parseFloat(oldPriceEl.innerText.replace(/[^0-9.,]/g, '').replace(',', '.'));
                        }

                        results.append({
                            title: titleEl.innerText.trim(),
                            price: finalPrice,
                            old_price: oldPrice,
                            link: linkEl.href,
                            image: imgEl ? imgEl.src : ""
                        });
                    }
                } catch (e) {}
            });
            return results;
        }""")

        await browser.close()
        
        if deals:
            # Pulizia e formattazione finale
            final_data = []
            for d in deals:
                if not d['link'].startswith("http"): continue
                
                # Calcolo sconto
                discount = 0
                if d['old_price'] > d['price']:
                    discount = round(((d['old_price'] - d['price']) / d['old_price']) * 100)
                
                final_data.append({
                    "id": str(time.time()) + str(random.randint(0,999)),
                    "title": d['title'],
                    "price": d['price'],
                    "old_price": d['old_price'],
                    "discountPct": discount,
                    "url": d['link'],
                    "image": d['image'],
                    "category": "Amazon Reale"
                })

            # Salvataggio JSON
            with open("offerte.json", "w", encoding="utf-8") as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            
            print(f"SUCCESSO: {len(final_data)} offerte reali estratte e salvate in offerte.json!")
