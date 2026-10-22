import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from src.utils import read_operations_from_excel


def test_read_operations_from_excel_success():
    """Проверяем успешное чтение файла и замену NaN на None"""
    mock_df = pd.DataFrame({
        "Дата операции": ["2021-12-20", "2021-12-21"],
        "Сумма операции": [-150.0, None]  # Специально передаем NaN
    })

    with patch("pandas.read_excel", return_value=mock_df):
        result = read_operations_from_excel("fake_path.xlsx")

        assert len(result) == 2
        assert result[0]["Сумма операции"] == -150.0
        assert result[1]["Сумма операции"] is None  # NaN успешно заменен на None


def test_read_operations_from_excel_file_not_found():
    """Проверяем поведение, если файла физически нет"""
    with patch("pandas.read_excel", side_effect=FileNotFoundError):
        result = read_operations_from_excel("missing_file.xlsx")
        assert result == []


def test_read_operations_from_excel_error():
    """Проверяем поведение при любой другой непредвиденной ошибке"""
    with patch("pandas.read_excel", side_effect=Exception("Поврежденный файл")):
        result = read_operations_from_excel("corrupted.xlsx")
        assert result == []
