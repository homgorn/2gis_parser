import asyncio
import datetime
from time import sleep
from urllib.parse import unquote

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from utils import xpathes
from utils.elements import (
    element_click,
    get_element_href,
    get_element_text,
    move_to_element,
)

TABLE_COLUMNS = ["Название", "Телефон", "Адрес", "Ссылка", "Соц.сети"]
TABLE = {column: [] for column in TABLE_COLUMNS}
CURRENT_DAY = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M")


async def run_parser(city, search_query):
    url = f"https://2gis.ru/{city}/search/{search_query}"
    options = Options()
    # options.add_argument("-headless")
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    driver.get(url)
    element_click(driver, xpathes.main_banner)
    element_click(driver, xpathes.cookie_banner)
    count_all_items = int(get_element_text(driver, xpathes.items_count))
    pages = round(count_all_items / 12 + 0.5)

    for _ in range(pages):
        main_block = driver.find_element(By.XPATH, xpathes.main_block)
        count_items = len(main_block.find_elements(By.XPATH, "div"))
        for item in range(1, count_items + 1):
            if main_block.find_element(By.XPATH, f"div[{item}]").get_attribute("class"):
                continue
            item_clicked = element_click(main_block, f"div[{item}]/div/div[2]")
            if not item_clicked:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                element_click(main_block, f"div[{item}]/div/div[2]")
            title = get_element_text(driver, xpathes.title)
            phone_btn_clicked = element_click(driver, xpathes.phone_btn)
            phone = get_element_text(driver, xpathes.phone) if phone_btn_clicked else ""
            # vk = get_element_href(driver, xpathes.vk)
            # telegram = get_element_href(driver, xpathes.telegram)
            # odnoklassniki = get_element_href(driver, xpathes.odnoklassniki)
            # print("vk = ", vk)
            # print("telegram = ", telegram)
            # social = [vk, telegram, odnoklassniki]
            move_to_element(driver, main_block)
            link = unquote(driver.current_url)
            address = get_element_text(driver, xpathes.address)
            TABLE["Название"].append(title)
            TABLE["Телефон"].append(phone)
            TABLE["Адрес"].append(address)
            TABLE["Ссылка"].append(link)
            TABLE["Соц.сети"].append("")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        element_click(driver, xpathes.next_page_btn)
        sleep(0.5)
    driver.quit()


async def main():
    city = "самара"
    search_query = "Мороженное"
    await run_parser(city, search_query)


if __name__ == "__main__":
    asyncio.run(main())
