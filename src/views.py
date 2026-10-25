import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
import time
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


STOCKS_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY") or os.getenv("API_KEY") or ""
CURRENCY_API_URL = "https://open.er-api.com/v6/latest/RUB"
STOCK_API_URL = "https://www.alphavantage.co/query"


CURRENCY_CACHE: Dict[str, float] = {"RUB": 1.0}


def init_currency_rates() -> None:
    if len(CURRENCY_CACHE) > 1:
        return
    try:
        response = requests.get(CURRENCY_API_URL, timeout=10)
        response.raise_for_status()
        time.sleep(1.2)
        payload = response.json()
        if payload.get("result") != "success":
            raise ValueError("Currency API did not return success")
        for currency, rub_to_currency in payload.get("rates", {}).items():
            if isinstance(rub_to_currency, (int, float)) and rub_to_currency > 0:
                CURRENCY_CACHE[currency.upper()] = round(1 / rub_to_currency, 4)
    except (requests.RequestException, ValueError, TypeError) as exc:
        logger.error("Не удалось получить курсы валют через API: %s", exc)


def get_currency_rates(currencies: List[str]) -> List[dict]:
    requested = list(dict.fromkeys(currency.upper() for currency in currencies if currency))
    if not requested:
        return []

    init_currency_rates()
    return [
        {"currency": currency, "rate": CURRENCY_CACHE[currency]}
        for currency in requested
        if currency in CURRENCY_CACHE and currency != "RUB"
    ]


def convert_currency_fast(amount: float, currency: str) -> float:
    """конвертирует валюту в рубли"""
    normalized_currency = (currency or "RUB").upper()
    if normalized_currency == "RUB":
        return round(amount, 2)

    init_currency_rates()
    return round(amount * CURRENCY_CACHE.get(normalized_currency, 1.0), 2)


def get_stock_prices(stocks: List[str]) -> List[dict]:

    if not STOCKS_API_KEY:
        logger.warning("Не задан ALPHA_VANTAGE_API_KEY (или API_KEY) для котировок акций")
        return []

    result = []
    for stock in dict.fromkeys(symbol.upper() for symbol in stocks if symbol):
        try:
            response = requests.get(
                STOCK_API_URL,
                params={"function": "GLOBAL_QUOTE", "symbol": stock, "apikey": STOCKS_API_KEY},
                timeout=10,
            )
            response.raise_for_status()
            time.sleep(1.2)
            payload = response.json()
            quote = payload.get("Global Quote", {})
            price = quote.get("05. price")
            if price is not None:
                result.append({"stock": stock, "price": round(float(price), 2)})
            else:
                logger.warning("API не вернул котировку для %s: %s", stock, payload.get("Note") or payload.get("Information") or "нет данных")
        except (requests.RequestException, ValueError, TypeError) as exc:
            logger.error("Не удалось получить цену акции %s: %s", stock, exc)
    return result


def get_greeting(dt: datetime) -> str:
    hour = dt.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 18:
        return "Добрый день"
    if 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def generate_main_page(
    df_transactions: pd.DataFrame,
    date_str: str,
    user_currencies: Optional[List[str]] = None,
    user_stocks: Optional[List[str]] = None,
) -> str:

    logger.info("Собираем главную страницу под дату %s", date_str)
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    greeting = get_greeting(dt)
    currencies = user_currencies if user_currencies is not None else ["USD", "EUR"]
    stocks = user_stocks if user_stocks is not None else ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]

    df = df_transactions.copy()
    if df.empty:
        df["Дата операции"] = pd.to_datetime(df.get("Дата операции", pd.Series(dtype="datetime64[ns]")))
    else:
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce")

    start_of_month = pd.Timestamp(year=dt.year, month=dt.month, day=1)
    end_date = pd.Timestamp(dt)
    df_historical = df[
        (df["Дата операции"] >= start_of_month)
        & (df["Дата операции"] <= end_date)
    ].copy()

    if "Сумма операции" in df_historical.columns:
        df_historical["Сумма операции"] = pd.to_numeric(df_historical["Сумма операции"], errors="coerce")
    else:
        df_historical["Сумма операции"] = pd.Series(dtype=float)
    expenses_df = df_historical[df_historical["Сумма операции"] < 0]

    # Показываем все карты из истории в порядке первого появления
    # Расходы считаются только по расходным операциям выбранного периода
    cards_metrics = {}
    if "Номер карты" in df.columns:
        for raw_card_num in df["Номер карты"]:
            if pd.isna(raw_card_num):
                continue
            card_num = str(raw_card_num).strip()
            if not card_num or card_num.lower() in {"none", "nan"}:
                continue
            last_digits = card_num[-4:] if len(card_num) >= 4 else card_num
            cards_metrics.setdefault(last_digits, 0.0)

    for _, row in expenses_df.iterrows():
        raw_card_num = row.get("Номер карты", "")

        if pd.isna(raw_card_num):
            continue

        card_num = str(raw_card_num).strip()

        if not card_num or card_num.lower() in {"none", "nan"}:
            continue

        last_digits = card_num[-4:] if len(card_num) >= 4 else card_num
        amount = abs(float(row["Сумма операции"]))

        currency = str(
            row.get("Валюта операции", "RUB") or "RUB"
        ).upper()

        amount_in_rub = convert_currency_fast(amount, currency)

        if currency != "RUB" and currency not in CURRENCY_CACHE:
            logger.warning(
                "Курс %s недоступен; сумма оставлена без конвертации",
                currency,
            )

        cards_metrics[last_digits] = (
            cards_metrics.get(last_digits, 0.0) + amount_in_rub
        )

    cards_data = [
        {
            "last_digits": last_digits,
            "total_spent": round(total_spent, 2),
            "cashback": round(total_spent * 0.01, 2),
        }
        for last_digits, total_spent in cards_metrics.items()
    ]

    df_spending = expenses_df.copy()
    df_spending["abs_amount"] = df_spending["Сумма операции"].abs()
    top_5 = df_spending.sort_values(by="abs_amount", ascending=False).head(5)
    top_transactions = []
    for _, row in top_5.iterrows():
        category = row.get("Категория")
        description = row.get("Описание")
        top_transactions.append(
            {
                "date": pd.Timestamp(row["Дата операции"]).strftime("%d.%m.%Y"),
                "amount": float(row["Сумма операции"]),
                "category": str(category) if pd.notna(category) and str(category) != "nan" else "Разное",
                "description": str(description) if pd.notna(description) and str(description) != "nan" else "",
            }
        )

    return json.dumps(
        {
            "greeting": greeting,
            "cards": cards_data,
            "top_transactions": top_transactions,
            "currency_rates": get_currency_rates(currencies),
            "stock_prices": get_stock_prices(stocks),
        },
        ensure_ascii=False,
        indent=2,
    )
