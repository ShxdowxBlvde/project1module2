import json
import logging
from datetime import datetime
from functools import wraps
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


def report_to_file(filename: Optional[str] = None):
    """Декоратор для записи результатов отчета в JSON-файл.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result_df = func(*args, **kwargs)
            out_file = filename

            if not out_file:
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                out_file = f"report_{func.__name__}_{timestamp}.json"

            # Спасаем JSON от ошибки сериализации Timestamp
            df_to_save = result_df.copy()
            for col in df_to_save.columns:
                # Если колонка содержит даты, принудительно переводим в строки
                if pd.api.types.is_datetime64_any_dtype(df_to_save[col]):
                    df_to_save[col] = df_to_save[col].dt.strftime("%Y-%m-%d %H:%M:%S")

            # Превращаем DataFrame в список обычных питоновских словарей
            result_dict = df_to_save.to_dict(orient="records")

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=4)

            logger.info(f"Отчет успешно сохранен в файл: {out_file}")
            return result_df

        return wrapper

    return decorator


@report_to_file()  # Фиксируем вызов со скобками
def spending_by_category(
        transactions: pd.DataFrame, category: str, date: Optional[str] = None
) -> pd.DataFrame:
    """Возвращает траты по заданной категории за последние три месяца"""
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
