const { chromium } = require('playwright');
const fs = require('fs');

class RealEstateScraper {
    constructor() {
        this.resultsBelgrade = [];
        this.resultsSerbia = [];
        this.outputFileBelgrade = '/home/dju/moji projekti/Web SCreper/rezultati_beograd.txt';
        this.outputFileSerbia = '/home/dju/moji projekti/Web SCreper/rezultati_srbija.txt';
    }

    saveResultsBelgrade() {
        let content = `REZULTATI ZA BEOGRAD I OKOLINU\n`;
        content += `Datum: ${new Date().toLocaleString()}\n`;
        content += `Kriterijumi: Kuće i seoska domaćinstva, 15.000 - 20.000 EUR, Beograd i okolina\n`;
        content += `${'='.repeat(80)}\n\n`;

        if (this.resultsBelgrade.length === 0) {
            content += 'Nema pronađenih oglasa u zadatom kriterijumu.\n\n';
            content += 'Direktni linkovi za pretragu KUĆA:\n';
            content += '• https://www.nekretnine.rs/stambeni-objekti/kuce/beograd/cena/15000_20000/\n';
            content += '• https://www.olx.rs/d/nedviznosti/prodazha/kukhi/beograd/\n';
            content += '• https://www.kupujemprodajem.com/nekretnine/kuce/beograd/\n\n';
            content += 'Direktni linkovi za pretragu SEOSKIH DOMAĆINSTAVA:\n';
            content += '• https://www.nekretnine.rs/stambeni-objekti/seoska-domacinstva/beograd/cena/15000_20000/\n';
            content += '• https://www.olx.rs/d/nedviznosti/prodazha/seosko-domacinstvo/beograd/\n';
            content += '• https://www.kupujemprodajem.com/nekretnine/seoska-domacinstva/beograd/\n';
        } else {
            content += `UKUPNO PRONAĐENO: ${this.resultsBelgrade.length} oglasa\n\n`;
            this.resultsBelgrade.forEach((ad, index) => {
                content += `${index + 1}. ${ad.title}\n`;
                content += `   Cena: ${ad.price}\n`;
                content += `   Lokacija: ${ad.location}\n`;
                content += `   Tip: ${ad.type || 'N/A'}\n`;
                content += `   Link: ${ad.link}\n`;
                content += `   Izvor: ${ad.source}\n`;
                content += `${'-'.repeat(80)}\n\n`;
            });
        }

        content += `\n${'='.repeat(80)}\n`;
        content += 'NAPOMENA: Ovo su rezultati automatske pretrage.\n';
        content += 'Preporučuje se ručna provera svakog oglasa.\n';
        content += `${'='.repeat(80)}\n`;

        fs.writeFileSync(this.outputFileBelgrade, content, 'utf8');
        console.log(`\n✓ Rezultati za Beograd sačuvani u: ${this.outputFileBelgrade}`);
    }

    saveResultsSerbia() {
        let content = `REZULTATI ZA ČITAVU SRBIJU\n`;
        content += `Datum: ${new Date().toLocaleString()}\n`;
        content += `Kriterijumi: Kuće i seoska domaćinstva, 15.000 - 20.000 EUR, Srbija\n`;
        content += `${'='.repeat(80)}\n\n`;

        if (this.resultsSerbia.length === 0) {
            content += 'Nema pronađenih oglasa u zadatom kriterijumu.\n\n';
            content += 'Direktni linkovi za pretragu KUĆA:\n';
            content += '• https://www.nekretnine.rs/stambeni-objekti/kuce/srbija/cena/15000_20000/\n';
            content += '• https://www.olx.rs/d/nedviznosti/prodazha/kukhi/\n';
            content += '• https://www.kupujemprodajem.com/nekretnine/kuce/\n\n';
            content += 'Direktni linkovi za pretragu SEOSKIH DOMAĆINSTAVA:\n';
            content += '• https://www.nekretnine.rs/stambeni-objekti/seoska-domacinstva/srbija/cena/15000_20000/\n';
            content += '• https://www.olx.rs/d/nedviznosti/prodazha/seosko-domacinstvo/\n';
            content += '• https://www.kupujemprodajem.com/nekretnine/seoska-domacinstva/\n';
        } else {
            content += `UKUPNO PRONAĐENO: ${this.resultsSerbia.length} oglasa\n\n`;
            this.resultsSerbia.forEach((ad, index) => {
                content += `${index + 1}. ${ad.title}\n`;
                content += `   Cena: ${ad.price}\n`;
                content += `   Lokacija: ${ad.location}\n`;
                content += `   Tip: ${ad.type || 'N/A'}\n`;
                content += `   Link: ${ad.link}\n`;
                content += `   Izvor: ${ad.source}\n`;
                content += `${'-'.repeat(80)}\n\n`;
            });
        }

        content += `\n${'='.repeat(80)}\n`;
        content += 'NAPOMENA: Ovo su rezultati automatske pretrage.\n';
        content += 'Preporučuje se ručna provera svakog oglasa.\n';
        content += `${'='.repeat(80)}\n`;

        fs.writeFileSync(this.outputFileSerbia, content, 'utf8');
        console.log(`\n✓ Rezultati za Srbiju sačuvani u: ${this.outputFileSerbia}`);
    }

