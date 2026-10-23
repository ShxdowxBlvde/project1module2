import json
import logging
import math
from typing import Any, Dict, List
import pandas as pd

logger = logging.getLogger(__name__)


def get_premium_cashback(
    transactions: List[Dict[str, Any]], year: int, month: int
) -> str:
    logger.info(f"считаем повышенный кешбэк за {year}-{month:02d}")
    target_txs = []

    for x in transactions:
        if x.get("Статус") != "OK" or x.get("Сумма операции", 0) >= 0:
            continue
        date_val = x.get("Дата операции")
        if not date_val:
            continue
        try:
            dt = pd.to_datetime(date_val)
            if dt.year == year and dt.month == month:
                target_txs.append(x)
        except Exception:
            continue

    analysis: Dict[str, float] = {}
    for tx in target_txs:
        category = tx.get("Категория", "Разное")
        cashback = abs(tx.get("Сумма операции", 0)) * 0.01
        analysis[category] = round(analysis.get(category, 0.0) + cashback, 2)

    return json.dumps(analysis, ensure_ascii=False)


def investment_bank(
    month: str, transactions: List[Dict[str, Any]], limit: int
) -> float:
    logger.info(f"считаем копилку за {month}")
    monthly_txs = []

    for x in transactions:
        if x.get("Сумма операции", 0) >= 0:
            continue
        date_val = x.get("Дата операции")
        if not date_val:
            continue
        try:
            dt_str = pd.to_datetime(date_val).strftime("%Y-%m")
            if dt_str == month:
                monthly_txs.append(x)
        except Exception:
            continue

    def calc_round_up(amount: float) -> float:
        abs_amount = abs(amount)
        if abs_amount == 0:
            return 0.0
        rounded = math.ceil(abs_amount / limit) * limit
        return round(rounded - abs_amount, 2)

    savings = list(
        map(lambda x: calc_round_up(x.get("Сумма операции", 0)), monthly_txs)
    )
    return round(sum(savings), 2)
