import logging
from typing import Any, Dict, List
import pandas as pd

logger = logging.getLogger(__name__)


def read_operations_from_excel(file_path: str) -> List[Dict[str, Any]]:
    """Считывает данные из Excel-файла с транзакциями
    Возвращает список словарей, где каждый словарь — одна транзакция
    Если файл поврежден или отсутствует, возвращает пустой список
    """
    logger.info(f"Попытка чтения данных из файла: {file_path}")
    try:
        # Читаем excel файл
        df = pd.read_excel(file_path)

        # Заменяем все пустые ячейки на none, чтобы избежать ошибок в json
        df = df.astype(object).where(pd.notnull(df), None)

        # Конвертируем dataframe в список словарей
        transactions = df.to_dict(orient="records")
        logger.info(f"Успешно загружено {len(transactions)} транзакций.")
        return transactions

    except FileNotFoundError:
        logger.error(f"Файл не найден по пути: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Произошла непредвиденная ошибка при чтении Excel: {e}")
        return []