    extractPrice(priceText) {
        if (!priceText) return null;
        const match = priceText.match(/(\d[\d.,\s]*)/);
        if (match) {
            const priceNum = parseInt(match[1].replace(/[^\d]/g, ''));
            if (priceNum >= 15000 && priceNum <= 20000) {
                return priceNum;
            }
        }
        return null;
    }

    async extractAdsFromPage(page, selector, source) {
        return await page.$$eval(selector, (items, src) => {
            return items.map(item => {
                const titleEl = item.querySelector('h2, h3, h6, .offer-title, .property-title, .adTitle, [data-testid="ad-title"], .title, a');
                const priceEl = item.querySelector('.offer-price, .property-price, .adPrice, [data-testid="ad-price"], .price');
                const locationEl = item.querySelector('.offer-location, .property-location, .adLocation, [data-testid="location-date"], [data-testid="ad-location"], .location');
                const linkEl = item.querySelector('a');

                return {
                    title: titleEl ? titleEl.innerText.trim() : 'Nema naslova',
                    price: priceEl ? priceEl.innerText.trim() : 'N/A',
                    location: locationEl ? locationEl.innerText.trim() : 'N/A',
                    link: linkEl ? linkEl.href : 'N/A',
                    source: src
                };
            });
        }, source);
    }

    // === BEOGRAD PRETRAGE ===

    async searchNekretnineRsBelgrade(page) {
        console.log('\n📍 [BEOGRAD] Pretražujem nekretnine.rs - KUĆE...');
        try {
            await page.goto('https://www.nekretnine.rs/stambeni-objekti/kuce/beograd/cena/15000_20000/', {
                waitUntil: 'networkidle',
                timeout: 30000
            });
            await page.waitForTimeout(3000);

            const ads = await this.extractAdsFromPage(page, '.offer-item, .property-item, [data-testid="listing-item"]', 'nekretnine.rs');

            ads.forEach(ad => {
                const priceNum = this.extractPrice(ad.price);
                if (priceNum) {
                    this.resultsBelgrade.push({ ...ad, type: 'Kuća' });
                    console.log(`  ✓ Pronađena kuća: ${ad.title.substring(0, 50)}... (${ad.price})`);
                }
            });
        } catch (error) {
            console.log(`  ⚠ Greška: ${error.message}`);
        }
    }

    async searchNekretnineRsBelgradeDomacinstva(page) {
        console.log('\n📍 [BEOGRAD] Pretražujem nekretnine.rs - SEOSKA DOMAĆINSTVA...');
        try {
            await page.goto('https://www.nekretnine.rs/stambeni-objekti/seoska-domacinstva/beograd/cena/15000_20000/', {
                waitUntil: 'networkidle',
                timeout: 30000
            });
            await page.waitForTimeout(3000);

            const ads = await this.extractAdsFromPage(page, '.offer-item, .property-item, [data-testid="listing-item"]', 'nekretnine.rs');

            ads.forEach(ad => {
                const priceNum = this.extractPrice(ad.price);
                if (priceNum) {
                    this.resultsBelgrade.push({ ...ad, type: 'Seosko domaćinstvo' });
                    console.log(`  ✓ Pronađeno domaćinstvo: ${ad.title.substring(0, 50)}... (${ad.price})`);
                }
            });
        } catch (error) {
            console.log(`  ⚠ Greška: ${error.message}`);
        }
    }

