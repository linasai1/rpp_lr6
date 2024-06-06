import os
import logging
from dotenv import load_dotenv
import requests
from TOKEn2 import bot_token
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Command
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

load_dotenv()


logging.basicConfig(level=logging.INFO)
bot = Bot(token=bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())
# States for adding, deleting and changing the currency exchange rate
class AddCurrencyState(StatesGroup):
    waiting_for_currency = State()
    waiting_for_rate =State()
class RemoveCurrencyState(StatesGroup):
    waiting_for_currencv = State()

class RemoveCurrencyState(StatesGroup):
    waiting_for_currency = State()

class ChangeRateState(StatesGroup):
    waiting_for_currency = State()
    waiting_for_rate = State()

@dp.message_handler(state=AddCurrencyState.waiting_for_currency) 
async def add_currency(message: types.Message, state: FSMContext):
    try:
        currency_name, rate = message.text.split()
        rate = float(rate)
        response = requests.post('http://127.0.0.1:5001/load', json={'currency_name': currency_name, 'rate': rate})
        if response.status_code == 200:
            await message.reply(f"Валюта {currency_name} успешна добавлена с курсом к рублю {rate}")
        else:
            await message.reply("Произошла ошибка. Пожалуйста,попробуйте снова.")
    except ValueError:
        await message.reply("Неккоретный формат ввода. Пожалуйста, введите название валюты и курс в формате: название_валюты курс")
    await state.finish()

# Обработчик для ввода названия валюты при удалении валюты
@dp.message_handler (state=RemoveCurrencyState.waiting_for_currency) 
async def remove_currency(message: types.Message, state: FSMContext):
    currency_name = message.text 
    response = requests.post('http://127.0.0.1:5001/delete', json={'currency_name': currency_name})
    if response.status_code == 200:
        await message.reply(f"Валюта {currency_name} успешно удалена")
    else:
        await message.reply("Ппоробуйте ещё раз")
    await state.finish()

# Обработчик для ввода названия валюты при изменении курса
@dp.message_handler (state=ChangeRateState.waiting_for_currency) 
async def change_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text
    exists = await currency_exists(currency_name)
    if exists:
        await state.update_data(currency_name=currency_name)
        await message.reply("Введите новый курс")
        await ChangeRateState.next()
    else:
        await message.reply("Такой валюты не существует.Пожалуйста,выберите существующую валюту.")
        await state.finish()

#Обработчик для ввода нового курса валюты
@dp.message_handler(state=ChangeRateState.waiting_for_rate)
async def update_currency_rate(message: types.Message, state: FSMContext): 
    try:
        rate = float(message.text)
        data = await state.get_data()
        currency_name = data.get('currency_name')
        response = requests.post("http://127.0.0.1:5001/update_currency", json={"currency_name": currency_name, "rate": rate})
        if response.status_code == 200:
            await message.reply(f"Курс валюты {currency_name} успешно обновлен")
        else:
            await message.reply("Произошла ошибка. Пожалуйста,попробуйте снова")
    except ValueError:
        await message.reply("Неккоретный формат курса. Пожалуйста,введите числовое значение")
    await state.finish()

async def currency_exists(currency_name):
    response = requests.get("http://127.0.0.1:5002/currency_exists", json={"currency_name": currency_name})
    if response.status_code != 200:
        return False
    return True

# Конвертация валюты на сервере
async def convert_currency_enter_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        data = await state.get_data()
        currency_name = data.get("currency_name")
        response = requests.get(f'http://127.0.0.1:5002/convert')
        data = response.json()
        converted_amount = data["converted_amount"] # Извлекаем конвертированную сумму из ответа сервера
        await message.reply(f"{amount} {currency_name} = {converted_amount:.2f} RUB") # Отформатировали вывод до двух знаков после запятой
    except ValueError:
        await message.reply("Неккоретный формат. Введите валюту числом.") 
    await state.finish()#Completing the status after processing the amount input


async def is_admin(user_id):
    admins = [1184918666] 
    if user_id not in admins:
        return False
    return True

@dp.message_handler(Command("manage_currencyy"))
async def manage_currency(message: types.Message): 
    admins = [1184918666]
    if message.from_user.id not in admins:
        await message.reply("Не успешно")
        return
    markup = types.ReplyKeyboardMarkup(row_width=3)
    btn_add = types.KeyboardButton("Добавить валюту") 
    btn_remove = types.KeyboardButton("Удалить валюту") 
    btn_change = types.KeyboardButton("Изменить курс валюты")
    markup.add(btn_add, btn_remove, btn_change)
    await message.reply(message.from_user.id)
    await message.reply("Select action:", reply_markup=markup)

