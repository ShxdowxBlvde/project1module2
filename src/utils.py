import logging
from typing import Any, Dict, List
import pandas as pd

logger = logging.getLogger(__name__)

def read_operations_from_excel(file_path: str) -> List[Dict[str, Any]]:
    logger.info(f"читаем эксель: {file_path}")
    try:
        df = pd.read_excel(file_path, engine="xlrd")

        # сначала приводим даты к нормальному виду пока они не стали object
        if "Дата операции" in df.columns:
            df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="mixed")
            df["Дата операции"] = df["Дата операции"].dt.strftime("%Y-%m-%d %H:%M:%S")

        # теперь безопасно меняем NaN на None для json
        df = df.astype(object).where(pd.notnull(df), None)

        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"не удалось прочитать файл: {e}")
        return
