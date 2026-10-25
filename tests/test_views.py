import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import requests

from src.views import (
    CURRENCY_CACHE,
    convert_currency_fast,
    generate_main_page,
    get_greeting,
    get_stock_prices,
    init_currency_rates,
)


def setup_function():
    CURRENCY_CACHE.clear()
    CURRENCY_CACHE["RUB"] = 1.0


def test_get_greeting():
    assert get_greeting(datetime(2021, 12, 31, 9, 0, 0)) == "Доброе утро"
    assert get_greeting(datetime(2021, 12, 31, 14, 0, 0)) == "Добрый день"
    assert get_greeting(datetime(2021, 12, 31, 20, 0, 0)) == "Добрый вечер"
    assert get_greeting(datetime(2021, 12, 31, 2, 0, 0)) == "Доброй ночи"


@patch("src.views.requests.get")
def test_init_currency_rates_success(mock_get):
    response = MagicMock()
    response.json.return_value = {
        "result": "success",
        "rates": {"USD": 0.01, "EUR": 0.02},
    }
    response.raise_for_status.return_value = None
    mock_get.return_value = response

    init_currency_rates()

    assert CURRENCY_CACHE["USD"] == 100.0
    assert CURRENCY_CACHE["EUR"] == 50.0


@patch("src.views.requests.get", side_effect=requests.RequestException("network error"))
def test_init_currency_rates_failure_does_not_use_fake_rates(mock_get):
    init_currency_rates()
    assert CURRENCY_CACHE == {"RUB": 1.0}


def test_convert_currency_fast():
    CURRENCY_CACHE["USD"] = 100.0
    assert convert_currency_fast(50.0, "USD") == 5000.0


@patch("src.views.requests.get")
def test_get_stock_prices_uses_api_key_and_parses_quote(mock_get):
    import src.views as views

    old_api_key = views.STOCKS_API_KEY
    try:
        views.STOCKS_API_KEY = "test-key"
        response = MagicMock()
        response.json.return_value = {"Global Quote": {"05. price": "123.4500"}}
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        assert get_stock_prices(["AAPL"]) == [{"stock": "AAPL", "price": 123.45}]
        assert mock_get.call_args.kwargs["params"]["apikey"] == "test-key"
    finally:
        views.STOCKS_API_KEY = old_api_key


@patch("src.views.get_currency_rates", return_value=[])
@patch("src.views.get_stock_prices", return_value=[])
def test_generate_main_page_filters_from_start_of_month_to_input_date(
    mock_stock_prices, mock_currency_rates
):
    CURRENCY_CACHE["RUB"] = 1.0
    data = {
        "Дата операции": [
            "2021-11-30 12:00:00",
            "2021-12-01 00:00:00",
            "2021-12-20 12:00:00",
            "2021-12-26 12:00:00",
        ],
        "Номер карты": ["*1111", "*7197", "*7197", "*2222"],
        "Сумма операции": [-9000.0, -1000.0, -500.0, -7000.0],
        "Валюта операции": ["RUB", "RUB", "RUB", "RUB"],
        "Категория": ["Вне периода", "Супермаркеты", "Одежда", "После даты"],
        "Описание": ["old", "Колхоз", "Zara", "future"],
    }

    result = json.loads(
        generate_main_page(
            pd.DataFrame(data), "2021-12-25 14:00:00", [], []
        )
    )

    assert result["greeting"] == "Добрый день"

    assert result["cards"] == [
        {"last_digits": "1111", "total_spent": 0.0, "cashback": 0.0},
        {"last_digits": "7197", "total_spent": 1500.0, "cashback": 15.0},
        {"last_digits": "2222", "total_spent": 0.0, "cashback": 0.0},
    ]
    assert [item["description"] for item in result["top_transactions"]] == [
        "Колхоз",
        "Zara",
    ]
    assert result["currency_rates"] == []
    assert result["stock_prices"] == []


@patch("src.views.get_currency_rates", return_value=[])
@patch("src.views.get_stock_prices", return_value=[])
def test_generate_main_page_empty_df(mock_stock_prices, mock_currency_rates):
    df_empty = pd.DataFrame(
        columns=[
            "Дата операции",
            "Номер карты",
            "Сумма операции",
            "Валюта операции",
            "Категория",
            "Описание",
        ]
    )
    result = json.loads(
        generate_main_page(df_empty, "2021-12-25 14:00:00", [], [])
    )
    assert result["cards"] == []
    assert result["top_transactions"] == []


@patch("src.views.get_currency_rates", return_value=[])
@patch("src.views.get_stock_prices", return_value=[])
def test_generate_main_page_only_income(mock_stock_prices, mock_currency_rates):
    data = {
        "Дата операции": ["2021-12-20 12:00:00"],
        "Номер карты": ["*7197"],
        "Сумма операции": [5000.0],
        "Валюта операции": ["RUB"],
        "Категория": ["Пополнение"],
        "Описание": ["Зарплата"],
    }
    result = json.loads(
        generate_main_page(pd.DataFrame(data), "2021-12-25 14:00:00", [], [])
    )


    assert result["cards"] == [
        {"last_digits": "7197", "total_spent": 0.0, "cashback": 0.0}
    ]
    assert result["top_transactions"] == []