#Обработка нажатия на кнопки
@dp.message_handler(lambda message: message.text in ["Добавить валюту", "Удалить валюту", "Изменить курс валюты"]) 
async def handle_buttons(message: types.Message):
    if message.text == "Добавить валюту":
        await message.reply("Добавьте название валюты")
        await AddCurrencyState.waiting_for_currency.set()
    elif message.text == "Удалить валюту":
        await message.reply("Введите название валюты")
        await RemoveCurrencyState.waiting_for_currency.set()
    elif message.text == "Изменить курс валюты":
        await message.reply("Введите название валюты")
        await ChangeRateState.waiting_for_currency.set()


# Обработчик для команды /start
@dp.message_handler(commands=["start", "start"], state="*") 
async def start_handler(message: types.Message, state: FSMContext): 
    await message.reply("Приветсвую!")

# Дополнительные действия,если необходимо перейти в другие состояния
    if await is_admin(message.from_user.id):
        markup = types.ReplyKeyboardMarkup(row_width=3) 
        btn_manage_currency = types.KeyboardButton("Управление валютами")
        btn_get_currences = types.KeyboardButton("Получить список валют") 
        btn_convert = types.KeyboardButton("Конвертировать валюту") 
        markup.add(btn_manage_currency, btn_get_currences, btn_convert)

        await message.reply("Выберите действие:", reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        btn_get_currencies = types.KeyboardButton("Получить список валют") 
        btn_convert = types.KeyboardButton("Конвертировать валюту") 
        markup.add(btn_get_currences, btn_convert)
        
        await message.reply("Выберите действие: ", reply_markup=markup)

@dp.message_handler(lambda message: message.text == "Управление валютами")
async def handle_manage_currency(message: types.Message):
    await manage_currency(message)

@dp.message_handler(lambda message:message.text == "Получить список валют")
async def handle_get_currences(message: types.Message):
    await get_currencies(message)

@dp.message_handler(lambda message:message.text == "Конвертировать валюту")
async def handle_convert_currency(message: types.Message):
    await convert_currency_start(message)

@dp.message_handler(Command("get_currencies"))
async def get_currencies(message: types.Message):
    response = requests.get('http://127.0.0.1:5002/currencies')
    if response.status_code != 200:
        await message.reply("Нет валют")
    currencies = response.json()['currencies']
    currencies_text = '\n'.join([f'{currency["currency_name"]}: {currency["rate"]} ' for currency in currencies])
    
    await message.reply(currencies_text)

@dp.message_handler(commands=["convert"])
async def convert_currency_start(message: types.Message):
    await ConvertCurrencyState.waiting_for_currency.set()
    await message.reply("Введите название валюты")

class ConvertCurrencyState(StatesGroup):
    waiting_for_currency = State()
    waiting_for_amount = State()

@dp.message_handler(state=ConvertCurrencyState.waiting_for_currency)
async def convert_currency_enter_currency(message: types.Message, state: FSMContext):
    currency_name = message.text
    exists = await currency_exists(currency_name)
    if exists:
        await state.update_data(currency_name=currency_name)
        await message.reply("Введите сумму для конвертации")
        await ConvertCurrencyState.next()
    else:
        await message.reply("Такая валюта не найдена, Пожалуйста укажите другую валюту или используйте другую команду.") 
        await state.finish()

@dp.message_handler(state=ConvertCurrencyState.waiting_for_amount)
async def convert_currency_enter_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        data = await state.get_data()
        currency_name = data.get("currency_name")
        response = requests.get(f'http://127.0.0.1:5002/convert?amount={amount}&currency_name={currency_name}')
        data = response.json()
        # Проверяем что ключ converted_amount сущетсвует в ответе сервера
        if "converted_amount" not in data:
            await message.reply("Сервер вернул некорретный ответ")
            return
        converted_amount = data["converted_amount"] # Извлекаем конвертированную сумму из ответа сервера
        await message.reply(f"{amount} {currency_name} = {converted_amount:.2f} RUB") # Отформатировали вывод до двух знаков после запятой
    except ValueError:
        await message.reply("Неккоретный формат суммы, Пожалуйста,введите числовое значение.") 
        await state.finish() # Завершаем состояние после обработки ввода суммы
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
