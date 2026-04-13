"""
Typical shelf-life estimates (days) for common fruits and vegetables.
Values are ballpark figures for home storage (often fridge); real life varies by ripeness,
variety, and handling. Used for planning only — not food-safety advice.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass

# All lookup keys are lowercase; values are days (whole numbers).
SHELF_LIFE_DAYS: dict[str, int] = {
    # Fruits
    "apple": 21,
    "apples": 21,
    "apricot": 4,
    "apricots": 4,
    "avocado": 4,
    "avocados": 4,
    "banana": 5,
    "bananas": 5,
    "blackberry": 4,
    "blackberries": 4,
    "blueberry": 7,
    "blueberries": 7,
    "cantaloupe": 7,
    "cherry": 5,
    "cherries": 5,
    "coconut": 14,
    "cranberry": 14,
    "cranberries": 14,
    "currant": 4,
    "date": 30,
    "dates": 30,
    "dragon fruit": 5,
    "durian": 5,
    "fig": 3,
    "figs": 3,
    "gooseberry": 7,
    "grape": 7,
    "grapes": 7,
    "grapefruit": 14,
    "guava": 5,
    "honeydew": 10,
    "jackfruit": 5,
    "kiwi": 14,
    "kiwis": 14,
    "kumquat": 14,
    "lemon": 21,
    "lemons": 21,
    "lime": 21,
    "limes": 21,
    "lychee": 5,
    "mango": 7,
    "mangoes": 7,
    "mangosteen": 5,
    "melon": 7,
    "mulberry": 3,
    "nectarine": 5,
    "nectarines": 5,
    "olive": 14,
    "orange": 14,
    "oranges": 14,
    "papaya": 5,
    "passion fruit": 7,
    "peach": 4,
    "peaches": 4,
    "pear": 7,
    "pears": 7,
    "persimmon": 7,
    "pineapple": 5,
    "pineapples": 5,
    "plantain": 7,
    "plum": 5,
    "plums": 5,
    "pomegranate": 21,
    "quince": 14,
    "raspberry": 3,
    "raspberries": 3,
    "rhubarb": 7,
    "star fruit": 5,
    "strawberry": 5,
    "strawberries": 5,
    "tamarind": 14,
    "tangerine": 14,
    "tangerines": 14,
    "watermelon": 7,
    # Vegetables & herbs
    "artichoke": 7,
    "artichokes": 7,
    "arugula": 5,
    "asparagus": 4,
    "beet": 14,
    "beets": 14,
    "beetroot": 14,
    "bell pepper": 10,
    "bok choy": 5,
    "broccoli": 7,
    "brussels sprout": 7,
    "brussels sprouts": 7,
    "cabbage": 14,
    "carrot": 21,
    "carrots": 21,
    "cauliflower": 7,
    "celery": 14,
    "chard": 5,
    "chili": 14,
    "chili pepper": 14,
    "collard greens": 5,
    "corn": 3,
    "cucumber": 7,
    "cucumbers": 7,
    "edamame": 3,
    "eggplant": 7,
    "eggplants": 7,
    "endive": 7,
    "fennel": 10,
    "garlic": 30,
    "ginger": 21,
    "green bean": 7,
    "green beans": 7,
    "scallion": 10,
    "scallions": 10,
    "spring onion": 10,
    "spring onions": 10,
    "jalapeno": 14,
    "jalapenos": 14,
    "kale": 7,
    "leek": 14,
    "leeks": 14,
    "lettuce": 6,
    "mushroom": 7,
    "mushrooms": 7,
    "okra": 4,
    "onion": 30,
    "onions": 30,
    "parsnip": 14,
    "parsnips": 14,
    "pea": 5,
    "peas": 5,
    "snow peas": 5,
    "snap peas": 5,
    "potato": 14,
    "potatoes": 14,
    "pumpkin": 30,
    "radish": 14,
    "radishes": 14,
    "romaine": 6,
    "rutabaga": 14,
    "shallot": 30,
    "shallots": 30,
    "spinach": 5,
    "sprouts": 3,
    "bean sprouts": 3,
    "squash": 7,
    "butternut squash": 30,
    "zucchini": 5,
    "zucchinis": 5,
    "sweet potato": 14,
    "sweet potatoes": 14,
    "swiss chard": 5,
    "tomato": 7,
    "tomatoes": 7,
    "cherry tomato": 5,
    "cherry tomatoes": 5,
    "turnip": 14,
    "turnips": 14,
    "watercress": 4,
    "basil": 5,
    "cilantro": 10,
    "coriander": 10,
    "dill": 10,
    "mint": 7,
    "oregano": 7,
    "parsley": 14,
    "rosemary": 14,
    "sage": 7,
    "thyme": 10,
    "iceberg": 7,
    "mixed greens": 5,
    "salad greens": 5,
    "kohlrabi": 14,
    "celeriac": 14,
    "lemon grass": 14,
    "lemongrass": 14,
}


@dataclass(frozen=True)
class ShelfLifeLookup:
    days: int | None
    """Matched shelf life in days, or None if unknown."""

    matched_name: str | None
    """Canonical produce name from the database (title case for display), if matched."""

    suggestions: list[str]
    """Nearby names if lookup failed (for 'Did you mean …')."""


def _normalize(name: str) -> str:
    return " ".join(name.strip().lower().split())


def lookup_shelf_life(name: str) -> ShelfLifeLookup:
    """
    Resolve a user-typed produce name to a shelf life in days.
    Uses exact match, then substring-style match, then fuzzy match (difflib).
    """
    n = _normalize(name)
    if not n:
        return ShelfLifeLookup(None, None, [])

    keys = SHELF_LIFE_DAYS
    if n in keys:
        return ShelfLifeLookup(keys[n], n.title(), [])

    # Substring: e.g. "baby spinach" contains "spinach"
    best_key: str | None = None
    best_len = 0
    for k in keys:
        if len(k) < 3:
            continue
        if k in n:
            if len(k) > best_len:
                best_len = len(k)
                best_key = k
        elif n in k and len(n) >= 4:
            if len(k) > best_len:
                best_len = len(k)
                best_key = k
    if best_key is not None:
        return ShelfLifeLookup(keys[best_key], best_key.title(), [])

    all_keys = list(keys.keys())
    matches = difflib.get_close_matches(n, all_keys, n=8, cutoff=0.55)
    if not matches:
        sample = sorted(set(keys.keys()))[:24]
        return ShelfLifeLookup(None, None, sample)

    best = matches[0]
    ratio = difflib.SequenceMatcher(None, n, best).ratio()
    if ratio >= 0.8:
        return ShelfLifeLookup(keys[best], best.title(), [])

    return ShelfLifeLookup(None, None, matches[:8])
