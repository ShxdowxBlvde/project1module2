import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import pandas as pd
import requests

load_dotenv()

logger = logging.getLogger(__name__)

# Инициализируем API-ключ из .env файла
API_KEY: str = os.getenv("API_KEY") or ""


def convert_currency(transaction: Dict[str, Any]) -> float:
    """
    Конвертирует сумму транзакции в рубли с помощью внешнего API
    Если валюта изначально рубли, возвращает сумму без запроса
    """
    amount = float(transaction["amount"])
    currency = transaction["currency"]

    if currency == "RUB":
        return amount

    url = "https://api.apilayer.com/exchangerates_data/convert"
    headers = {"apikey": API_KEY}
    params = {"from": currency, "to": "RUB", "amount": amount}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        return float(data["result"])
    except Exception as e:
        logger.error(f"Ошибка конвертации валюты {currency} через API: {e}")
        # В случае ошибки возвращаем исходную сумму как резервный вариант
        return amount


def get_greeting(dt: datetime) -> str:
    """Определяет приветствие в зависимости от часа суток"""
    hour = dt.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def generate_main_page(df_transactions: pd.DataFrame, date_str: str) -> str:
    """
    Генерирует JSON-ответ для Главной страницы
    Конвертирует все иностранные траты в рубли с помощью функции convert_currency
    """
    logger.info(f"Генерация главной страницы для даты {date_str}")
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    # 1. Приветствие
    greeting = get_greeting(dt)

    # Фильтруем транзакции до указанной даты
    df = df_transactions.copy()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])
    df = df[df["Дата операции"] <= pd.to_datetime(dt)]

    # Фильтруем только расходы
    expenses_df = df[df["Сумма операции"] < 0]

    cards_metrics: Dict[str, float] = {}

    # 2. Расчет по картам с конвертацией валюты
    for _, row in expenses_df.iterrows():
        card_num = str(row.get("Номер карты", "Неизвестно"))
        last_digits = card_num[-4:] if len(card_num) >= 4 else card_num

        # Формируем структуру словаря для функции конвертации
        tx_data = {
            "amount": abs(row["Сумма операции"]),
            "currency": row.get("Валюта операции", "RUB"),  # Убедитесь, что эта колонка есть в Excel
        }

        # Конвертируем расход в рубли
        amount_in_rub = convert_currency(tx_data)

        # Аккумулируем траты по маске карты
        cards_metrics[last_digits] = cards_metrics.get(last_digits, 0.0) + amount_in_rub

    # Преобразуем агрегированные метрики карт в требуемый формат списка
    cards_data = []
    for last_digits, total_spent in cards_metrics.items():
        cards_data.append(
            {
                "last_digits": last_digits,
                "total_spent": round(total_spent, 2),
                "cashback": round(total_spent * 0.01, 2),  # 1 рубль на каждые 100 рублей
            }
        )

    # 3. Топ-5 транзакций по сумме платежа (сортируем по модулю исходного значения)
    df["abs_amount"] = df["Сумма операции"].abs()
    top_5 = df.sort_values(by="abs_amount", ascending=False).head(5)

    top_transactions = []
    for _, row in top_5.iterrows():
        top_transactions.append(
            {
                "date": pd.to_datetime(row["Дата операции"]).strftime("%d.%m.%Y"),
                "amount": row["Сумма операции"],
                "category": row.get("Категория", "Разное"),
                "description": row.get("Описание", ""),
            }
        )

    # Заглушки для блоков курсов валют и акций (как в изначальной структуре)
    currency_rates = [{"currency": "USD", "rate": 73.21}, {"currency": "EUR", "rate": 87.08}]
    stock_prices = [
        {"stock": "AAPL", "price": 150.12},
        {"stock": "AMZN", "price": 3173.18},
        {"stock": "GOOGL", "price": 2742.39},
        {"stock": "MSFT", "price": 296.71},
        {"stock": "TSLA", "price": 1007.08},
    ]

    response_data = {
        "greeting": greeting,
        "cards": cards_data,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }

    return json.dumps(response_data, ensure_ascii=False, indent=2)
