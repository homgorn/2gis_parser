import asyncio
import os
import re

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


def process_social(xpath, driver):
    driver.implicitly_wait(0.2)
    link = get_element_href(driver, xpath)
    decoded_link = decode_fucking_social(link)
    label = get_element_label(driver, xpath)
    label_and_link = f"{label}: {decoded_link}"
    return label_and_link if link != "" and label != "" else ""


def find_and_get_elements(driver, main_block, data_in_memory):
    title = get_element_text(driver, xpathes.title)
    print(title)
    driver.implicitly_wait(0.2)
    phone_btn_clicked = element_click(driver, xpathes.phone_btn)
    driver.implicitly_wait(0.2)
    phone = get_elements_text(driver, xpathes.phone) if phone_btn_clicked else ""
    link = get_element_text(driver, xpathes.link)
    socials_selectors = [xpathes.social[f"social{i}"] for i in range(1, 6)]

    socials = []
    for xpath in socials_selectors:
        socials.append(process_social(xpath, driver))
    email = get_element_href(driver, xpathes.email)
    real_email = re.search(r"mailto:(.+)", email).group(1) if email != "" else ""
    rating = get_element_text(driver, xpathes.rating)
    move_to_element(driver, main_block)

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
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        element_click(driver, xpathes.main_banner)
        element_click(driver, xpathes.cookie_banner)
        count_all_items = int(get_element_text(driver, xpathes.items_count))
        print(count_all_items)
        pages = round(count_all_items / 12 + 0.5)
        items_counts = 0
        data_in_memory = []

        for _ in range(pages):
            main_block = driver.find_element(By.XPATH, xpathes.main_block)
            count_items = len(main_block.find_elements(By.XPATH, "div"))
            print(count_items)
            for item in range(1, count_items + 1):
                if main_block.find_element(By.XPATH, f"div[{item}]").get_attribute("class"):
                    continue
                item_clicked = element_click(main_block, f"div[{item}]/div/div[2]")
                if not item_clicked:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    element_click(main_block, f"div[{item}]/div/div[2]")
                print(f"Уже спарсили {items_counts} магазинов")
                items_counts += 1
                find_and_get_elements(driver, main_block, data_in_memory)

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            element_click(driver, xpathes.next_page_btn)

        driver.quit()
        save_data_to_csv(data_in_memory, city, search_query)
        await get_excel(city, search_query)
    except (InvalidSessionIdException, NoSuchElementException) as e:
        print(e)
        save_data_to_csv(data_in_memory, city, search_query)
        await get_excel(city, search_query)
    except (KeyboardInterrupt, Exception, TelegramBadRequest):
        save_data_to_csv(data_in_memory, city, search_query)
        await get_excel(city, search_query)


async def main():
    city = "samara"
    search_query = "Автосалон"
    await run_parser(city, search_query, 1)


if __name__ == "__main__":
    asyncio.run(main())