    async searchOlxRsBelgrade(page) {
        console.log('\n📍 [BEOGRAD] Pretražujem OLX.rs - KUĆE...');
        try {
            await page.goto('https://www.olx.rs/d/nedviznosti/prodazha/kukhi/beograd/', {
                waitUntil: 'domcontentloaded',
                timeout: 30000
            });
            await page.waitForTimeout(3000);

            const ads = await this.extractAdsFromPage(page, '[data-cy="l-card"], .css-qfzx1y, [data-testid="listing-ad"]', 'olx.rs');

            ads.forEach(ad => {
                const priceNum = this.extractPrice(ad.price);
                if (priceNum) {
                    this.resultsBelgrade.push({ ...ad, type: 'Kuća' });
                    console.log(`  ✓ Pronađena kuća: ${ad.title.substring(0, 50)}... (${ad.price})`);
                }
            });
        } catch (error) {
            console.log(`  ⚠ Greška: ${error.message}`);
        }
    }

    async searchOlxRsBelgradeDomacinstva(page) {
        console.log('\n📍 [BEOGRAD] Pretražujem OLX.rs - SEOSKA DOMAĆINSTVA...');
        try {
            await page.goto('https://www.olx.rs/d/nedviznosti/prodazha/seosko-domacinstvo/beograd/', {
                waitUntil: 'domcontentloaded',
                timeout: 30000
            });
            await page.waitForTimeout(3000);

            const ads = await this.extractAdsFromPage(page, '[data-cy="l-card"], .css-qfzx1y, [data-testid="listing-ad"]', 'olx.rs');

            ads.forEach(ad => {
                const priceNum = this.extractPrice(ad.price);
                if (priceNum) {
                    this.resultsBelgrade.push({ ...ad, type: 'Seosko domaćinstvo' });
                    console.log(`  ✓ Pronađeno domaćinstvo: ${ad.title.substring(0, 50)}... (${ad.price})`);
                }
            });
        } catch (error) {
            console.log(`  ⚠ Greška: ${error.message}`);
        }
    }

    async searchKupujemProdajemBelgrade(page) {
        console.log('\n📍 [BEOGRAD] Pretražujem KupujemProdajem.com - KUĆE...');
        try {
            await page.goto('https://www.kupujemprodajem.com/nekretnine/kuce/beograd/cena/15000/20000', {
                waitUntil: 'networkidle',
                timeout: 30000
            });
            await page.waitForTimeout(3000);

            const ads = await this.extractAdsFromPage(page, '.adItem, [data-testid="ad-list-item"], .AdItem', 'kupujemprodajem.com');

            ads.forEach(ad => {
                const priceNum = this.extractPrice(ad.price);
                if (priceNum) {
                    this.resultsBelgrade.push({ ...ad, type: 'Kuća' });
                    console.log(`  ✓ Pronađena kuća: ${ad.title.substring(0, 50)}... (${ad.price})`);
                }
            });
        } catch (error) {
            console.log(`  ⚠ Greška: ${error.message}`);
        }
    }

    async searchKupujemProdajemBelgradeDomacinstva(page) {
        console.log('\n📍 [BEOGRAD] Pretražujem KupujemProdajem.com - SEOSKA DOMAĆINSTVA...');
        try {
            await page.goto('https://www.kupujemprodajem.com/nekretnine/seoska-domacinstva/beograd/cena/15000/20000', {
                waitUntil: 'networkidle',
                timeout: 30000
            });
            await page.waitForTimeout(3000);

            const ads = await this.extractAdsFromPage(page, '.adItem, [data-testid="ad-list-item"], .AdItem', 'kupujemprodajem.com');

            ads.forEach(ad => {
                const priceNum = this.extractPrice(ad.price);
                if (priceNum) {
                    this.resultsBelgrade.push({ ...ad, type: 'Seosko domaćinstvo' });
                    console.log(`  ✓ Pronađeno domaćinstvo: ${ad.title.substring(0, 50)}... (${ad.price})`);
                }
            });
        } catch (error) {
            console.log(`  ⚠ Greška: ${error.message}`);
        }
    }

    // === SRBIJA PRETRAGE ===

