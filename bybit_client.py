import ccxt
import secret_settings
# Инициализируем биржу (замените 'binance' на вашу биржу, например, 'bybit', 'okx')
# Для фьючерсов Binance используется субкласс 'binanceusdm'
exchange = ccxt.bybit({
    'apiKey': secret_settings.YOUR_API_KEY,
    'secret': secret_settings.YOUR_SECRET_KEY,
    'enableRateLimit': True,  # Обязательно для соблюдения лимитов запросов
})


def get_open_positions_and_pnl():
    result = ''
    try:
        # Загружаем рынки, чтобы CCXT знал структуру тикеров
        exchange.load_markets()

        # Получаем все позиции по аккаунту
        positions = exchange.fetch_positions()
        print('header')
        header_string = f"{'Символ':<12} | {'Сторона':<7} | {'Размер':<10} | {'Вход':<10} | {'Текущая':<10} | {'Unrealized PnL':<12}"
        print(header_string)
        result += header_string + '\n'
        print("-" * 75)
        result += "-" * 75 + '\n'

        has_open_positions = False

        pos_sum = 0
        unrealized_pnl_sum = 0
        for pos in positions:
            # У разных бирж пустые позиции могут иметь размер 0.0, None или '0'
            contracts = pos.get('contracts')


            if contracts is not None and float(contracts) > 0:




                has_open_positions = True
                symbol = pos.get('symbol', 'N/A') or 0
                side = pos.get('side', 'N/A').upper() or 0
                entry_price = pos.get('entryPrice', 0) or 0
                current_price = pos.get('markPrice', 0) or 0
                unrealized_pnl = pos.get('unrealizedPnl', 0) or 0

                pos_sum += float(contracts) * float(entry_price)
                unrealized_pnl_sum += unrealized_pnl

                # Форматируем вывод данных
                res_string = f"{symbol:<12} | {side:<7} | {contracts:<10} | {entry_price:<10.4f} | {current_price:<10.4f} | {unrealized_pnl:<12.2f}"
                print(res_string)
                result+=res_string+'\n'

        if not has_open_positions:
            print("У вас нет открытых позиций.")

    except Exception as e:
        print(f"Произошла ошибка при получении позиций: {e}")

    try:
        ratio = unrealized_pnl_sum/pos_sum
    except:
        ratio = 0

    return result, ratio


def close_all_positions():
    try:
        exchange.load_markets()
        positions = exchange.fetch_positions()
        closed_count = 0

        for pos in positions:
            contracts = pos.get('contracts')

            if contracts is not None and float(contracts) > 0:
                symbol = pos.get('symbol')
                side = pos.get('side').upper()  # LONG или SHORT
                amount = float(contracts)

                order_side = 'sell' if side == 'LONG' else 'buy'

                # Базовые параметры закрытия
                params = {'reduceOnly': True}

                # РЕШЕНИЕ ОШИБКИ BYBIT:
                # Извлекаем 'positionIdx' из сырых данных биржи (pos['info'])
                # В Hedge Mode: 1 — для LONG, 2 — для SHORT. В One-Way: 0.
                raw_info = pos.get('info', {})
                position_idx = raw_info.get('positionIdx')

                if position_idx is not None:
                    params['positionIdx'] = int(position_idx)

                print(f"Закрываю позицию {side} по {symbol} (Idx: {position_idx}) объемом {amount}...")

                order = exchange.create_market_order(
                    symbol=symbol,
                    side=order_side,
                    amount=amount,
                    params=params
                )

                print(f"Позиция {symbol} успешно закрыта. ID ордера: {order.get('id')}")
                closed_count += 1

        if closed_count == 0:
            print("Нет открытых позиций для закрытия.")
        else:
            print(f"Всего закрыто позиций: {closed_count}")

    except Exception as e:
        print(f"Произошла ошибка при закрытии позиций: {e}")
