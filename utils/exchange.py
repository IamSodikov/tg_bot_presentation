import aiohttp
from typing import Optional

async def get_rate() -> Optional[float]:
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "tether", "vs_currencies": "rub"}
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                price = data.get("tether", {}).get("rub")
                if isinstance(price, (int, float)):
                    return float(price)
    except Exception as e:
        print("USDT/RUB fetch failed: %s", e)
    return None
