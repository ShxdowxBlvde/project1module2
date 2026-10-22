import os
import json
import logging
from datetime import datetime
import pandas as pd

from src.utils import read_operations_from_excel
from src.views import generate_main_page
from src.services import get_premium_cashback, investment_bank
from src.reports import spending_by_category

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Жестко привязываем путь к созданной вами папке logs в корне
log_file_path = os.path.join(BASE_DIR, "logs", "../logs/project.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("../logs/project.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Старт приложения.")

    # Подгружаем пользовательские настройки из конфига
    settings_path = "user_settings.json"
    if os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            user_settings = json.load(f)
    else:
        # Дефолтные настройки, если пользователь забыл создать файл
        user_settings = {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "AMZN"],
            "default_category_report": "Супермаркеты",
            "investment_limit": 50
        }
        logger.warning("Конфиг user_settings.json не найден. Взял дефолтные настройки.")

    # Проверяем, на месте ли файл с транзакциями, без него дальше не пройти
    excel_path = "data/operations.xlsx"
    if not os.path.exists(excel_path):
        logger.error(f"Файл данных не найден по пути: {excel_path}!")
        print("Ошибка: Положите Excel-файл с транзакциями в папку data/operations.xlsx")
        return

    # Вытаскиваем сырые транзакции через утилиты
    raw_transactions = read_operations_from_excel(excel_path)
    if not raw_transactions:
        logger.warning("Файл пустой или не удалось прочитать транзакции.")
        return

    # Делаем датафрейм для модулей, которые работают через pandas (views и reports)
    df_transactions = pd.DataFrame(raw_transactions)

    # За базовую точку отсчета берем текущее время запуска программы
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_year = datetime.now().year
    current_month = datetime.now().month
    current_month_str = datetime.now().strftime("%Y-%m")

    print(f"--- Запуск анализа данных на момент: {current_time_str} ---")

    # 1. Генерируем данные для Главной страницы
    logger.info("Формируем данные для главной страницы.")
    main_page_json = generate_main_page(df_transactions, current_time_str)
    print("\n[Ответ Главной страницы (JSON)]:")
    print(main_page_json)

    # 2. Считаем аналитику по сервисам (кешбэк и инвесткопилка)
    logger.info("Запускаем расчеты по сервисам.")

    cashback_analysis = get_premium_cashback(raw_transactions, year=current_year, month=current_month)
    print(f"\n[Анализ повышенного кешбэка за {current_month:02d}.{current_year}]:")
    print(cashback_analysis)

    round_limit = user_settings.get("investment_limit", 50)
    saved_money = investment_bank(month=current_month_str, transactions=raw_transactions, limit=round_limit)
    print(
        f"\n[Инвесткопилка]: За месяц {current_month_str} удалось накопить: {saved_money} руб. (шаг {round_limit} руб.)")

    # 3. Формируем отчет по тратам (декоратор сам создаст JSON-файл на диске)
    logger.info("Генерируем файловый отчет.")
    target_category = user_settings.get("default_category_report", "Супермаркеты")

    report_df = spending_by_category(df_transactions, category=target_category, date=current_time_str)
    print(f"\n[Отчет сформирован]: Данные по категории '{target_category}' за 3 месяца сохранены в корень проекта.")


if __name__ == "__main__":
    main()
