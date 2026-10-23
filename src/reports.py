import json
import logging
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)

# находим корень проекта (на один уровень выше папки src)
ROOT_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT_DIR / "logs"

def report_to_file(filename: Optional[str] = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result_df = func(*args, **kwargs)
            out_file = filename

            if not out_file:
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                # принудительно сохраняем файл в корень проекта
                out_path = ROOT_DIR / f"report_{func.__name__}_{timestamp}.json"
            else:
                out_path = ROOT_DIR / out_file

            df_to_save = result_df.copy()
            for col in df_to_save.columns:
                if pd.api.types.is_datetime64_any_dtype(df_to_save[col]):
                    df_to_save[col] = df_to_save[col].dt.strftime("%Y-%m-%d %H:%M:%S")

            result_dict = df_to_save.to_dict(orient="records")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=4)

            logger.info(f"отчет успешно сохранен по пути: {out_path}")
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