    async searchNekretnineRsSerbia(page) {
        console.log('\n📍 [SRBIJA] Pretražujem nekretnine.rs - KUĆE...');
        try {
            await page.goto('https://www.nekretnine.rs/stambeni-objekti/kuce/srbija/cena/15000_20000/', {
                waitUntil: 'networkidle',
                timeout: 30000
            });
            await page.waitForTimeout(3000);

            const ads = await this.extractAdsFromPage(page, '.offer-item, .property-item, [data-testid="listing-item"]', 'nekretnine.rs');

            ads.forEach(ad => {
                const priceNum = this.extractPrice(ad.price);
                if (priceNum) {
                    this.resultsSerbia.push({ ...ad, type: 'Kuća' });
                    console.log(`  ✓ Pronađena kuća: ${ad.title.substring(0, 50)}... (${ad.price})`);
                }
            });
        } catch (error) {
            console.log(`  ⚠ Greška: ${error.message}`);
        }
    }

    async searchNekretnineRsSerbiaDomacinstva(page) {
        console.log('\n📍 [SRBIJA] Pretražujem nekretnine.rs - SEOSKA DOMAĆINSTVA...');
        try {
            await page.goto('https://www.nekretnine.rs/stambeni-objekti/seoska-domacinstva/srbija/cena/15000_20000/', {
                waitUntil: 'networkidle',
                timeout: 30000
            });
            await page.waitForTimeout(3000);

            const ads = await this.extractAdsFromPage(page, '.offer-item, .property-item, [data-testid="listing-item"]', 'nekretnine.rs');

            ads.forEach(ad => {
                const priceNum = this.extractPrice(ad.price);
                if (priceNum) {
                    this.resultsSerbia.push({ ...ad, type: 'Seosko domaćinstvo' });
                    console.log(`  ✓ Pronađeno domaćinstvo: ${ad.title.substring(0, 50)}... (${ad.price})`);
                }
            });
        } catch (error) {
            console.log(`  ⚠ Greška: ${error.message}`);
        }
    }

    async searchOlxRsSerbia(page) {
        console.log('\n📍 [SRBIJA] Pretražujem OLX.rs - KUĆE...');
        try {
            await page.goto('https://www.olx.rs/d/nedviznosti/prodazha/kukhi/', {
                waitUntil: 'domcontentloaded',
                timeout: 30000
            });
            await page.waitForTimeout(3000);

            const ads = await this.extractAdsFromPage(page, '[data-cy="l-card"], .css-qfzx1y, [data-testid="listing-ad"]', 'olx.rs');

            ads.forEach(ad => {
                const priceNum = this.extractPrice(ad.price);
                if (priceNum) {
                    this.resultsSerbia.push({ ...ad, type: 'Kuća' });
                    console.log(`  ✓ Pronađena kuća: ${ad.title.substring(0, 50)}... (${ad.price})`);
                }
            });
        } catch (error) {
            console.log(`  ⚠ Greška: ${error.message}`);
        }
    }

    async searchOlxRsSerbiaDomacinstva(page) {
        console.log('\n📍 [SRBIJA] Pretražujem OLX.rs - SEOSKA DOMAĆINSTVA...');
        try {
            await page.goto('https://www.olx.rs/d/nedviznosti/prodazha/seosko-domacinstvo/', {
                waitUntil: 'domcontentloaded',
                timeout: 30000
            });
            await page.waitForTimeout(3000);

            const ads = await this.extractAdsFromPage(page, '[data-cy="l-card"], .css-qfzx1y, [data-testid="listing-ad"]', 'olx.rs');

            ads.forEach(ad => {
                const priceNum = this.extractPrice(ad.price);
                if (priceNum) {
                    this.resultsSerbia.push({ ...ad, type: 'Seosko domaćinstvo' });
                    console.log(`  ✓ Pronađeno domaćinstvo: ${ad.title.substring(0, 50)}... (${ad.price})`);
                }
            });
        } catch (error) {
            console.log(`  ⚠ Greška: ${error.message}`);
        }
    }

    async searchKupujemProdajemSerbia(page) {
        console.log('\n📍 [SRBIJA] Pretražujem KupujemProdajem.com - KUĆE...');
        try {
            await page.goto('https://www.kupujemprodajem.com/nekretnine/kuce/cena/15000/20000', {
                waitUntil: 'networkidle',
                timeout: 30000
            });
            await page.waitForTimeout(3000);

            const ads = await this.extractAdsFromPage(page, '.adItem, [data-testid="ad-list-item"], .AdItem', 'kupujemprodajem.com');

            ads.forEach(ad => {
                const priceNum = this.extractPrice(ad.price);
                if (priceNum) {
                    this.resultsSerbia.push({ ...ad, type: 'Kuća' });
                    console.log(`  ✓ Pronađena kuća: ${ad.title.substring(0, 50)}... (${ad.price})`);
                }
            });
        } catch (error) {
            console.log(`  ⚠ Greška: ${error.message}`);
        }
    }

