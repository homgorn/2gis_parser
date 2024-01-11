import asyncio
import logging
import os
import sys
from typing import Any, Dict

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, Message
from dotenv import load_dotenv
from mtranslate import translate

from main import run_parser

load_dotenv()
TOKEN = os.getenv("TOKEN")

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
    await show_summary(message=message, data=data)
    await state.clear()


async def show_summary(message: Message, data: Dict[str, Any]) -> None:
    query = data["query"]
    translated_city = translate(data["city"], "en", "ru").lower()
    try:
        await run_parser(translated_city, query)
        await message.answer_document(
            FSInputFile(f"files/{translated_city}_{query}.xlsx"),
            caption="Запрос выполнен успешно",
        )
        os.remove(f"files/{translated_city}_{query}.xlsx")
        os.remove(f"result_output/{translated_city}_{query}.csv")
    except Exception as e:
        await message.answer_document(
            FSInputFile(f"files/{translated_city}_{query}.xlsx"),
            caption=f"Произошла ошибка, но эти данные удалось спарсить",
        )
        os.remove(f"files/{translated_city}_{query}.xlsx")
        os.remove(f"result_output/{translated_city}_{query}.csv")


async def main():
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(form_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
