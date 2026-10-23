import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from src.main import main


@patch("pathlib.Path.exists")
@patch("builtins.open")
@patch("src.main.read_operations_from_excel")
@patch("src.main.generate_main_page")
@patch("src.main.get_premium_cashback")
@patch("src.main.investment_bank")
@patch("src.main.spending_by_category")
def test_main_flow_success(
        mock_spending, mock_investment, mock_cashback,
        mock_generate, mock_read_excel, mock_open, mock_exists
):
    # имитируем, что конфиги и файлы данных существуют
    mock_exists.return_value = True

    # имитируем успешное чтение настроек из user_settings.json
    mock_file = MagicMock()
    mock_file.__enter__.return_value.read.return_value = '{"investment_limit": 50, "default_category_report": "Супермаркеты"}'
    mock_open.return_value = mock_file

    # имитируем возвращаемое значение из Excel (одна транзакция)
    mock_read_excel.return_value = [
        {"Дата операции": "2021-12-20 12:00:00", "Сумма операции": -100.0, "Категория": "Супермаркеты"}
    ]

    mock_generate.return_value = "{}"
    mock_cashback.return_value = "{}"
    mock_investment.return_value = 0.0

    main()

    # проверяем, что все ключевые модули были вызваны по цепочке
    mock_read_excel.assert_called_once()
    mock_generate.assert_called_once()
    mock_cashback.assert_called_once()
    mock_investment.assert_called_once()
    mock_spending.assert_called_once()


@patch("pathlib.Path.exists")
def test_main_missing_excel(mock_exists):
    # имитируем, что файла с транзакциями нет на месте

    mock_exists.side_effect = [True, False]

    with patch("src.main.read_operations_from_excel") as mock_read_excel:
        main()
        # функция чтения Excel не должна вызываться при отсутствии файла
        mock_read_excel.assert_not_called()


@patch("pathlib.Path.exists")
@patch("src.main.read_operations_from_excel")
def test_main_empty_excel(mock_read_excel, mock_exists):
    # имитируем, что файлы есть, но из экселя вернулся пустой список
    mock_exists.return_value = True
    mock_read_excel.return_value = []

    with patch("src.main.generate_main_page") as mock_generate:
        main()
        # генерация страницы должна прерваться
        mock_generate.assert_not_called()
