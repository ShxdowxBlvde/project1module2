import json
import logging
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


def report_to_file(filename: Optional[str] = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result_df = func(*args, **kwargs)

            current_file_dir = Path(__file__).resolve().parent
            root_project_dir = current_file_dir.parent
            target_logs_dir = root_project_dir / "logs"

            # Жестко создаем папку logs в корне, если её стерли
            target_logs_dir.mkdir(exist_ok=True)

            # Формируем имя файла
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                out_path = target_logs_dir / f"report_{func.__name__}_{timestamp}.json"
            else:
                out_path = target_logs_dir / filename

            # Логируем для проверки в единственный файл project.log
            logger.info(f"декоратор записывает отчет по пути: {out_path}")

            df_to_save = result_df.copy()
            for col in df_to_save.columns:
                if pd.api.types.is_datetime64_any_dtype(df_to_save[col]):
                    df_to_save[col] = df_to_save[col].dt.strftime("%Y-%m-%d %H:%M:%S")

            result_dict = df_to_save.to_dict(orient="records")

            # Чистим от невалидных для JSON значений NaN
            for row in result_dict:
                for key, val in row.items():
                    if pd.isna(val):
                        row[key] = None

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=4)

            return result_df

        return wrapper

    return decorator


@report_to_file()
def spending_by_category(
    transactions: pd.DataFrame, category: str, date: Optional[str] = None
) -> pd.DataFrame:
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
