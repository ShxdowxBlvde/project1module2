import pytest
from unittest.mock import patch, MagicMock
from src.main import main


@patch("os.path.exists")
@patch("builtins.open")
@patch("src.main.read_operations_from_excel")
@patch("src.main.generate_main_page")
@patch("src.main.get_premium_cashback")
@patch("src.main.investment_bank")
@patch("src.main.spending_by_category")
def test_main_flow_success(
        mock_spending,
        mock_investment,
        mock_cashback,
        mock_generate_page,
        mock_read_excel,
        mock_open,
        mock_exists
):
    """
    Проверяем сквозной сценарий main():
    все ключевые функции должны вызваться по одному разу в правильном порядке
    """
    # Имитируем, что конфиги и файлы данных существуют
    mock_exists.return_value = True

    # Имитируем успешное чтение настроек из user_settings.json
    mock_file = MagicMock()
    mock_file.__enter__.return_value.read.return_value = '{"investment_limit": 50, "default_category_report": "Супермаркеты"}'
    mock_open.return_value = mock_file

    # Имитируем возвращаемое значение из Excel
    mock_read_excel.return_value = [
        {"Дата операции": "2021-12-20 12:00:00", "Сумма операции": -100.0, "Категория": "Супермаркеты"}
    ]

    # Ставим заглушки на тяжелую логику, чтобы просто проверить факт вызова
    mock_generate_page.return_value = "{}"
    mock_cashback.return_value = "{}"
    mock_investment.return_value = 0.0

    # Запускаем main()
    main()

    # Проверяем, что утилита чтения Excel была вызвана для нужного файла
    mock_read_excel.assert_called_once_with("data/operations.xlsx")

    # Проверяем, что сработали генерация страниц, сервисы и отчеты
    mock_generate_page.assert_called_once()
    mock_cashback.assert_called_once()
    mock_investment.assert_called_once()
    mock_spending.assert_called_once()


@patch("os.path.exists")
def test_main_missing_excel(mock_exists):
    """
    Проверяем сценарий, когда Excel-файла нет на месте
    Программа должна залогировать ошибку и прервать выполнение без падения
    """
    # Имитируем, что файла с транзакциями не существует
    mock_exists.return_value = False

    with patch("src.main.read_operations_from_excel") as mock_read_excel:
        main()
        # Функция чтения Excel не должна даже вызываться
        mock_read_excel.assert_not_called()
