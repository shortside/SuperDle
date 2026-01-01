#!/usr/bin/env python3
"""
🇳🇱 Dutch Supermarket Scraper
Scrapes products from Dutch supermarkets using Playwright

Install:
    pip install playwright beautifulsoup4
    playwright install chromium

Usage:
    python scraper.py
    python scraper.py --visible (to see the browser)
"""

import json
import time
import random
import argparse
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PlaywrightTimeout
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    print("⚠️  Run: pip install playwright && playwright install chromium")

OUTPUT_FILE = "games.json"

CATEGORIES = [
    "melk", "kaas", "yoghurt", "boter", "eieren",
    "kip", "gehakt", "worst", "ham",
    "brood", "croissant",
    "cola", "sap", "water", "bier", "wijn", "koffie", "thee",
    "chips", "chocolade", "koekjes", "snoep", "noten",
    "pasta", "rijst",
    "tomaat", "appel", "banaan", "aardappel",
    "ketchup", "mayonaise",
    "cornflakes", "hagelslag", "pindakaas",
    "pizza", "ijs", "friet",
]


class Product:
    def __init__(self, name: str, price: float, image: str, store: str):
        self.name = name
        self.price = price
        self.image = image
        self.store = store


class DutchScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.products: List[Product] = []
        self.seen: set = set()
        
    def _delay(self, min_s=1, max_s=3):
        time.sleep(random.uniform(min_s, max_s))
        
    def _parse_price(self, text: str) -> Optional[float]:
        if not text:
            return None
        text = text.replace('€', '').replace(',', '.').strip()
        match = re.search(r'(\d+)[.,](\d{2})', text)
        if match:
            return float(f"{match.group(1)}.{match.group(2)}")
        return None
    
    def _add(self, p: Product) -> bool:
        key = f"{p.store}:{p.name}"
        if key not in self.seen and p.price and p.price > 0 and p.image:
            self.seen.add(key)
            self.products.append(p)
            return True
        return False

    def scrape_ah(self, page: Page, categories: List[str], max_per_cat: int = 30):
        """Scrape Albert Heijn using their search"""
        print("\n🔵 ALBERT HEIJN")
        
        for cat in categories:
            try:
                print(f"  {cat}...", end=" ", flush=True)
                
                # Navigate
                page.goto(f"https://www.ah.nl/zoeken?query={cat}", timeout=60000)
                
                # Handle cookie popup
                try:
                    page.click('button:has-text("Accepteren")', timeout=3000)
                except:
                    pass
                
                # Wait for page to load
                page.wait_for_load_state('networkidle', timeout=15000)
                time.sleep(2)
                
                # Scroll to load products
                for _ in range(3):
                    page.mouse.wheel(0, 1000)
                    time.sleep(0.5)
                
                # Get HTML
                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find all product links/cards
                added = 0
                
                # AH uses various selectors - try them all
                for selector in ['[data-testhook="product-card"]', 'article', '[class*="product"]', 'a[href*="/producten/"]']:
                    if added > 0:
                        break
                    cards = soup.select(selector)[:max_per_cat * 2]
                    
                    for card in cards:
                        if added >= max_per_cat:
                            break
                        try:
                            # Find name - look for product title
                            name = None
                            for sel in ['[data-testhook="product-title"]', '[class*="title"]', 'span[class*="Title"]', 'h2', 'h3']:
                                elem = card.select_one(sel)
                                if elem:
                                    name = elem.get_text(strip=True)
                                    if len(name) > 3 and len(name) < 100:
                                        break
                                    name = None
                            
                            if not name:
                                continue
                            
                            # Find price
                            price = None
                            for sel in ['[data-testhook="price-amount"]', '[class*="price"]', '[class*="Price"]', 'span[class*="euro"]']:
                                elem = card.select_one(sel)
                                if elem:
                                    price = self._parse_price(elem.get_text())
                                    if price:
                                        break
                            
                            if not price:
                                continue
                            
                            # Find image
                            img = card.select_one('img')
                            image = ""
                            if img:
                                image = img.get('src', '') or img.get('data-src', '')
                                if not image and img.get('srcset'):
                                    image = img.get('srcset').split()[0]
                            
                            if not image or 'data:' in image:
                                continue
                            
                            if self._add(Product(name, price, image, "Albert Heijn")):
                                added += 1
                                
                        except Exception:
                            continue
                
                print(f"{added} products")
                self._delay()
                
            except Exception as e:
                print(f"error")
                continue

    def scrape_dirk(self, page: Page, categories: List[str], max_per_cat: int = 30):
        """Scrape Dirk"""
        print("\n🔴 DIRK")
        
        for cat in categories:
            try:
                print(f"  {cat}...", end=" ", flush=True)
                
                page.goto(f"https://www.dirk.nl/boodschappen/zoeken?q={cat}", timeout=60000)
                
                try:
                    page.click('button:has-text("Accepteren")', timeout=3000)
                except:
                    pass
                
                page.wait_for_load_state('networkidle', timeout=15000)
                time.sleep(2)
                
                for _ in range(3):
                    page.mouse.wheel(0, 1000)
                    time.sleep(0.5)
                
                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                added = 0
                cards = soup.select('[class*="product"]')[:max_per_cat * 2]
                
                for card in cards:
                    if added >= max_per_cat:
                        break
                    try:
                        name = None
                        for sel in ['[class*="title"]', '[class*="name"]', 'h2', 'h3', 'span']:
                            elem = card.select_one(sel)
                            if elem:
                                text = elem.get_text(strip=True)
                                if len(text) > 3 and len(text) < 100:
                                    name = text
                                    break
                        
                        if not name:
                            continue
                        
                        price = None
                        for sel in ['[class*="price"]', '[class*="Price"]']:
                            elem = card.select_one(sel)
                            if elem:
                                price = self._parse_price(elem.get_text())
                                if price:
                                    break
                        
                        if not price:
                            continue
                        
                        img = card.select_one('img')
                        image = ""
                        if img:
                            image = img.get('src', '') or img.get('data-src', '')
                        
                        if not image or 'data:' in image:
                            continue
                        
                        if self._add(Product(name, price, image, "Dirk")):
                            added += 1
                            
                    except:
                        continue
                
                print(f"{added} products")
                self._delay()
                
            except Exception as e:
                print(f"error")
                continue

    def scrape_plus(self, page: Page, categories: List[str], max_per_cat: int = 30):
        """Scrape Plus"""
        print("\n🟢 PLUS")
        
        for cat in categories:
            try:
                print(f"  {cat}...", end=" ", flush=True)
                
                page.goto(f"https://www.plus.nl/zoekresultaten?SearchTerm={cat}", timeout=60000)
                
                try:
                    page.click('button:has-text("Accepteren")', timeout=3000)
                except:
                    pass
                
                page.wait_for_load_state('networkidle', timeout=15000)
                time.sleep(2)
                
                for _ in range(3):
                    page.mouse.wheel(0, 1000)
                    time.sleep(0.5)
                
                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')
                
                added = 0
                cards = soup.select('[class*="product"]')[:max_per_cat * 2]
                
                for card in cards:
                    if added >= max_per_cat:
                        break
                    try:
                        name = None
                        for sel in ['[class*="title"]', '[class*="name"]', 'h2', 'h3']:
                            elem = card.select_one(sel)
                            if elem:
                                text = elem.get_text(strip=True)
                                if len(text) > 3 and len(text) < 100:
                                    name = text
                                    break
                        
                        if not name:
                            continue
                        
                        price = None
                        for sel in ['[class*="price"]', '[class*="Price"]']:
                            elem = card.select_one(sel)
                            if elem:
                                price = self._parse_price(elem.get_text())
                                if price:
                                    break
                        
                        if not price:
                            continue
                        
                        img = card.select_one('img')
                        image = ""
                        if img:
                            image = img.get('src', '') or img.get('data-src', '')
                        
                        if not image or 'data:' in image:
                            continue
                        
                        if self._add(Product(name, price, image, "Plus")):
                            added += 1
                            
                    except:
                        continue
                
                print(f"{added} products")
                self._delay()
                
            except Exception as e:
                print(f"error")
                continue

    def save(self):
        """Save to games.json"""
        print(f"\n💾 Saving {len(self.products)} products...")
        random.shuffle(self.products)
        
        games = {}
        for i, p in enumerate(self.products):
            games[f"game-{i}"] = {
                "name": p.name,
                "price": f"€{p.price:.2f}",
                "image": p.image
            }
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(games, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved to {OUTPUT_FILE}")
        
    def summary(self):
        """Print summary"""
        print("\n" + "=" * 50)
        print(f"📊 TOTAL: {len(self.products)} products")
        stores = {}
        for p in self.products:
            stores[p.store] = stores.get(p.store, 0) + 1
        for store, count in sorted(stores.items(), key=lambda x: -x[1]):
            print(f"   {store}: {count}")
        if self.products:
            prices = [p.price for p in self.products]
            print(f"   Price range: €{min(prices):.2f} - €{max(prices):.2f}")

    def run(self, stores: List[str], categories: List[str], max_per_cat: int):
        """Main run method"""
        if not HAS_PLAYWRIGHT:
            return
            
        print("=" * 50)
        print("🇳🇱 DUTCH SUPERMARKET SCRAPER")
        print("=" * 50)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                slow_mo=100,  # Slow down actions
            )
            context = browser.new_context(
                viewport={'width': 1400, 'height': 900},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='nl-NL',
            )
            page = context.new_page()
            
            try:
                if 'ah' in stores:
                    self.scrape_ah(page, categories, max_per_cat)
                if 'dirk' in stores:
                    self.scrape_dirk(page, categories, max_per_cat)
                if 'plus' in stores:
                    self.scrape_plus(page, categories, max_per_cat)
            finally:
                browser.close()
        
        self.summary()
        if self.products:
            self.save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stores', nargs='+', default=['ah', 'dirk', 'plus'])
    parser.add_argument('--categories', nargs='+', default=CATEGORIES)
    parser.add_argument('--max', type=int, default=20)
    parser.add_argument('--visible', action='store_true')
    args = parser.parse_args()
    
    scraper = DutchScraper(headless=not args.visible)
    scraper.run(args.stores, args.categories, args.max)


if __name__ == "__main__":
    main()
