import json
import math
import logging
from datetime import datetime
from typing import List, Any, Dict

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from datetime import datetime
import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def get_premium_cashback(transactions: List[Dict[str, Any]], year: int, month: int) -> str:
    """Анализ кешбэка по категориям за определенный год и месяц"""
    logger.info(f"Запуск анализа кешбэка за {year}-{month:02d}")

    target_txs = []
    for x in transactions:
        # Проверяем базовые условия статуса и расхода
        if x.get("Статус") != "OK" or x.get("Сумма операции", 0) >= 0:
            continue

        date_val = x.get("Дата операции")
        if not date_val:
            continue

        try:

            date_str = str(date_val).strip()[:10]
            dt = datetime.strptime(date_str, "%Y-%m-%d")

            # Проверяем совпадение по году и месяцу
            if dt.year == year and dt.month == month:
                target_txs.append(x)
        except Exception as e:
            logger.warning(f"Не удалось распарсить дату транзакции '{date_val}': {e}")
            continue

    analysis: Dict[str, float] = {}
    for tx in target_txs:
        category = tx.get("Категория", "Разное")

        cashback = abs(tx.get("Сумма операции", 0)) * 0.01
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