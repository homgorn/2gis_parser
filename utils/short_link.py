import requests


async def get_short_link(link):
    endpoint = "https://clck.ru/--"
    url = (
        f"{link}",
        "?utm_source=sender",
    )
    response = requests.get(endpoint, params={"url": url})
    return response.text
