import pytest
import json
from src.services import get_premium_cashback, investment_bank


@pytest.fixture
def sample_transactions():
    """Фикстура с полным форматом даты времени для предотвращения падений парсинга"""
    return [
        {"Дата операции": "2021-12-05 10:00:00", "Сумма операции": -1005.0, "Категория": "Супермаркеты",
         "Статус": "OK"},
        {"Дата операции": "2021-12-10 15:00:00", "Сумма операции": -500.0, "Категория": "Супермаркеты", "Статус": "OK"},
        {"Дата операции": "2021-12-15 18:00:00", "Сумма операции": -250.0, "Категория": "Фастфуд", "Статус": "OK"},
        {"Дата операции": "2021-12-20 20:00:00", "Сумма операции": 5000.0, "Категория": "Пополнение", "Статус": "OK"},
        {"Дата операции": "2021-11-01 12:00:00", "Сумма операции": -1000.0, "Категория": "Супермаркеты", "Статус": "OK"}
    ]


def test_get_premium_cashback(sample_transactions):
    """Проверяем расчет кешбэка за декабрь 2021"""
    result_str = get_premium_cashback(sample_transactions, year=2021, month=12)
    result = json.loads(result_str)

    # Траты декабря в Супермаркетах: 1005 + 500 = 1505 руб -> 15.05 руб кешбэка
    assert result["Супермаркеты"] == 15.05
    assert result["Фастфуд"] == 2.50
    assert "Пополнение" not in result


def test_investment_bank(sample_transactions):
    """Проверяем расчет инвесткопилки"""
    # Округление до 50:
    # 1005.0 -> 1050.0 (копилка +45.0)
    # 500.0  -> 500.0  (копилка +0.0)
    # 250.0  -> 250.0  (копилка +0.0)
    # Итого = 45.0
    saved_money = investment_bank(month="2021-12", transactions=sample_transactions, limit=50)
    assert saved_money == 45.0
