import asyncio
import logging
import os
import sys
from typing import Any, Dict
from aiogram.client.session.aiohttp import AiohttpSession

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, Message
from aiogram.utils.backoff import Backoff, BackoffConfig
from dotenv import load_dotenv
from mtranslate import translate
import logging

from selenium.common import TimeoutException, InvalidSessionIdException

from main import run_parser
from save_on_excel import get_excel

DEFAULT_BACKOFF_CONFIG = BackoffConfig(min_delay=1.0, max_delay=5.0, factor=1.3, jitter=0.1)
session = AiohttpSession(timeout=600000000000000000000000000000000)

load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML, session=session)
form_router = Router()


class Form(StatesGroup):
    city = State()
    query = State()


@form_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.city)
    await message.answer("Введи название города")


@form_router.message(Form.city)
async def process_city(message: Message, state: FSMContext) -> None:
    await state.update_data(city=message.text)
    await state.set_state(Form.query)
    await message.answer("Введи поисковый запрос")


@form_router.message(Form.query)
async def process_query(message: Message, state: FSMContext) -> None:
    data = await state.update_data(query=message.text)
    await state.clear()
    await show_summary(message=message, data=data, state=state)
    await state.clear()


backoff_config: BackoffConfig = DEFAULT_BACKOFF_CONFIG
backoff = Backoff(config=backoff_config)


async def show_summary(message: Message, data: Dict[str, Any], state: FSMContext) -> None:
    # query = "%20".join((data["query"].split(" ")))
    try:
        query = data["query"]
        translated_city = translate(data["city"], "en", "ru").lower()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(await run_parser(translated_city, query, 1, 0))
        await message.answer_document(
            FSInputFile(f"files/{translated_city}_{query}.xlsx"),
            caption="Запрос выполнен успешно",
        )
        os.remove(f"files/{translated_city}_{query}.xlsx")
        os.remove(f"result_output/{translated_city}_{query}.csv")
        await state.clear()
    except TelegramNetworkError as e:
        print(f"Произошло исключение TimeoutException в bot.py")

    except TimeoutException as e:
        print(f"Произошло исключение TimeoutException в bot.py")
    # except Exception:
    #     backoff.reset()
    #     await get_excel(translated_city, query)
    #     await message.answer_document(FSInputFile(f"files/{translated_city}_{query}.xlsx"))
    #     os.remove(f"files/{translated_city}_{query}.xlsx")
    #     os.remove(f"result_output/{translated_city}_{query}.csv")
    #     await state.clear()


async def main():
    try:
        dp = Dispatcher()
        dp.include_router(form_router)
        await dp.start_polling(bot, polling_timeout=500000000000000, backoff_config=backoff_config)
    except TelegramNetworkError as e:
        print(f"Произошло исключение TimeoutException в main")

    except TimeoutException as e:
        print(f"Произошло исключение TimeoutException в main")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
