from selenium import webdriver
from selenium.webdriver.chrome.options import Options


async def get_driver():
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
    options.add_argument("--disable-session-crashed-bubble")
    options.add_argument("--disable-session-restore")

    options.add_experimental_option(
        "prefs",
        {
            "profile.managed_default_content_settings.images": 2,
        },
    )
    driver = webdriver.Chrome(options=options)
    return driver
