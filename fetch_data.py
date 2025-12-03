import requests
import json
import random
from datetime import datetime

POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"

def fetch_polymarket_data():
    """
    Fetches active binary markets from Polymarket.
    Returns a list of standardized market objects.
    """
    try:
        params = {
            "limit": 10,
            "closed": "false",
            "order": "startDate",
            "ascending": "false" 
        }
        response = requests.get(POLYMARKET_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        markets = []
        for event in data:
            if not event.get('markets'):
                continue
                
            for m in event['markets']:
                if not m.get('outcomePrices'):
                    continue
                    
                try:
                    outcomes = json.loads(m['outcomePrices'])
                    
                    markets.append({
                        "platform": "Polymarket",
                        "id": m.get('id'),
                        "question": event.get('title'),
                        "yes_price": float(outcomes[0]) if len(outcomes) > 0 else 0.5,
                        "no_price": float(outcomes[1]) if len(outcomes) > 1 else 0.5,
                        "volume": float(m.get('volume', 0)),
                        "timestamp": datetime.now().isoformat()
                    })
                except:
                    continue
        return markets
    except Exception as e:
        print(f"Error fetching Polymarket data: {e}")
        return []

def generate_mock_data():
    """
    Generates synthetic market data for demonstration purposes.
    """
    markets = []
    
    markets.append({
        "platform": "Polymarket",
        "id": "mock_poly_1",
        "question": "US Civil War in 2025?",
        "yes_price": 0.65,
        "no_price": 0.35,
        "volume": 250000,
        "age_minutes": 10,
        "timestamp": datetime.now().isoformat()
    })
    
    markets.append({
        "platform": "Polymarket",
        "id": "mock_poly_2",
        "question": "Will Gavin Newsom launch a token in September?",
        "yes_price": 0.80,
        "no_price": 0.20,
        "volume": 50000,
        "age_minutes": 5,
        "timestamp": datetime.now().isoformat()
    })
    
    markets.append({
        "platform": "Kalshi",
        "id": "mock_kalshi_1",
        "question": "Will OpenSea launch a token by October 31?",
        "yes_price": 0.75,
        "no_price": 0.25,
        "volume": 100000,
        "age_minutes": 12,
        "timestamp": datetime.now().isoformat()
    })

    markets.append({
        "platform": "Kalshi",
        "id": "mock_kalshi_2",
        "question": "Will it rain in London tomorrow?",
        "yes_price": 0.40,
        "no_price": 0.60,
        "volume": 5000,
        "age_minutes": 300,
        "timestamp": datetime.now().isoformat()
    })

    return markets

def get_all_markets(use_mock=True):
    """
    Aggregates data from all sources.
    """
    if use_mock:
        return generate_mock_data()
    
    poly_markets = fetch_polymarket_data()
    for m in poly_markets:
        m['age_minutes'] = random.randint(1, 300)
        
    return poly_markets
