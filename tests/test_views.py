import pytest
import json
import pandas as pd
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.views import (
    get_greeting,
    convert_currency_fast,
    generate_main_page,
    CURRENCY_CACHE,
    init_currency_rates,
)


def test_get_greeting():
    assert get_greeting(datetime(2021, 12, 31, 9, 0, 0)) == "Доброе утро"
    assert get_greeting(datetime(2021, 12, 31, 14, 0, 0)) == "Добрый день"
    assert get_greeting(datetime(2021, 12, 31, 20, 0, 0)) == "Добрый вечер"
    assert get_greeting(datetime(2021, 12, 31, 2, 0, 0)) == "Доброй ночи"


@patch("requests.get")
def test_init_currency_rates_success(mock_get):
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"rates": {"USD": 0.01}}
    mock_get.return_value = mock_res

    CURRENCY_CACHE.clear()
    CURRENCY_CACHE["RUB"] = 1.0
    init_currency_rates()
    assert "USD" in CURRENCY_CACHE


@patch("requests.get", side_effect=Exception("error"))
def test_init_currency_rates_fail(mock_get):
    CURRENCY_CACHE.clear()
    CURRENCY_CACHE["RUB"] = 1.0
    init_currency_rates()
    assert CURRENCY_CACHE["USD"] == 96.50


def test_convert_currency_fast():
    CURRENCY_CACHE["USD"] = 100.0
    assert convert_currency_fast(50.0, "USD") == 5000.0


def test_generate_main_page():
    data = {
        "Дата операции": ["2021-12-20 12:00:00", "2021-12-20 12:00:00"],
        "Номер карты": ["*7197", "None"],
        "Сумма операции": [-1000.0, -500.0],
        "Валюта операции": ["RUB", "RUB"],
        "Категория": ["Супермаркеты", "Одежда"],
        "Описание": ["Колхоз", "Zara"],
    }
    df = pd.DataFrame(data)

    response_str = generate_main_page(df, "2021-12-25 14:00:00")
    res = json.loads(response_str)

    assert res["greeting"] == "Добрый день"
    assert len(res["cards"]) == 1


def test_generate_main_page_empty_df():
    # Проверяем работу страницы, если расходов вообще не было за весь период
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
    response_str = generate_main_page(df_empty, "2021-12-25 14:00:00")
    res = json.loads(response_str)

    assert res["cards"] == []
    assert res["top_transactions"] == []


def test_generate_main_page_only_income():

    data = {
        "Дата операции": ["2021-12-20 12:00:00"],
        "Номер карты": ["*7197"],
        "Сумма операции": [5000.0],  # Положительное число
        "Валюта операции": ["RUB"],
        "Категория": ["Пополнение"],
        "Описание": ["Зарплата"],
    }
    df = pd.DataFrame(data)
    response_str = generate_main_page(df, "2021-12-25 14:00:00")
    res = json.loads(response_str)

    # Доходы не должны попадать в метрики карт расходов
    assert res["cards"] == []
    # Доходы также НЕ должны попадать в топ-5 платежей
    assert len(res["top_transactions"]) == 0
