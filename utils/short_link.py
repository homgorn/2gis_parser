import aiohttp


async def async_get_short_link(link):
    endpoint = "https://clck.ru/--"
    url = f"{link}?utm_source=sender"

    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint, params={"url": url}) as response:
            return await response.text()
