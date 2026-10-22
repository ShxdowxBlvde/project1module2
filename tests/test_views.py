import pytest
import json
import pandas as pd
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.views import get_greeting, convert_currency, generate_main_page


def test_get_greeting():
    """Проверяем правильность подбора приветствий по времени суток"""
    assert get_greeting(datetime(2026, 1, 1, 9, 0, 0)) == "Доброе утро"
    assert get_greeting(datetime(2026, 1, 1, 14, 0, 0)) == "Добрый день"
    assert get_greeting(datetime(2026, 1, 1, 19, 0, 0)) == "Добрый вечер"
    assert get_greeting(datetime(2026, 1, 1, 2, 0, 0)) == "Доброй ночи"


def test_convert_currency_rub():
    """Если валюта RUB, API дергаться не должно, возвращаем сумму как есть"""
    tx = {"amount": 500.0, "currency": "RUB"}
    assert convert_currency(tx) == 500.0


@patch("requests.get")
def test_convert_currency_usd(mock_get):
    """Имитируем успешный ответ внешнего API для конвертации валюты"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": 7500.0}
    mock_get.return_value = mock_response

    tx = {"amount": 100.0, "currency": "USD"}
    result = convert_currency(tx)

    assert result == 7500.0
    mock_get.assert_called_once()


@patch("requests.get", side_effect=Exception("API limit exceeded"))
def test_convert_currency_api_error(mock_get):
    """Если API упало, функция должна вернуть исходную сумму как резерв"""
    tx = {"amount": 100.0, "currency": "EUR"}
    result = convert_currency(tx)
    assert result == 100.0


@patch("src.views.convert_currency", side_effect=lambda x: x["amount"])
def test_generate_main_page(mock_convert):
    """Тестируем сборку JSON-ответа для главной страницы"""
    data = {
        "Дата операции": ["2021-12-20 12:00:00", "2021-12-21 15:00:00"],
        "Номер карты": ["*1111", "*1111"],
        "Сумма операции": [-1000.0, -2000.0],
        "Валюта операции": ["RUB", "RUB"],
        "Категория": ["Супермаркеты", "Рестораны"],
        "Описание": ["Магнит", "Вкусно и точка"]
    }
    df = pd.DataFrame(data)

    response_str = generate_main_page(df, "2021-12-25 14:00:00")
    res = json.loads(response_str)

    assert res["greeting"] == "Добрый день"
    assert len(res["cards"]) == 1
    assert res["cards"][0]["last_digits"] == "1111"
    assert res["cards"][0]["total_spent"] == 3000.0
    assert res["cards"][0]["cashback"] == 30.0  # 1% от 3000
    assert len(res["top_transactions"]) == 2