    async searchKupujemProdajemSerbiaDomacinstva(page) {
        console.log('\n📍 [SRBIJA] Pretražujem KupujemProdajem.com - SEOSKA DOMAĆINSTVA...');
        try {
            await page.goto('https://www.kupujemprodajem.com/nekretnine/seoska-domacinstva/cena/15000/20000', {
                waitUntil: 'networkidle',
                timeout: 30000
            });
            await page.waitForTimeout(3000);

            const ads = await this.extractAdsFromPage(page, '.adItem, [data-testid="ad-list-item"], .AdItem', 'kupujemprodajem.com');

            ads.forEach(ad => {
                const priceNum = this.extractPrice(ad.price);
                if (priceNum) {
                    this.resultsSerbia.push({ ...ad, type: 'Seosko domaćinstvo' });
                    console.log(`  ✓ Pronađeno domaćinstvo: ${ad.title.substring(0, 50)}... (${ad.price})`);
                }
            });
        } catch (error) {
            console.log(`  ⚠ Greška: ${error.message}`);
        }
    }

    async run() {
        console.log('\n' + '='.repeat(80));
        console.log('WEB SCRAPER - Kuće i seoska domaćinstva');
        console.log('Cilj: 15.000 - 20.000 EUR');
        console.log('='.repeat(80));

        const browser = await chromium.launch({ headless: true });
        const context = await browser.newContext({
            userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        });
        const page = await context.newPage();

        // === BEOGRAD PRETRAGA ===
        console.log('\n\n' + '🏠'.repeat(20));
        console.log('PRETRAGA ZA BEOGRAD I OKOLINU');
        console.log('🏠'.repeat(20) + '\n');
        
        await this.searchNekretnineRsBelgrade(page);
        await this.searchNekretnineRsBelgradeDomacinstva(page);
        await this.searchOlxRsBelgrade(page);
        await this.searchOlxRsBelgradeDomacinstva(page);
        await this.searchKupujemProdajemBelgrade(page);
        await this.searchKupujemProdajemBelgradeDomacinstva(page);

        // === SRBIJA PRETRAGA ===
        console.log('\n\n' + '🇷🇸'.repeat(20));
        console.log('PRETRAGA ZA ČITAVU SRBIJU');
        console.log('🇷🇸'.repeat(20) + '\n');
        
        await this.searchNekretnineRsSerbia(page);
        await this.searchNekretnineRsSerbiaDomacinstva(page);
        await this.searchOlxRsSerbia(page);
        await this.searchOlxRsSerbiaDomacinstva(page);
        await this.searchKupujemProdajemSerbia(page);
        await this.searchKupujemProdajemSerbiaDomacinstva(page);

        await browser.close();

        // Čuva rezultate
        this.saveResultsBelgrade();
        this.saveResultsSerbia();

        // Finalni rezime
        console.log('\n\n' + '='.repeat(80));
        console.log('PRETRAGA ZAVRŠENA!');
        console.log('='.repeat(80));
        console.log(`\n📊 REZULTATI:`);
        console.log(`   • Beograd i okolina: ${this.resultsBelgrade.length} oglasa`);
        console.log(`     → Fajl: ${this.outputFileBelgrade}`);
        console.log(`   • Srbija (cela): ${this.resultsSerbia.length} oglasa`);
        console.log(`     → Fajl: ${this.outputFileSerbia}`);
        console.log(`\n📝 UKUPNO: ${this.resultsBelgrade.length + this.resultsSerbia.length} oglasa`);
        console.log(`\n🔍 Pretražene kategorije:`);
        console.log(`   • Kuće`);
        console.log(`   • Seoska domaćinstva`);
        console.log('='.repeat(80) + '\n');
    }
}

// Pokreće scraper
const scraper = new RealEstateScraper();
scraper.run().catch(error => {
    console.error('Greška:', error);
    process.exit(1);
});
