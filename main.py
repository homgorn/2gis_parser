import asyncio
import os
import re
import time

import pandas as pd

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from selenium import webdriver
from selenium.common import InvalidSessionIdException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

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
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)


def create_dirs():
    if not os.path.exists("result_output"):
        os.makedirs("result_output")
    if not os.path.exists("files"):
        os.makedirs("files")


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
    # driver.implicitly_wait(0.1)
    link = await get_element_href(driver, xpath)
    decoded_link = await decode_fucking_social(link)
    label = await get_element_label(driver, xpath)
    label_and_link = f"{label}: {decoded_link}"
    return label_and_link if link != "" and label != "" else ""


async def find_and_get_elements(driver, main_block, data_in_memory):
    count_errors = 0
    title = await get_element_text(driver, xpathes.title)
    if title == "":
        count_errors += 1
        if count_errors >= 10:
            raise Exception
    print(title)
    try:
        time.sleep(0.4)
        element = driver.find_element(By.CSS_SELECTOR, xpathes.phone_btn)
        ActionChains(driver).move_to_element(element).click().perform()
        phone_numper = await get_elements_text(driver, xpathes.phone)
        phone = phone_numper if "..." not in phone_numper else ""
        print(phone)
    except NoSuchElementException:
        phone = ""
        pass
    link = await get_elements_text(driver, xpathes.link)
    print(link)
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


async def run_parser(city, search_query):
    create_dirs()
    options = Options()
    options.add_argument("-headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-application-cache")
    options.add_argument("--disable-animations")
    options.add_argument("--process-per-site=1")
    options.add_argument("--disable-gpu-process-for-dx12-vulkan-info-collection")

    options.add_experimental_option(
        "prefs",
        {
            "profile.managed_default_content_settings.images": 2,
        },
    )
    driver = webdriver.Chrome(options=options)
    # try:
    url = f"https://2gis.ru/{city}/search/{search_query}"
    print(url)

    driver.get(url)
    await element_click(driver, xpathes.main_banner)
    await element_click(driver, xpathes.cookie_banner)
    count_all_items = int(await get_element_text(driver, xpathes.items_count))
    print(count_all_items)
    pages = round(count_all_items / 12 + 0.5)
    items_counts = 0
    data_in_memory = []

    for _ in range(pages):
        main_block = driver.find_element(By.XPATH, xpathes.main_block)
        count_items = len(main_block.find_elements(By.XPATH, "div"))
        for item in range(1, count_items):
            print(f"div[{item}]")
            if main_block.find_element(By.XPATH, f"div[{item}]").get_attribute("class"):
                continue

            item_clicked = await element_click(main_block, f"div[{item}]/div/div[2]")
            if not item_clicked:
                await make_scroll(driver, xpathes.scroll)
                await element_click(main_block, f"div[{item}]/div/div[2]")

            print(f"Уже спарсили {items_counts} магазинов")
            items_counts += 1
            await find_and_get_elements(driver, main_block, data_in_memory)
        await make_scroll(driver, xpathes.scroll)
        await element_click(driver, xpathes.next_page_btn)
        save_data_to_csv(data_in_memory, city, search_query)
        data_in_memory = []

    driver.quit()

    await get_excel(city, search_query)

    # except (InvalidSessionIdException, NoSuchElementException, TelegramBadRequest) as e:
    #     print(e)
    #     driver.quit()
    #     save_data_to_csv(data_in_memory, city, search_query)
    #     await get_excel(city, search_query)
    # except (KeyboardInterrupt, Exception, TelegramBadRequest) as e:
    #     print(e)
    #     driver.quit()
    #     save_data_to_csv(data_in_memory, city, search_query)
    #     await get_excel(city, search_query)


async def main():
    city = "moscow"
    search_query = "Магазин телефонов"
    await run_parser(city, search_query)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
