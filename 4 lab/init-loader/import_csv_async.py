"""
При изначальной разработке проекта данный скрипт предназначался для загрузки данных и запускался из консоли при поднятом сервисе. Сейчас просто заворачиваем в Docker -> Kubernetes
"""

import argparse
import asyncio
from typing import Any, Dict

import httpx
import pandas as pd
from tqdm import tqdm


async def send_rows(rows: list[Dict[str, Any]], api_url: str) -> None:
    """Асинхронно отправляет каждую строку в API, соблюдая порядок."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        pbar = tqdm(total=len(rows), desc="Отправлено строк")
        sent = 0

        for row in rows:
            try:
                response = await client.post(api_url, json=row)
                response.raise_for_status()
            except Exception as e:
                print(f"\nОшибка при отправке строки {row}: {e}")
                break
            else:
                sent += 1
                pbar.update(1)

        pbar.close()
        print(f"\nВсего успешно отправлено: {sent} из {len(rows)}")


async def wait_for_api(api_base: str, retries: int = 30, delay: int = 5) -> bool:
    """Ждёт готовности API."""
    health_url = f"{api_base}/docs"
    async with httpx.AsyncClient() as client:
        for attempt in range(1, retries + 1):
            try:
                response = await client.get(health_url)
                if response.status_code == 200:
                    print(f"API готов после {attempt} попыток")
                    return True
            except Exception as e:
                print(f"Попытка {attempt}/{retries}: API не готов - {e}")
            await asyncio.sleep(delay)
    return False


async def main(csv_path: str, api_url: str) -> None:
    """Загружает CSV в pandas и передаёт строки в send_rows."""
    api_base = api_url.rsplit("/", 1)[0]

    print(f"Ожидание готовности API: {api_base}")
    if not await wait_for_api(api_base):
        print("API не доступен, выход")
        return

    df = pd.read_csv(csv_path, dtype=str).fillna("")
    records = df.to_dict(orient="records")

    await send_rows(records, api_url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Импорт CSV в API из pandas DataFrame последовательно"
    )
    parser.add_argument("--csv", required=True, help="Путь к CSV-файлу для импорта")
    parser.add_argument(
        "--api",
        default="http://business:8000/transactions",
        help="URL API для отправки данных",
    )
    args = parser.parse_args()

    asyncio.run(main(args.csv, args.api))
