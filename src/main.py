import json
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd

from src.utils import read_operations_from_excel
from src.views import generate_main_page
from src.services import get_premium_cashback, investment_bank
from src.reports import spending_by_category

ROOT_DIR = Path(__file__).resolve().parent.parent
settings_path = ROOT_DIR / "user_settings.json"
excel_path = ROOT_DIR / "data" / "operations.xls"
log_file_path = ROOT_DIR / "logs" / "project.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler(log_file_path, encoding="utf-8")],
)
logger = logging.getLogger(__name__)


def render_dashboard(
    main_page_json_str: str, cashback_json_str: str, saved_money: float, step: int
):
    data = json.loads(main_page_json_str)
    cashback_data = json.loads(cashback_json_str)

    print("\n" + "=" * 60)
    print(f" Направление: ГЛАВНАЯ СТРАНИЦА | {data.get('greeting', 'Привет')}!")
    print("=" * 60)

    print("\n Состояние счетов и карт:")
    print("-" * 40)
    for card in data.get("cards", []):
        print(f"  • Карта *{card['last_digits']}:")
        print(f"    Потрачено: {card['total_spent']:,.2f} руб")
        print(f"    Кешбэк:    {card['cashback']:,.2f} руб")
        print("-" * 40)

    print("\n ТОП-5 КРУПНЫХ ОПЕРАЦИЙ:")
    print("-" * 60)
    for i, tx in enumerate(data.get("top_transactions", []), 1):
        print(f"  {i}. {tx['date']} | {tx['amount']:,.2f} руб | {tx['category']}")
        print(f"     Описание: {tx['description']}")
        print("-" * 60)

    print("\n АНАЛИТИКА ПО СЕРВИСАМ:")
    print("=" * 60)

    print(
        f"  [Инвесткопилка] Накоплено за месяц: {saved_money:,.2f} руб (округление до {step} руб)"
    )
    print("-" * 60)

    # ВОТ ЭТОТ БЛОК ВОЗВРАЩАЕМ:
    print("  [Повышенный кешбэк по категориям]:")
    if cashback_data:
        for cat, amt in cashback_data.items():
            print(f"    • {cat}: {amt:,.2f} руб")
    else:
        print("    Траты по категориям повышенного кешбэка отсутствуют")

    print("-" * 60)
    print("  [Курсы валют]  ", end="")
    curr_line = [
        f"{c['currency']}: {c['rate']} руб" for c in data.get("currency_rates", [])
    ]
    print(" | ".join(curr_line))

    print("  [Акции S&P500] ", end="")
    stock_line = [f"{s['stock']}: ${s['price']}" for s in data.get("stock_prices", [])]
    print(" | ".join(stock_line))

    print("=" * 60 + "\n")


def main():
    logger.info("старт проекта")

    if settings_path.exists():
        with open(settings_path, "r", encoding="utf-8") as f:
            user_settings = json.load(f)
    else:
        user_settings = {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "AMZN"],
            "default_category_report": "Супермаркеты",
            "investment_limit": 50,
        }

    if not excel_path.exists():
        logger.error(f"файл не найден: {excel_path}")
        return

    raw_transactions = read_operations_from_excel(str(excel_path))
    if not raw_transactions:
        logger.warning("транзакций нет")
        return

    df_transactions = pd.DataFrame(raw_transactions)

    system_now = datetime.now()
    greeting_time_str = system_now.strftime("%Y-%m-%d %H:%M:%S")

    df_transactions["Дата операции"] = pd.to_datetime(df_transactions["Дата операции"])
    max_excel_date = df_transactions["Дата операции"].max()

    current_year = max_excel_date.year
    current_month = max_excel_date.month
    current_month_str = max_excel_date.strftime("%Y-%m")

    main_page_json = generate_main_page(df_transactions, greeting_time_str)

    print("\n" + ">" * 20 + " ДЕМОНСТРАЦИЯ ТРЕБУЕМОГО JSON ОТВЕТА СТРАНИЦЫ " + "<" * 20)
    print(main_page_json)
    print(">" * 60 + "\n")

    cashback_analysis = get_premium_cashback(
        raw_transactions, year=current_year, month=current_month
    )

    round_limit = user_settings.get("investment_limit", 50)
    saved_money = investment_bank(
        month=current_month_str, transactions=raw_transactions, limit=round_limit
    )

    render_dashboard(main_page_json, cashback_analysis, saved_money, round_limit)

    target_category = user_settings.get("default_category_report", "Супермаркеты")
    spending_by_category(
        df_transactions, category=target_category, date=greeting_time_str
    )
    logger.info("отчет успешно сохранен в файл")


if __name__ == "__main__":
    main()
