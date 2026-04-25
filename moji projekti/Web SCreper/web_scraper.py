#!/usr/bin/env python3
"""
Web Scraper za seoska imanja u okolini Beograda
Cilj: Pronalazak oglasa od 15.000 - 20.000 eura
"""

import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright
from urllib.parse import urljoin, quote

class RealEstateScraper:
    def __init__(self):
        self.results = []
        self.output_file = "/home/dju/moji projekti/Web SCreper/rezultati_oglasi.txt"
        
    def save_results(self):
        """Čuva rezultate u tekstualni fajl"""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(f"Rezultati pretrage seoskih imanja\n")
            f.write(f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Kriterijumi: 15.000 - 20.000 EUR, okolina Beograda\n")
            f.write("=" * 80 + "\n\n")
            
            if not self.results:
                f.write("Nema pronađenih oglasa.\n")
            else:
                for idx, ad in enumerate(self.results, 1):
                    f.write(f"{idx}. {ad.get('title', 'Nema naslova')}\n")
                    f.write(f"   Cena: {ad.get('price', 'N/A')}\n")
                    f.write(f"   Lokacija: {ad.get('location', 'N/A')}\n")
                    f.write(f"   Opis: {ad.get('description', 'N/A')}\n")
                    f.write(f"   Link: {ad.get('link', 'N/A')}\n")
                    f.write("-" * 80 + "\n\n")
                    
        print(f"Rezultati sačuvani u: {self.output_file}")
        
    def is_price_in_range(self, price_text):
        """Proverava da li je cena u rasponu 15.000 - 20.000 EUR"""
        if not price_text:
            return False
            
        # Uklanja razmake i ekstrahuje brojeve
        numbers = re.findall(r'\d+', price_text.replace('.', '').replace(',', ''))
        if numbers:
            try:
                price = int(numbers[0])
                # Proverava da li je cena između 15.000 i 20.000
                return 15000 <= price <= 20000
            except ValueError:
                pass
        return False
        
    def is_near_belgrade(self, location):
        """Proverava da li je lokacija u okolini Beograda"""
        if not location:
            return False
            
        location_lower = location.lower()
        belgrade_keywords = [
            'beograd', 'bg', 'beo', 'grad', 'novi beograd', 'zemun', 'rakovica',
            'voždovac', 'voždovač', 'čukarica', 'čukarič', 'palilula', 'zvezdara',
            'grocka', 'barajevo', 'lazarevac', 'mladenovac', 'obrenovac', 'sopot',
            'surčin', 'surcin', 'zemun', 'zemunsk',
            'batajnica', 'borča', 'borca', 'kotež', 'kotez', 'umka', 'rušanj', 'rusanj',
            'ripanj', 'jajinci', 'mirijevo', 'kotež', 'leštane', 'lestane',
            'kaluđerica', 'kaluderica', 'vinča', 'vinca', 'padinska skela'
        ]
        
        return any(keyword in location_lower for keyword in belgrade_keywords)

    async def search_nekretnine_rs(self, page):
        """Pretražuje nekretnine.rs"""
        print("Pretražujem nekretnine.rs...")
        try:
            # URL za pretragu zemljišta kuća u Beogradu
            url = "https://www.nekretnine.rs/stambeni-objekti/kuce/beograd/cena/15000_20000/"
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Čeka da se oglasi učitaju
            await page.wait_for_selector('.offer-title, .property-title, h2', timeout=10000)
            
            # Prikupi oglase
            ads = await page.query_selector_all('.offer-item, .property-item, .oglas, article')
            
            for ad in ads:
                try:
                    title_elem = await ad.query_selector('h2, .offer-title, .property-title, a')
                    price_elem = await ad.query_selector('.offer-price, .property-price, .price')
                    location_elem = await ad.query_selector('.offer-location, .property-location, .location')
                    desc_elem = await ad.query_selector('.offer-description, .property-description, .description')
                    link_elem = await ad.query_selector('a')
                    
                    title = await title_elem.inner_text() if title_elem else "Nema naslova"
                    price = await price_elem.inner_text() if price_elem else "N/A"
                    location = await location_elem.inner_text() if location_elem else "N/A"
                    description = await desc_elem.inner_text() if desc_elem else "N/A"
                    link = await link_elem.get_attribute('href') if link_elem else "N/A"
                    
                    if link and link.startswith('/'):
                        link = urljoin("https://www.nekretnine.rs", link)
                    
                    # Proverava kriterijume
                    if self.is_price_in_range(price) and self.is_near_belgrade(location):
                        self.results.append({
                            'title': title.strip(),
                            'price': price.strip(),
                            'location': location.strip(),
                            'description': description.strip()[:200] + "..." if len(description) > 200 else description.strip(),
                            'link': link,
                            'source': 'nekretnine.rs'
                        })
                        print(f"✓ Pronađen oglas: {title[:50]}...")
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Greška pri pretrazi nekretnine.rs: {e}")

    async def search_olx_rs(self, page):
        """Pretražuje OLX.rs"""
        print("Pretražujem OLX.rs...")
        try:
            # URL za pretragu zemljišta kuća u Beogradu
            url = "https://www.olx.rs/d/nedviznosti/prodazha/kukhi/beograd/q-ku%C4%87a/"
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Čeka da se oglasi učitaju
            await page.wait_for_selector('.css-qfzx1y, [data-testid="listing-ad"]', timeout=10000)
            
            # Prikupi oglase
            ads = await page.query_selector_all('.css-qfzx1y, [data-testid="listing-ad"]')
            
            for ad in ads:
                try:
                    title_elem = await ad.query_selector('h6, .css-16v5mdi, [data-testid="ad-title"]')
                    price_elem = await ad.query_selector('.css-10b0gli, [data-testid="ad-price"]')
                    location_elem = await ad.query_selector('.css-ve6ph5, [data-testid="location-date"]')
                    link_elem = await ad.query_selector('a')
                    
                    title = await title_elem.inner_text() if title_elem else "Nema naslova"
                    price = await price_elem.inner_text() if price_elem else "N/A"
                    location = await location_elem.inner_text() if location_elem else "N/A"
                    link = await link_elem.get_attribute('href') if link_elem else "N/A"
                    
                    if link and link.startswith('/'):
                        link = urljoin("https://www.olx.rs", link)
                    
                    # Proverava kriterijume
                    if self.is_price_in_range(price) and self.is_near_belgrade(location):
                        self.results.append({
                            'title': title.strip(),
                            'price': price.strip(),
                            'location': location.strip(),
                            'description': "Pogledajte detalje na linku",
                            'link': link,
                            'source': 'olx.rs'
                        })
                        print(f"✓ Pronađen oglas: {title[:50]}...")
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Greška pri pretrazi OLX.rs: {e}")

    async def search_halooglasi(self, page):
        """Pretražuje Halooglasi"""
        print("Pretražujem Halooglasi...")
        try:
            # URL za pretragu kuća u Beogradu
            url = "https://www.halooglasi.com/nedviznosti/prodaja-kukha/beograd"
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Čeka da se oglasi učitaju
            await page.wait_for_selector('.product-item, .listing-item', timeout=10000)
            
            # Prikupi oglase
            ads = await page.query_selector_all('.product-item, .listing-item')
            
            for ad in ads:
                try:
                    title_elem = await ad.query_selector('.product-title, h3, a')
                    price_elem = await ad.query_selector('.product-price, .price')
                    location_elem = await ad.query_selector('.product-location, .location')
                    link_elem = await ad.query_selector('a')
                    
                    title = await title_elem.inner_text() if title_elem else "Nema naslova"
                    price = await price_elem.inner_text() if price_elem else "N/A"
                    location = await location_elem.inner_text() if location_elem else "N/A"
                    link = await link_elem.get_attribute('href') if link_elem else "N/A"
                    
                    if link and link.startswith('/'):
                        link = urljoin("https://www.halooglasi.com", link)
                    
                    # Proverava kriterijume
                    if self.is_price_in_range(price) and self.is_near_belgrade(location):
                        self.results.append({
                            'title': title.strip(),
                            'price': price.strip(),
                            'location': location.strip(),
                            'description': "Pogledajte detalje na linku",
                            'link': link,
                            'source': 'halooglasi'
                        })
                        print(f"✓ Pronađen oglas: {title[:50]}...")
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Greška pri pretrazi Halooglasi: {e}")

    async def run(self):
        """Pokreće scraper na svim sajtovima"""
        print("\n" + "=" * 80)
        print("POKRETANJE WEB SCRAPER-A ZA SEOSKA IMANJA")
        print("=" * 80 + "\n")
        
        async with async_playwright() as p:
            # Pokreće browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Pretražuje sve sajtove
            await self.search_nekretnine_rs(page)
            await self.search_olx_rs(page)
            await self.search_halooglasi(page)
            
            # Zatvara browser
            await browser.close()
        
        # Čuva rezultate
        self.save_results()
        
        # Prikazuje rezime
        print("\n" + "=" * 80)
        print(f"PRETRAGA ZAVRŠENA!")
        print(f"Ukupno pronađenih oglasa: {len(self.results)}")
        print(f"Rezultati sačuvani u: {self.output_file}")
        print("=" * 80 + "\n")

if __name__ == "__main__":
    scraper = RealEstateScraper()
    asyncio.run(scraper.run())
