import json
import logging
import os
from datetime import datetime
from functools import wraps
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)

def report_to_file(filename: Optional[str] = None):
    """Декоратор для записи отчетов в json файл"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result_df = func(*args, **kwargs)
            out_file = filename
            if not out_file:
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                out_file = f"report+{func.__name__}_{timestamp}.json"

            result_dict = result_df.to_dict(orient='records')
            with open(out_file, 'w', encoding="utf-8") as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=4)
            logger.info(f"Отчет сохранен в файле: {out_file}")
            return result_df
        return wrapper
    return decorator

@report_to_file
def spending_by_category( transactions: pd.DataFrame, category: str, date: Optional[datetime] = None) -> pd.DataFrame:
    logger.info(f"Формирование отчета по категории{category}")
    if date is None:
        target_date = pd.Timestamp.now()
    else:
        target_date = pd.to_datetime(date)
    start_date = target_date - pd.DateOffset(months=3)
    df = transactions.copy()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])
    filtered_df = df[
        (df["Дата операции"] >= start_date)
        & (df["Дата операции"] <= target_date)
        & (df["Категория"] == category)
        & (df["Сумма операции"] < 0)
    ]
    return filtered_df