import pytest
import json
import pandas as pd
from pathlib import Path
from src.reports import spending_by_category
from unittest.mock import patch

def test_spending_by_category_filtering():
    data = {
        "Дата операции": ["2021-12-20 10:00:00", "2021-08-01 09:00:00"],
        "Категория": ["Супермаркеты", "Супермаркеты"],
        "Сумма операции": [-100.0, -300.0]
    }
    df = pd.DataFrame(data)

    # за 3 месяца от декабря останется только первая транзакция
    result_df = spending_by_category(df, category="Супермаркеты", date="2021-12-22 00:00:00")

    assert len(result_df) == 1
    assert -100.0 in result_df["Сумма операции"].values
    assert -300.0 not in result_df["Сумма операции"].values


def test_decorator_saves_to_logs_and_cleans_nan(tmp_path):
    data = {
        "Дата операции": ["2021-12-20 12:00:00"],
        "Категория": ["Супермаркеты"],
        "Сумма операции": [-100.0],
        "Кешбэк": [float("nan")]
    }
    df = pd.DataFrame(data)
    test_file = tmp_path / "test_report.json"

    with patch("builtins.open", return_value=open(test_file, "w", encoding="utf-8")):
        spending_by_category(df, category="Супермаркеты", date="2021-12-22 00:00:00")

    assert test_file.exists()

    file_content = test_file.read_text(encoding="utf-8")
    saved_data = json.loads(file_content.replace("NaN", "null"))

    assert saved_data[0]["Кешбэк"] is None