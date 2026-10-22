import pytest
import os
import json
import pandas as pd
from src.reports import spending_by_category


def test_spending_by_category_filtering():
    """Проверяем фильтрацию по диапазону дат и категории расходов"""
    data = {
        "Дата операции": ["2021-12-20 10:00:00", "2021-11-15 14:00:00", "2021-08-01 09:00:00", "2021-12-21 18:00:00"],
        "Категория": ["Супермаркеты", "Супермаркеты", "Супермаркеты", "Фастфуд"],
        "Сумма операции": [-100.0, -200.0, -300.0, -400.0]
    }
    df = pd.DataFrame(data)

    # Период за 3 месяца от 2021-12-22: с 2021-09-22 по 2021-12-22
    result_df = spending_by_category(df, category="Супермаркеты", date="2021-12-22 00:00:00")

    assert len(result_df) == 2
    assert -100.0 in result_df["Сумма операции"].values
    assert -200.0 in result_df["Сумма операции"].values
    assert -300.0 not in result_df["Сумма операции"].values  # Слишком старая
    assert -400.0 not in result_df["Сумма операции"].values  # Другая категория


def test_decorator_creates_file():
    """Проверяем, что декоратор без проблем создает JSON и не падает на Timestamp."""
    data = {
        "Дата операции": ["2021-12-20 12:30:15"],
        "Категория": ["Супермаркеты"],
        "Сумма операции": [-150.0]
    }
    df = pd.DataFrame(data)


    for file in os.listdir("."):
        if file.startswith("report_spending_by_category_") and file.endswith(".json"):
            os.remove(file)


    spending_by_category(df, category="Супермаркеты", date="2021-12-22 00:00:00")

    # Ищем созданный файл
    report_file = None
    for file in os.listdir("."):
        if file.startswith("report_spending_by_category_") and file.endswith(".json"):
            report_file = file
            break

    assert report_file is not None, "Декоратор не создал файл отчета"

    # Проверяем, что внутри лежит валидный JSON без ошибок сериализации
    with open(report_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
        assert len(saved_data) == 1
        assert saved_data[0]["Сумма операции"] == -150.0
        assert saved_data[0]["Дата операции"] == "2021-12-20 12:30:15"


    os.remove(report_file)
