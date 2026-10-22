import json
import math
import logging
from datetime import datetime
from typing import List, Any, Dict

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_premium_cashback(transactions: List[Dict[str, Any]], year: int, month: int) -> str:
    """
    Анализ кешбэка по категориям за определенный год и месяц.
    Возвращает JSON-строку.
    """
    logger.info(f" Запуск анализа кэшбэка за {year}-{month:02d}")


    target_txs = list(
        filter(
            lambda x: x.get("Статус") == "OK"
            and x.get("Сумма операций", 0) < 0
            and datetime.strptime(x.get("Дата операции", ""), "%Y-%m-%d %H:%M:%S").year == year
            and datetime.strptime(x.get("Дата операции", ""), "%Y-%m-%d %H:%M:%S").month == month,
            transactions,
        )
    )
    analysis: Dict[str, float] = {}
    for tx in target_txs:
        category = tx.get("Категория", "Разное")
        cashback = abs(tx.get("Сумма операций", 0)) * 0.01
        analysis[category] = round(analysis.get(category, 0.0) + cashback, 2)
    return json.dumps(analysis, ensure_ascii=False)


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int):
    """
       Расчет суммы округлений в Инвесткопилку за указанный месяц (YYYY-MM).
    """
    logger.info(f"Расчет инвесткопилки за {month} с лимитом {limit}")
    monthly_txs = list(
        filter(
            lambda x: x.get("Дата операции", "").startswith(month) and x.get("Сумма операции", 0) < 0,
            transactions,
        )
    )
    def calc_round_up(amount: float) -> float:
        abs_amount = abs(amount)
        if abs_amount == 0:
            return 0.0
        rounded = math.ceil(abs_amount / limit) * limit
        return round(rounded - abs_amount, 2)

    savings = list(map(lambda x: calc_round_up(x.get("Сумма операции", 0)), monthly_txs))

    return round(sum(savings), 2)