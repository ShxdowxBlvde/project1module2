import pytest
import json
import pandas as pd
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.views import get_greeting, convert_currency_fast, generate_main_page, CURRENCY_CACHE


def test_get_greeting():
    assert get_greeting(datetime(2021, 12, 31, 9, 0, 0)) == "Доброе утро"
    assert get_greeting(datetime(2021, 12, 31, 14, 0, 0)) == "Добрый день"
    assert get_greeting(datetime(2021, 12, 31, 20, 0, 0)) == "Добрый вечер"
    assert get_greeting(datetime(2021, 12, 31, 2, 0, 0)) == "Доброй ночи"


def test_convert_currency_fast():
    # жестко прописываем курс в кэш для теста
    CURRENCY_CACHE["USD"] = 100.0
    assert convert_currency_fast(50.0, "USD") == 5000.0
    assert convert_currency_fast(100.0, "RUB") == 100.0


def test_generate_main_page():
    data = {
        "Дата операции": ["2021-12-20 12:00:00"],
        "Номер карты": ["*7197"],
        "Сумма операции": [-1000.0],
        "Валюта операции": ["RUB"],
        "Категория": ["Супермаркеты"],
        "Описание": ["Колхоз"]
    }
    df = pd.DataFrame(data)

    response_str = generate_main_page(df, "2021-12-25 14:00:00")
    res = json.loads(response_str)

    assert res["greeting"] == "Добрый день"
    assert len(res["cards"]) == 1
    assert res["cards"][0]["last_digits"] == "7197"
    assert res["cards"][0]["total_spent"] == 1000.0
    assert res["cards"][0]["cashback"] == 10.0
