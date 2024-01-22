import asyncio
import os
import random
import re
import time

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from dotenv import load_dotenv
from selenium.common import InvalidSessionIdException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from save_on_csv import create_dirs, save_data_to_csv
from save_on_excel import get_excel
from utils import xpathes
from utils.decod_link import decode_fucking_social
from utils.driver_settings import get_driver
from utils.elements import (
    element_click,
    get_element_href,
    get_element_label,
    get_element_text,
    get_elements_text,
    make_scroll,
    move_to_element,
)

load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)

if not os.path.exists("logs/"):
    os.makedirs("logs")


async def process_social(xpath, driver):
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

    time.sleep(0.2)
    try:
        element = driver.find_element(By.CSS_SELECTOR, xpathes.phone_btn)
        ActionChains(driver).move_to_element(element).click().perform()
        phone_number = await get_elements_text(driver, xpathes.phone)
        phone = phone_number if "..." not in phone_number else ""
    except NoSuchElementException:
        phone = ""
        pass

    link = await get_elements_text(driver, xpathes.link)
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


async def run_parser(city, search_query, current_page_number, items_counts):
    current_page_number = current_page_number
    create_dirs()
    driver = await get_driver()
    url = f"https://2gis.ru/{city}/search/{search_query}/"
    try:
        print(url)
        driver.get(url)
        await element_click(driver, xpathes.main_banner)
        await element_click(driver, xpathes.cookie_banner)
        count_all_items = int(await get_element_text(driver, xpathes.items_count))
        print(count_all_items)
        pages = round(count_all_items / 12 + 0.5)
        items_counts = items_counts
        data_in_memory = []

        if current_page_number != 1:
            for i in range(1, current_page_number):
                main_block = driver.find_element(By.XPATH, xpathes.main_block)

                for item in range(1, 13):
                    if main_block.find_element(By.XPATH, f"div[{item}]").get_attribute("class"):
                        continue
                    await make_scroll(driver, xpathes.scroll)
                    await element_click(main_block, f"div[{item}]/div/div[2]")
                await make_scroll(driver, xpathes.scroll)
                await element_click(driver, xpathes.next_page_btn)

        for i in range(current_page_number, pages + 1):
            try:
                main_block = driver.find_element(By.XPATH, xpathes.main_block)

                for item in range(1, 13):
                    try:
                        if main_block.find_element(By.XPATH, f"div[{item}]").get_attribute("class"):
                            continue
                        item_clicked = await element_click(main_block, f"div[{item}]/div/div[2]")
                        if not item_clicked:
                            await make_scroll(driver, xpathes.scroll)
                            await element_click(main_block, f"div[{item}]/div/div[2]")
                        if items_counts % 100 == 0:
                            print(f"Уже спарсили {items_counts} магазинов")
                        items_counts += 1

                        await find_and_get_elements(driver, main_block, data_in_memory)
                    except TelegramNetworkError:
                        continue

            except NoSuchElementException as e:
                print(f"Произошло исключение NoSuchElementException: {e}")
                pass

            except InvalidSessionIdException as e:
                print(f"Произошло исключение InvalidSessionIdException в первом блоке: {e}")
                driver.quit()
                time.sleep(5)
                await run_parser(city, search_query, current_page_number)
            current_page_number += 1
            await make_scroll(driver, xpathes.scroll)
            await element_click(driver, xpathes.next_page_btn)
            save_data_to_csv(data_in_memory, city, search_query)
            data_in_memory = []

        driver.quit()
        await get_excel(city, search_query)

    except TelegramNetworkError as e:
        print(f"Произошло исключение TimeoutException: {e}")

    except TimeoutException as e:
        print(f"Произошло исключение TimeoutException: {e}")
    except InvalidSessionIdException as e:
        print(f"Произошло исключение InvalidSessionIdException во втором блоке: {e}")
        driver.quit()
        time.sleep(5)
        await run_parser(city, search_query, current_page_number, items_counts)

    except KeyboardInterrupt:
        driver.quit()
        save_data_to_csv(data_in_memory, city, search_query)
        await get_excel(city, search_query)


async def main():
    city = "samara"
    search_query = "Магазин%20техники"
    current_page_number = 1
    await run_parser(city, search_query, current_page_number, 0)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
