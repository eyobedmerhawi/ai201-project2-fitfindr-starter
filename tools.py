"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    listings = load_listings()

    # Step 1: Filter by price
    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]

    # Step 2: Filter by size
    if size is not None:
        listings = [l for l in listings if size.upper() in l["size"].upper()]

    # Step 3: Score by keyword overlap with description
    keywords = description.lower().split()

    def score(listing):
        text = (
            listing["title"].lower() + " " +
            listing["description"].lower() + " " +
            " ".join(listing["style_tags"]).lower()
        )
        return sum(1 for kw in keywords if kw in text)

    # Step 4: Drop zero-score listings and sort
    scored = [(score(l), l) for l in listings]
    scored = [(s, l) for s, l in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)

    return [l for _, l in scored]

# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    client = _get_groq_client()

    item_description = (
        f"{new_item['title']} — ${new_item['price']} from {new_item['platform']}. "
        f"Style: {', '.join(new_item['style_tags'])}. "
        f"Colors: {', '.join(new_item['colors'])}."
    )

    # Step 1: Check if wardrobe is empty
    if not wardrobe.get("items"):
        prompt = (
            f"A user is considering buying this secondhand item:\n{item_description}\n\n"
            f"They haven't told us what's in their wardrobe yet. "
            f"Give them 1-2 general styling suggestions — what kinds of pieces pair well "
            f"with this item, what vibe it suits, and how to wear it."
        )
    else:
        wardrobe_text = "\n".join(
            f"- {item['name']} ({', '.join(item['style_tags'])})"
            for item in wardrobe["items"]
        )
        prompt = (
            f"A user is considering buying this secondhand item:\n{item_description}\n\n"
            f"Their current wardrobe includes:\n{wardrobe_text}\n\n"
            f"Suggest 1-2 complete outfit combinations using the new item and "
            f"specific pieces from their wardrobe. Name the exact wardrobe pieces. "
            f"Be specific about the vibe and how to style it."
        )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )

    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    # Step 1: Guard against empty outfit
    if not outfit or not outfit.strip():
        return "Unable to generate fit card: no outfit suggestion provided."

    client = _get_groq_client()

    prompt = (
        f"Write a 2-4 sentence Instagram caption for this thrifted outfit.\n\n"
        f"Item: {new_item['title']} — ${new_item['price']} from {new_item['platform']}\n"
        f"Outfit: {outfit}\n\n"
        f"The caption should:\n"
        f"- Sound casual and authentic, like a real OOTD post\n"
        f"- Mention the item name, price, and platform once each\n"
        f"- Capture the outfit vibe in specific terms\n"
        f"- Use lowercase, feel free to add 1-2 relevant emojis\n"
        f"- NOT sound like a product description\n"
        f"Return only the caption text, nothing else."
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=1.2,
    )

    return response.choices[0].message.content.strip()
