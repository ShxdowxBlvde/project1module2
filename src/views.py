import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List
from dotenv import load_dotenv
import pandas as pd
import requests

load_dotenv()
logger = logging.getLogger(__name__)
API_KEY: str = os.getenv("API_KEY") or ""

CURRENCY_CACHE: Dict[str, float] = {"RUB": 1.0}


def init_currency_rates():
    global CURRENCY_CACHE
    if len(CURRENCY_CACHE) > 1:
        return
    url = "https://apilayer.com"
    headers = {"apikey": API_KEY}
    params = {"base": "RUB"}
    try:
        logger.info("загружаем курсы валют один раз за запуск")
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        rates = response.json().get("rates", {})
        for cur, rate in rates.items():
            if rate > 0:
                CURRENCY_CACHE[cur] = round(1.0 / rate, 4)
    except Exception as e:
        logger.error(f"лимит апи исчерпан: {e}, берем дефолтные курсы")
        CURRENCY_CACHE.update({"USD": 96.50, "EUR": 104.20, "TRY": 2.82})


def convert_currency_fast(amount: float, currency: str) -> float:
    init_currency_rates()
    return round(amount * CURRENCY_CACHE.get(currency, 1.0), 2)


def get_greeting(dt: datetime) -> str:
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
    logger.info(f"собираем главную страницу под дату {date_str}")
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    greeting = get_greeting(dt)

    df = df_transactions.copy()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])


    df_historical = df[df["Дата операции"] <= pd.to_datetime(dt)]


    expenses_df = df_historical[df_historical["Сумма операции"] < 0]
    cards_metrics: Dict[str, float] = {}

    for _, row in expenses_df.iterrows():
        card_num = str(row.get("Номер карты", ""))
        # Отсекаем пустые ячейки и некорректные строки 'nan'
        if not card_num or card_num == "None" or card_num == "nan" or pd.isna(row.get("Номер карты")):
            continue
        last_digits = card_num[-4:] if len(card_num) >= 4 else card_num

        amount = abs(row["Сумма операции"])
        currency = row.get("Валюта операции", "RUB")

        amount_in_rub = convert_currency_fast(amount, currency)
        cards_metrics[last_digits] = cards_metrics.get(last_digits, 0.0) + amount_in_rub

    cards_data = []
    for last_digits, total_spent in cards_metrics.items():
        cards_data.append({
            "last_digits": last_digits,
            "total_spent": round(total_spent, 2),
            "cashback": round(total_spent * 0.01, 2)
        })


    df_spending = df_historical[df_historical["Сумма операции"] < 0].copy()
    df_spending["abs_amount"] = df_spending["Сумма операции"].abs()
    top_5 = df_spending.sort_values(by="abs_amount", ascending=False).head(5)

    top_transactions = []
    for _, row in top_5.iterrows():
        cat = row.get("Категория")
        cat = str(cat) if pd.notnull(cat) else "Разное"
        desc = row.get("Описание")
        desc = str(desc) if pd.notnull(desc) else ""

        top_transactions.append({
            "date": pd.to_datetime(row["Дата операции"]).strftime("%d.%m.%Y"),
            "amount": row["Сумма операции"],
            "category": cat if cat != "nan" else "Разное",
            "description": desc if desc != "nan" else ""
        })

    return json.dumps({
        "greeting": greeting,
        "cards": cards_data,
        "top_transactions": top_transactions,
        "currency_rates": [
            {"currency": "USD", "rate": CURRENCY_CACHE.get("USD", 96.50)},
            {"currency": "EUR", "rate": CURRENCY_CACHE.get("EUR", 104.20)}
        ],
        "stock_prices": [
            {"stock": "AAPL", "price": 150.12},
            {"stock": "AMZN", "price": 3173.18},
            {"stock": "GOOGL", "price": 2742.39},
            {"stock": "MSFT", "price": 296.71},
            {"stock": "TSLA", "price": 1007.08}
        ]
    }, ensure_ascii=False, indent=2)

