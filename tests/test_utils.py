import pytest
from unittest.mock import patch
import pandas as pd
from src.utils import read_operations_from_excel


def test_read_operations_from_excel_success():
    # имитируем таблицу с датой и пустым значением (NaN)
    mock_df = pd.DataFrame({
        "Дата операции": ["2021-12-20 12:00:00"],
        "Сумма операции": [-150.0],
        "Категория": [None]
    })

    with patch("pandas.read_excel", return_value=mock_df):
        result = read_operations_from_excel("fake_path.xls")

        assert len(result) == 1
        assert result[0]["Сумма операции"] == -150.0
        assert result[0]["Категория"] is None  # NaN успешно заменен на None
        assert result[0]["Дата операции"] == "2021-12-20 12:00:00"


def test_read_operations_from_excel_file_not_found():
    with patch("pandas.read_excel", side_effect=FileNotFoundError):
        result = read_operations_from_excel("missing_file.xls")
        assert result is None
