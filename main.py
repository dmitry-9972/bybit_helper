import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F
from pathlib import Path

import secret_settings
from bybit_client import close_all_positions
# ================== НАСТРОЙКИ ==================
from secret_settings import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Глобальные переменные
CHAT_ID = secret_settings.CHAT_ID  # ← будет заполняться автоматически
last_price = None
trading_active = True

CLOSE_WHEN_PNL_RATIO_ABOVE = 0.01  ################################################ ЗАКРЫТЬ КОГДА ПНЛ БУДЕТ БОЛЬШЕ 1%


# ================== КОМАНДА START ==================
@dp.message(Command("start"))
async def start(message: types.Message):
    print('start')
    global CHAT_ID
    CHAT_ID = message.chat.id

    print(f"✅ Chat ID сохранён: {CHAT_ID}")

    await message.answer(
        "✅ Бот успешно запущен!\n"
        f"Ваш Chat ID: <code>{CHAT_ID}</code>\n\n"
        "Теперь я буду присылать ваши открытые позиции каждые 30 секунд",
        parse_mode="HTML"
    )


# ================== ОБРАБОТКА КНОПКИ ==================
@dp.callback_query(F.data == "close_all")
async def close_all_trades(callback: types.CallbackQuery):
    print('close_all_trades')
    global trading_active
    if CHAT_ID is None:
        await callback.answer("Сначала выполните /start", show_alert=True)
        return

    await callback.answer("🔴 Команда принята!", show_alert=True)
    print("🛑 Получена команда: ЗАКРЫТЬ ВСЕ СДЕЛКИ")
    trading_active = False

    from bybit_client import close_all_positions
    for x in range(2):
        try:
            print(f'try to close all {x}')
            close_all_positions()
        except:
            pass

    # here we should close all positions

    try:
        await bot.send_message(CHAT_ID, "✅ Команда на закрытие всех сделок выполнена!")
    except Exception as e:
        print(f"Ошибка: {e}")


# ================== ОСНОВНОЙ ЦИКЛ ==================
async def price_updater():
    print('price_updater')
    global last_price

    await asyncio.sleep(3)  # ждём, пока пользователь нажмёт /start

    while True:
        if CHAT_ID is None:
            print('CHAT_ID is None')
            await asyncio.sleep(5)
            continue
        print('CHAT_ID is not None')

        if not trading_active:
            await asyncio.sleep(10)
            continue

        # current_price = await get_btc_price()
        # last_price = current_price
        current_positions, pnl_ration = await get_current_positions()

        if pnl_ration >= CLOSE_WHEN_PNL_RATIO_ABOVE:
            print('ЗАКРЫВАЕМ ВСЕ СДЕЛКИ')
            close_all_positions()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔴 ЗАКРЫТЬ ВСЕ СДЕЛКИ", callback_data="close_all")
        ]])

        try:
            await bot.send_message(
                CHAT_ID,
                # f"💰 BTC/USDT: **${current_price:,.2f}**",
                current_positions + '\n' + f'PNL RATION: {pnl_ration}',
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Ошибка отправки цены: {e}")

        await asyncio.sleep(30)


# async def get_btc_price():
#     print('get_btc_price')
#     try:
#         import requests
#         r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10)
#         return float(r.json()['price'])
#     except:
#         return 67000.0

async def get_current_positions():
    from bybit_client import get_open_positions_and_pnl
    return get_open_positions_and_pnl()


# ================== ЗАПУСК ==================
async def main():
    print("🚀 Бот запущен. Напишите /start в Telegram...")
    asyncio.create_task(price_updater())

    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())