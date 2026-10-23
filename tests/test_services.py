import pytest
import json
from src.services import get_premium_cashback, investment_bank


@pytest.fixture
def sample_transactions():
    return [
        {
            "Дата операции": "2021-12-05 10:00:00",
            "Сумма операции": -1005.0,
            "Категория": "Супермаркеты",
            "Статус": "OK",
        },
        {
            "Дата операции": "2021-12-10 15:00:00",
            "Сумма операции": -500.0,
            "Категория": "Супермаркеты",
            "Статус": "OK",
        },
        {
            "Дата операции": "2021-12-15 18:00:00",
            "Сумма операции": -250.0,
            "Категория": "Фастфуд",
            "Статус": "OK",
        },
        {
            "Дата операции": "2021-12-20 20:00:00",
            "Сумма операции": 5000.0,
            "Категория": "Пополнение",
            "Статус": "OK",
        },
        {
            "Дата операции": "битая_дата",
            "Сумма операции": -100.0,
            "Категория": "Супермаркеты",
            "Статус": "OK",
        },
        {
            "Дата операции": "2021-12-05 10:00:00",
            "Сумма операции": -100.0,
            "Категория": "Супермаркеты",
            "Статус": "FAILED",
        },
        {
            "Дата операции": None,
            "Сумма операции": -100.0,
            "Категория": "Супермаркеты",
            "Статус": "OK",
        },
    ]


def test_get_premium_cashback(sample_transactions):
    result_str = get_premium_cashback(sample_transactions, year=2021, month=12)
    result = json.loads(result_str)
    assert result["Супермаркеты"] == 15.05
    assert result["Фастфуд"] == 2.50


def test_investment_bank(sample_transactions):
    saved_money = investment_bank(
        month="2021-12", transactions=sample_transactions, limit=50
    )
    assert saved_money == 45.0


def test_get_premium_cashback_empty_list():
    # Проверяем сервис кешбэка на пустом списке
    result = get_premium_cashback([], year=2021, month=12)
    assert json.loads(result) == {}


def test_investment_bank_no_matching_month():
    # Проверяем инвесткопилку, если в указанном месяце нет трат
    txs = [
        {
            "Дата операции": "2021-11-05 10:00:00",
            "Сумма операции": -1005.0,
            "Категория": "Супермаркеты",
            "Статус": "OK",
        }
    ]
    saved_money = investment_bank(month="2021-12", transactions=txs, limit=50)
    assert saved_money == 0.0


@pytest.mark.parametrize(
    "amount, limit, expected",
    [
        (-100.0, 50, 0.0),
        (-101.0, 50, 49.0),
        (-149.0, 50, 1.0),
        (0.0, 50, 0.0),
    ],
)
def test_investment_bank_math(limit, amount, expected):

    txs = [
        {
            "Дата операции": "2021-12-01 00:00:00",
            "Сумма операции": amount,
            "Статус": "OK",
        }
    ]
    saved = investment_bank(month="2021-12", transactions=txs, limit=limit)
    assert saved == expected
