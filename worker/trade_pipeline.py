import logging
from pathlib import Path

import httpx
import pandas as pd

from app.core.logging import setup_logging
from app.core.settings import settings

logger = logging.getLogger("crypto_flow.worker.trade_pipeline")

OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)


class BinanceWorker:
    """Worker responsible for fetching, transforming, and saving trade data from Binance."""  # noqa: E501

    def __init__(self) -> None:
        self.client = httpx.Client(base_url=settings.binance_base_url, timeout=10)

    def fetch_data(
        self, endpoint: str, params: dict[str, str | int] | None = None
    ) -> list | None:
        logger.info(f"Starting request | endpoint={endpoint} | params={params}")
        try:
            response = self.client.get(endpoint, params=params)
            response.raise_for_status()
            logger.info(f"Request finished | status={response.status_code}")
            return response.json()
        except httpx.TimeoutException:
            logger.error(f"Timeout accessing {endpoint}")
        except httpx.ConnectError:
            logger.error(f"Connection error accessing {endpoint}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error | status={e.response.status_code} | body={e.response.text}")  # noqa: E501
        except Exception:
            logger.exception("Unexpected error in fetch_data")
        return None

    def transform(self, raw_data: list, symbol: str) -> pd.DataFrame:
        logger.info(f"Starting transformation | symbol={symbol} | records={len(raw_data)}") # noqa: E501
        df = pd.DataFrame(raw_data)

        df["price"] = df["price"].astype(float)
        df["qty"] = df["qty"].astype(float)
        df["quoteQty"] = df["quoteQty"].astype(float)
        df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
        df = df.rename(columns={
            "id": "trade_id",
            "qty": "quantity",
            "quoteQty": "quote_quantity",
            "isBuyerMaker": "is_buyer_maker",
            "isBestMatch": "is_best_match",
        })
        df["symbol"] = symbol
        logger.info(f"Transformation finished | symbol={symbol} | shape={df.shape}")
        return df

    def save(self, df: pd.DataFrame, filename: str) -> None:
        """Temporary persistence, gonna be replaced by Postgres via repository."""
        filepath = OUTPUT_DIR / filename
        try:
            df_excel = df.copy()
            df_excel["time"] = df_excel["time"].dt.tz_localize(None)
            df_excel.to_excel(filepath, index=False)
            logger.info(f"Data saved | file={filepath} | records={len(df)}")
        except Exception:
            logger.exception(f"Failed to save file {filepath}")

    def run(self) -> None:
        logger.info("Ingestion started")
        total_records = 0

        for symbol in settings.binance_symbols:
            raw = self.fetch_data(
                "/trades",
                params={"symbol": symbol, "limit": settings.binance_limit},
            )
            if raw is None:
                logger.warning(f"No data for {symbol}. Skipping.")
                continue

            df = self.transform(raw, symbol)
            self.save(df, filename=f"trades_{symbol}.xlsx")
            total_records += len(df)

        logger.info(f"Ingestion finished | total_records={total_records}")
        self.client.close()


if __name__ == "__main__":
    setup_logging()
    worker = BinanceWorker()
    worker.run()