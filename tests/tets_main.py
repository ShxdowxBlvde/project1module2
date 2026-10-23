import pytest
from unittest.mock import patch, MagicMock
from src.main import main


@patch("pathlib.Path.exists")
@patch("builtins.open")
@patch("src.main.read_operations_from_excel")
@patch("src.main.generate_main_page")
@patch("src.main.get_premium_cashback")
@patch("src.main.investment_bank")
@patch("src.main.spending_by_category")
def test_main_flow(
        mock_spending, mock_investment, mock_cashback,
        mock_generate, mock_read_excel, mock_open, mock_exists
):
    # имитируем что все файлы найдены
    mock_exists.return_value = True

    # имитируем загрузку user_settings.json
    mock_file = MagicMock()
    mock_file.__enter__.return_value.read.return_value = '{"investment_limit": 50}'
    mock_open.return_value = mock_file

    # имитируем одну транзакцию из экселя
    mock_read_excel.return_value = [
        {"Дата операции": "2021-12-20 12:00:00", "Сумма операции": -100.0, "Категория": "Супермаркеты"}
    ]

    mock_generate.return_value = "{}"
    mock_cashback.return_value = "{}"
    mock_investment.return_value = 0.0

    main()

    # проверяем что все модули были вызваны цепочкой
    mock_read_excel.assert_called_once()
    mock_generate.assert_called_once()
    mock_cashback.assert_called_once()
    mock_investment.assert_called_once()
    mock_spending.assert_called_once()
