#!/usr/bin/env python3
"""
Dutch Supermarket Product Fetcher
Uses Open Food Facts API - an open, free database of food products

Install: pip install requests
Usage: python fetch_products.py
"""

import json
import time
import random
import requests
from typing import List, Dict, Any

OUTPUT_FILE = "games.json"

HEADERS = {
    "User-Agent": "CostcodleGame/1.0 (educational project)"
}

# Dutch supermarket brands to search
DUTCH_STORES = [
    "Albert Heijn", "AH", "Jumbo", "Lidl", "Aldi", "Plus", 
    "Dirk", "Coop", "Spar", "DekaMarkt", "Hoogvliet"
]

# Categories to search (Open Food Facts uses English)
CATEGORIES = [
    "milk", "cheese", "yogurt", "butter", "eggs",
    "bread", "cereals", "pasta", "rice", "noodles",
    "chicken", "beef", "pork", "fish", "salmon",
    "chocolate", "cookies", "chips", "candy", "snacks",
    "coffee", "tea", "juice", "soda", "water", "beer", "wine",
    "tomato", "vegetables", "fruits", "salad",
    "sauce", "ketchup", "mayonnaise", "mustard",
    "soup", "canned", "frozen",
    "toothpaste", "shampoo", "soap"
]


def fetch_open_food_facts() -> List[Dict[str, Any]]:
    """Fetch Dutch products from Open Food Facts API"""
    print("\n🌍 Fetching from OPEN FOOD FACTS (Dutch products)...")
    
    all_products = []
    seen = set()
    
    # Search for products sold in Netherlands
    base_url = "https://world.openfoodfacts.org/cgi/search.pl"
    
    for category in CATEGORIES:
        try:
            print(f"  Searching: {category}...", end=" ", flush=True)
            
            params = {
                "search_terms": category,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 100,
                "countries_tags_en": "netherlands",
            }
            
            response = requests.get(base_url, params=params, headers=HEADERS, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", [])
                added = 0
                
                for p in products:
                    code = p.get("code", "")
                    name = p.get("product_name", "") or p.get("product_name_nl", "")
                    
                    if not name or code in seen:
                        continue
                    
                    seen.add(code)
                    
                    # Get image
                    image = p.get("image_front_url", "") or p.get("image_url", "")
                    
                    # Try to get price (Open Food Facts doesn't always have prices)
                    # Generate a realistic price based on category
                    price = generate_realistic_price(category, name)
                    
                    if image and price > 0:
                        all_products.append({
                            "name": name,
                            "price": price,
                            "image": image,
                            "store": "Dutch Supermarket",
                            "category": category
                        })
                        added += 1
                
                print(f"found {added} products")
            else:
                print(f"error: {response.status_code}")
            
            time.sleep(0.5)  # Be nice to the API
            
        except Exception as e:
            print(f"error: {e}")
    
    print(f"  ✅ Total products: {len(all_products)}")
    return all_products


def generate_realistic_price(category: str, name: str) -> float:
    """Generate a realistic Dutch supermarket price based on category"""
    price_ranges = {
        "milk": (0.89, 2.49),
        "cheese": (1.99, 8.99),
        "yogurt": (0.79, 3.49),
        "butter": (1.49, 4.99),
        "eggs": (1.99, 4.49),
        "bread": (0.99, 3.99),
        "cereals": (1.99, 5.99),
        "pasta": (0.79, 2.99),
        "rice": (1.29, 4.99),
        "noodles": (0.69, 2.49),
        "chicken": (3.99, 9.99),
        "beef": (4.99, 14.99),
        "pork": (3.49, 11.99),
        "fish": (3.99, 12.99),
        "salmon": (5.99, 15.99),
        "chocolate": (0.99, 4.99),
        "cookies": (0.99, 3.49),
        "chips": (1.29, 3.99),
        "candy": (0.79, 2.99),
        "snacks": (1.49, 4.49),
        "coffee": (3.99, 9.99),
        "tea": (1.49, 4.99),
        "juice": (1.29, 3.99),
        "soda": (0.79, 2.49),
        "water": (0.39, 1.99),
        "beer": (0.79, 2.49),
        "wine": (3.99, 12.99),
        "vegetables": (0.99, 3.99),
        "fruits": (0.99, 4.99),
        "sauce": (1.29, 3.99),
        "ketchup": (1.49, 2.99),
        "mayonnaise": (1.29, 3.49),
        "soup": (1.29, 3.99),
        "frozen": (2.49, 6.99),
        "toothpaste": (1.49, 4.99),
        "shampoo": (1.99, 6.99),
        "soap": (0.99, 3.99),
    }
    
    min_price, max_price = price_ranges.get(category, (1.49, 5.99))
    
    # Add some variation based on product name length (larger names often = bigger products)
    name_factor = min(len(name) / 30, 1.5)
    
    base_price = random.uniform(min_price, max_price)
    price = base_price * (0.8 + name_factor * 0.4)
    
    # Round to realistic price points
    price = round(price * 100) / 100
    if price > 1:
        # Make it end in .49, .99, .29, etc.
        cents = random.choice([0.29, 0.49, 0.69, 0.79, 0.89, 0.99])
        price = int(price) + cents
    
    return round(price, 2)


def format_price(price: float) -> str:
    """Format price as Euro string"""
    return f"€{price:.2f}"


def generate_games_json(products: List[Dict[str, Any]]) -> None:
    """Generate games.json from product list"""
    print(f"\n📝 Generating {OUTPUT_FILE}...")
    
    # Shuffle for variety
    random.shuffle(products)
    
    games = {}
    for i, product in enumerate(products):
        games[f"game-{i}"] = {
            "name": product["name"],
            "price": format_price(product["price"]),
            "image": product["image"]
        }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(games, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(games)} products to {OUTPUT_FILE}")


def main():
    print("=" * 60)
    print("🇳🇱 DUTCH SUPERMARKET PRODUCT FETCHER")
    print("   Using Open Food Facts (open database)")
    print("=" * 60)
    
    all_products = fetch_open_food_facts()
    
    if not all_products:
        print("\n❌ No products found!")
        return
    
    print(f"\n📊 TOTAL PRODUCTS: {len(all_products)}")
    
    # Show category distribution
    categories = {}
    for p in all_products:
        cat = p.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nBy category:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:10]:
        print(f"  - {cat}: {count}")
    
    generate_games_json(all_products)
    
    print("\n✨ Done! Your games.json is ready.")
    print("=" * 60)


if __name__ == "__main__":
    main()
