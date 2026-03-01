import copy
import random
from typing import List

import config
from models import MarketData


class PriceSimulator:
    def __init__(self, cfg: config.AppConfig = None, seed: int = None):
        self._cfg = cfg or config.default_config()
        self._rng = random.Random(seed)

    def _is_sensational(self, market: MarketData) -> bool:
        text = (market.question + " " + market.description).lower()
        return any(kw in text for kw in config.SENSATIONAL_KEYWORDS)

    def step(self, markets: List[MarketData], elapsed_minutes: float) -> List[MarketData]:
        updated: List[MarketData] = []
        for m in markets:
            new_m = copy.deepcopy(m)
            if self._is_sensational(m):
                new_m.yes_price = self._simulate_hype_fade(m.yes_price, elapsed_minutes)
            else:
                new_m.yes_price = self._simulate_random_walk(m.yes_price)
            new_m.no_price = round(1.0 - new_m.yes_price, 6)
            new_m.spread = abs(new_m.yes_price + new_m.no_price - 1.0)
            if m.age_minutes is not None:
                new_m.age_minutes = m.age_minutes + elapsed_minutes
            updated.append(new_m)
        return updated

    def _simulate_hype_fade(self, yes_price: float, elapsed_minutes: float) -> float:
        time_factor = elapsed_minutes / 15.0
        fade_rate = 0.08 * time_factor * yes_price
        noise = self._rng.gauss(0, 0.005)
        new_price = yes_price - fade_rate + noise
        return max(0.02, min(0.98, new_price))

    def _simulate_random_walk(self, yes_price: float) -> float:
        noise = self._rng.gauss(0, 0.01)
        return max(0.01, min(0.99, yes_price + noise))
