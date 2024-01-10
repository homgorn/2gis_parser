from time import sleep
from urllib.parse import unquote
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
import xpathes
import datetime
from selenium.webdriver.chrome.options import Options

TABLE_COLUMNS = ["Название", "Телефон", "Адрес", "Ссылка", "Соц.сети"]
TABLE = {column: [] for column in TABLE_COLUMNS}
CURRENT_DAY = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M")


def get_element_text(driver: WebDriver, path: str) -> str:
    try:
        return driver.find_element(By.XPATH, path).text
    except NoSuchElementException:
        return ""


def move_to_element(driver: WebDriver, element) -> None:
    try:
        webdriver.ActionChains(driver).move_to_element(element).perform()
    except StaleElementReferenceException:
        pass


def element_click(driver, path: str) -> bool:
    try:
        driver.find_element(By.XPATH, path).click()
        return True
    except:
        return False


def main():
    city = "samara"
    search_query = "Вкусно и точка"
    url = f"https://2gis.ru/{city}/search/{search_query}"
    options = Options()
    options.add_argument("-headless")
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
            vk = get_element_text(driver, xpathes.vk)
            telegram = get_element_text(driver, xpathes.telegram)
            odnoklassniki = get_element_text(driver, xpathes.odnoklassniki)
            social = [vk, telegram, odnoklassniki]
            move_to_element(driver, main_block)
            link = unquote(driver.current_url)
            address = get_element_text(driver, xpathes.address)
            TABLE["Название"].append(title)
            TABLE["Телефон"].append(phone)
            TABLE["Адрес"].append(address)
            TABLE["Ссылка"].append(link)
            TABLE["Соц.сети"].append(social)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        element_click(driver, xpathes.next_page_btn)
        sleep(0.5)
    driver.quit()
    pd.DataFrame(TABLE).to_excel(f"./files/{city}-{search_query}-{CURRENT_DAY}.xlsx")


if __name__ == "__main__":
    main()
