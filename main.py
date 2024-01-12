import asyncio
import cProfile
import os
import re
import datetime

import pandas as pd
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from selenium import webdriver
from selenium.common import InvalidSessionIdException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from save_on_excel import get_excel
from utils import xpathes
from utils.decod_link import decode_fucking_social
from utils.elements import (
    element_click,
    get_element_href,
    get_element_label,
    get_element_text,
    get_elements_text,
    move_to_element,
    make_scroll,
    get_find_element
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)


def save_data_to_csv(data_in_memory, city, search_query):
    df = pd.DataFrame(
        data_in_memory, columns=["title", "link", "phone", "real_email", "socials", "rating"]
    )
    df.to_csv(
        f"result_output/{city}_{search_query}.csv",
        mode="a",
        header=not os.path.isfile(f"result_output/{city}_{search_query}.csv"),
        index=False,
    )


async def process_social(xpath, driver):
    # driver.implicitly_wait(0.2)
    link = await get_element_href(driver, xpath)
    decoded_link = await decode_fucking_social(link)
    label = await get_element_label(driver, xpath)
    label_and_link = f"{label}: {decoded_link}"
    print(label_and_link)
    return label_and_link if link != "" and label != "" else ""


async def find_and_get_elements(driver, main_block, data_in_memory):
    title = await get_element_text(driver, xpathes.title)
    print(title)
    driver.implicitly_wait(0.1)
    phone_btn_clicked = await element_click(driver, xpathes.phone_btn)
    driver.implicitly_wait(0.1)
    phone = await get_elements_text(driver, xpathes.phone) if phone_btn_clicked else ""
    link = await get_element_text(driver, xpathes.link)
    socials_selectors = [xpathes.social[f"social{i}"] for i in range(1, 6)]

    socials = []
    for xpath in socials_selectors:
        socials.append(await process_social(xpath, driver))
    email = await get_element_href(driver, xpathes.email)
    real_email = re.search(r"mailto:(.+)", email).group(1) if email != "" else ""
    rating = await get_element_text(driver, xpathes.rating)
    await move_to_element(driver, main_block)

    row_data = [
        title,
        link,
        phone,
        real_email,
        socials,
        rating,
    ]

    data_in_memory.append(row_data)


async def run_parser(city, search_query, user_id):
    try:
        url = f"https://2gis.ru/{city}/search/{search_query}"
        options = Options()
        options.add_argument("-headless")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_experimental_option(
            "prefs",
            {
                "profile.managed_default_content_settings.images": 2,
            },
        )
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        # await element_click(driver, xpathes.main_banner)
        await element_click(driver, xpathes.cookie_banner)
        count_all_items = int(await get_element_text(driver, xpathes.items_count))
        print(count_all_items)
        pages = round(count_all_items / 12 + 0.5)
        items_counts = 0
        data_in_memory = []

        for _ in range(pages):
            try:
                main_block = await get_find_element(driver, xpathes.main_block)
                count_items = len(main_block.find_elements(By.CSS_SELECTOR, "div"))
                print(count_items)
                for item in range(1, count_items + 1):
                    start_time = datetime.datetime.now()
                    if main_block.find_element(By.CSS_SELECTOR, xpathes.main_block + f" > div:nth-child({item})") \
                            .get_attribute("class"):
                        continue

                    item_clicked = await element_click(main_block, xpathes.main_block + f" > div:nth-child({item})")
                    if not item_clicked:
                        await make_scroll(driver, xpathes.scroll)
                        await element_click(main_block, xpathes.main_block + f" > div:nth-child({item})")

                    print(f"Уже спарсили {items_counts} магазинов")
                    items_counts += 1
                    await find_and_get_elements(driver, main_block, data_in_memory)
                    end_time = datetime.datetime.now()
                    result = end_time - start_time
                    print(f"Время выполнения итерации: {result} секунд")
                await make_scroll(driver, xpathes.scroll)
                await element_click(driver, xpathes.next_page_btn)

            except NoSuchElementException:
                continue

        driver.quit()
        save_data_to_csv(data_in_memory, city, search_query)
        await get_excel(city, search_query)
    except (InvalidSessionIdException, NoSuchElementException, TelegramBadRequest) as e:
        print(e)
        save_data_to_csv(data_in_memory, city, search_query)
        await get_excel(city, search_query)
    except (KeyboardInterrupt, Exception, TelegramBadRequest) as e:
        print(e)
        save_data_to_csv(data_in_memory, city, search_query)
        await get_excel(city, search_query)


async def main():
    city = "samara"
    search_query = "Вкусно и точка"
    await run_parser(city, search_query, 1)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
