import asyncio
import os
import re
import time
import logging  # Добавлено для использования модуля logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from dotenv import load_dotenv
from selenium.common import InvalidSessionIdException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
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
logging.basicConfig(
    filename="logs/your_bot.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def process_social(xpath, driver):
    try:
        link = await get_element_href(driver, xpath)
        decoded_link = await decode_fucking_social(link)
        label = await get_element_label(driver, xpath)
        label_and_link = f"{label}: {decoded_link}"
        return label_and_link if link != "" and label != "" else ""
    except Exception as e:
        logger.error(f"Error processing social link: {e}")
        return ""


async def find_and_get_elements(driver, main_block, data_in_memory):
    count_errors = 0
    try:
        title = await get_element_text(driver, xpathes.title)
        if title == "":
            count_errors += 1
            if count_errors >= 10:
                raise Exception
        print(title)

        time.sleep(0.2)
        element = driver.find_element(By.CSS_SELECTOR, xpathes.phone_btn)
        ActionChains(driver).move_to_element(element).click().perform()
        phone_numper = await get_elements_text(driver, xpathes.phone)
        phone = phone_numper if "..." not in phone_numper else ""
    except Exception as e:
        logger.error(f"Error finding and getting elements: {e}")
        phone = ""

    try:
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
    except Exception as e:
        logger.error(f"Error finding and getting elements: {e}")


async def run_parser(city, search_query):
    create_dirs()
    driver = await get_driver()

    try:
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
            try:
                main_block = driver.find_element(By.XPATH, xpathes.main_block)
                count_items = len(main_block.find_elements(By.XPATH, "div"))
                for item in range(1, count_items):
                    try:
                        if main_block.find_element(By.XPATH, f"div[{item}]").get_attribute("class"):
                            continue

                        item_clicked = await element_click(main_block, f"div[{item}]/div/div[2]")
                        if not item_clicked:
                            await make_scroll(driver, xpathes.scroll)
                            await element_click(main_block, f"div[{item}]/div/div[2]")

                        print(f"Уже спарсили {items_counts} магазинов")
                        items_counts += 1

                        await find_and_get_elements(driver, main_block, data_in_memory)
                    except TelegramNetworkError:
                        continue

            except TelegramNetworkError:
                continue

            await make_scroll(driver, xpathes.scroll)
            await element_click(driver, xpathes.next_page_btn)
            save_data_to_csv(data_in_memory, city, search_query)
            data_in_memory = []

        driver.quit()

        await get_excel(city, search_query)
    except Exception as e:
        logger.error(f"Error in main parsing process: {e}")
        pass
    except (InvalidSessionIdException, NoSuchElementException) as e:
        logger.error(f"Error in main parsing process: {e}")
        driver.quit()
        save_data_to_csv(data_in_memory, city, search_query)
        await get_excel(city, search_query)
    except (KeyboardInterrupt, Exception) as e:
        logger.error(f"Error in main parsing process: {e}")
        driver.quit()
        save_data_to_csv(data_in_memory, city, search_query)
        await get_excel(city, search_query)


async def main():
    city = "samara"
    search_query = "Магазин%20техники"
    await run_parser(city, search_query)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
