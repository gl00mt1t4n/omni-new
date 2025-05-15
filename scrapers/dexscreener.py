import requests
import re 
import json

def get_trending_pairs(limit=20):
    url = "https://dexscreener.com/solana?rankBy=trendingScoreH24&order=desc"
    raw = requests.get(url)
    html = raw.text

    # regex match since there is lots of gibberish

    print(html[:2000])  # Preview first 2000 chars
    match = re.search(r"window\.__SERVER_DATA\s*=\s*({.*?});", html, re.DOTALL)
    if not match:
        raise Exception("Couldn't extract from dexscreener API")
    print(match.group(1)[:1000])  # Print first part of the matched JSON

if __name__ == "__main__":
    get_trending_pairs()