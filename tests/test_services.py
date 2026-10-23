import pytest
import json
from src.services import get_premium_cashback, investment_bank


@pytest.fixture
def sample_transactions():
    return [
        {"Дата операции": "2021-12-05 10:00:00", "Сумма операции": -1005.0, "Категория": "Супермаркеты",
         "Статус": "OK"},
        {"Дата операции": "2021-12-10 15:00:00", "Сумма операции": -500.0, "Категория": "Супермаркеты", "Статус": "OK"},
        {"Дата операции": "2021-12-15 18:00:00", "Сумма операции": -250.0, "Категория": "Фастфуд", "Статус": "OK"},
        {"Дата операции": "2021-12-20 20:00:00", "Сумма операции": 5000.0, "Категория": "Пополнение", "Статус": "OK"}
    ]


def test_get_premium_cashback(sample_transactions):
    result_str = get_premium_cashback(sample_transactions, year=2021, month=12)
    result = json.loads(result_str)

    # 1005 + 500 = 1505 руб расходов -> 15.05 руб кешбэка
    assert result["Супермаркеты"] == 15.05
    assert result["Фастфуд"] == 2.50


def test_investment_bank(sample_transactions):
    # копилка с шагом 50:
    # 1005.0 округляется до 1050 (+45.0)
    # 500.0 и 250.0 уже кратны 50 (+0)
    saved_money = investment_bank(month="2021-12", transactions=sample_transactions, limit=50)
    assert saved_money == 45.0
