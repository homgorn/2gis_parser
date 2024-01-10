from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


def get_element_text(driver: WebDriver, path: str) -> str:
    try:
        return driver.find_element(By.XPATH, path).text
    except NoSuchElementException:
        return ""


def get_elements_text(driver: WebDriver, path: str) -> set:
    phone_set = set()
    try:
        result = driver.find_elements(By.XPATH, path)
        for element in result:
            phone_set.add(element.text)
        return phone_set
    except NoSuchElementException:
        return set()


def get_element_href(driver, path):
    try:
        return driver.find_element(By.CSS_SELECTOR, path).get_dom_attribute("href")
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
