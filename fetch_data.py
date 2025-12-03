import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import config

class MarketDataFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = {}
        
    def _rate_limited_request(self, url: str, params: dict = None, platform: str = "generic") -> Optional[dict]:
        if platform in self.last_request_time:
            elapsed = time.time() - self.last_request_time[platform]
            if elapsed < config.FETCH_CONFIG["rate_limit_delay"]:
                time.sleep(config.FETCH_CONFIG["rate_limit_delay"] - elapsed)
        
        for attempt in range(config.FETCH_CONFIG["retry_attempts"]):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=config.FETCH_CONFIG["timeout"]
                )
                response.raise_for_status()
                self.last_request_time[platform] = time.time()
                return response.json()
            except requests.RequestException:
                if attempt < config.FETCH_CONFIG["retry_attempts"] - 1:
                    time.sleep(config.FETCH_CONFIG["retry_delay"] * (attempt + 1))
                else:
                    return None
        return None

    def fetch_polymarket_markets(self) -> List[Dict]:
        params = {
            "limit": 50,
            "closed": "false",
            "order": "startDate",
            "ascending": "false"
        }
        
        data = self._rate_limited_request(
            config.POLYMARKET_API_URL,
            params=params,
            platform="polymarket"
        )
        
        if not data:
            return []
        
        markets = []
        for event in data:
            if not event.get('markets'):
                continue
                
            for m in event['markets']:
                market_data = self._parse_polymarket_market(event, m)
                if market_data:
                    markets.append(market_data)
        
        return markets
    
    def _parse_polymarket_market(self, event: dict, market: dict) -> Optional[Dict]:
        try:
            if not market.get('outcomePrices'):
                return None
            
            outcomes = json.loads(market['outcomePrices'])
            if len(outcomes) < 2:
                return None
            
            yes_price = float(outcomes[0])
            no_price = float(outcomes[1])
            
            start_date_str = event.get('startDate')
            if start_date_str:
                try:
                    start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                    age_minutes = (datetime.now(start_date.tzinfo) - start_date).total_seconds() / 60
                except:
                    age_minutes = None
            else:
                age_minutes = None
            
            volume = float(market.get('volume', 0))
            liquidity = float(market.get('liquidity', 0))
            
            return {
                "platform": "Polymarket",
                "id": market.get('id', 'unknown'),
                "question": event.get('title', 'Unknown'),
                "yes_price": yes_price,
                "no_price": no_price,
                "volume": volume,
                "liquidity": liquidity,
                "spread": abs(yes_price + no_price - 1.0),
                "age_minutes": age_minutes,
                "timestamp": datetime.now().isoformat(),
                "description": event.get('description', ''),
                "end_date": event.get('endDate'),
            }
        except Exception:
            return None
    
    def fetch_kalshi_markets(self, api_key: Optional[str] = None) -> List[Dict]:
        if not api_key:
            return []
        
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        url = f"{config.KALSHI_API_URL}/markets"
        params = {
            "limit": 50,
            "status": "open"
        }
        
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            markets = []
            for market in data.get('markets', []):
                market_data = self._parse_kalshi_market(market)
                if market_data:
                    markets.append(market_data)
            
            return markets
        except Exception:
            return []
    
    def _parse_kalshi_market(self, market: dict) -> Optional[Dict]:
        try:
            yes_price = market.get('yes_bid', 50) / 100.0
            no_price = market.get('no_bid', 50) / 100.0
            
            open_time_str = market.get('open_time')
            if open_time_str:
                try:
                    open_time = datetime.fromisoformat(open_time_str.replace('Z', '+00:00'))
                    age_minutes = (datetime.now(open_time.tzinfo) - open_time).total_seconds() / 60
                except:
                    age_minutes = None
            else:
                age_minutes = None
            
            return {
                "platform": "Kalshi",
                "id": market.get('ticker', 'unknown'),
                "question": market.get('title', 'Unknown'),
                "yes_price": yes_price,
                "no_price": no_price,
                "volume": float(market.get('volume', 0)),
                "liquidity": float(market.get('open_interest', 0)),
                "spread": abs(yes_price + no_price - 1.0),
                "age_minutes": age_minutes,
                "timestamp": datetime.now().isoformat(),
                "description": market.get('subtitle', ''),
                "end_date": market.get('close_time'),
            }
        except Exception:
            return None

def generate_synthetic_markets() -> List[Dict]:
    markets = []
    
    sensational_markets = [
        {
            "question": "Will the US have a civil war in 2025?",
            "yes_price": 0.78,
            "volume": 450000,
            "age_minutes": 8,
            "platform": "Polymarket"
        },
        {
            "question": "Will Gavin Newsom launch a cryptocurrency token in Q1 2025?",
            "yes_price": 0.85,
            "volume": 120000,
            "age_minutes": 12,
            "platform": "Polymarket"
        },
        {
            "question": "Will the US military engage Venezuela by December 2025?",
            "yes_price": 0.72,
            "volume": 280000,
            "age_minutes": 15,
            "platform": "Polymarket"
        },
        {
            "question": "Will OpenSea launch a token by March 2025?",
            "yes_price": 0.81,
            "volume": 95000,
            "age_minutes": 6,
            "platform": "Kalshi"
        },
        {
            "question": "Will Monad do an airdrop by February 2025?",
            "yes_price": 0.76,
            "volume": 175000,
            "age_minutes": 18,
            "platform": "Kalshi"
        },
    ]
    
    normal_markets = [
        {
            "question": "Will it rain in London tomorrow?",
            "yes_price": 0.45,
            "volume": 25000,
            "age_minutes": 120,
            "platform": "Kalshi"
        },
        {
            "question": "Will Bitcoin be above $100k by year end?",
            "yes_price": 0.62,
            "volume": 850000,
            "age_minutes": 480,
            "platform": "Polymarket"
        },
        {
            "question": "Will Trump win 2024 election?",
            "yes_price": 0.55,
            "volume": 2500000,
            "age_minutes": 2400,
            "platform": "Polymarket"
        },
    ]
    
    all_markets = sensational_markets + normal_markets
    
    for idx, m in enumerate(all_markets):
        yes_price = m["yes_price"]
        markets.append({
            "platform": m["platform"],
            "id": f"synthetic_{idx}",
            "question": m["question"],
            "yes_price": yes_price,
            "no_price": round(1.0 - yes_price, 2),
            "volume": m["volume"],
            "liquidity": m["volume"] * 0.3,
            "spread": 0.02,
            "age_minutes": m["age_minutes"],
            "timestamp": datetime.now().isoformat(),
            "description": m["question"],
            "end_date": (datetime.now() + timedelta(days=90)).isoformat(),
        })
    
    return markets

def get_all_markets(use_mock: bool = True, kalshi_api_key: Optional[str] = None) -> List[Dict]:
    if use_mock:
        return generate_synthetic_markets()
    
    fetcher = MarketDataFetcher()
    
    poly_markets = fetcher.fetch_polymarket_markets()
    
    kalshi_markets = []
    if kalshi_api_key:
        kalshi_markets = fetcher.fetch_kalshi_markets(kalshi_api_key)
    
    all_markets = poly_markets + kalshi_markets
    
    if not all_markets:
        return generate_synthetic_markets()
    
    return all_markets
