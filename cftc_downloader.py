import argparse
import logging
from pathlib import Path

import pandas as pd
import requests

from cftc_config import load_cftc_credentials

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent


DATASETS = {
    "disaggregated": {"id": "72hh-3qpy", "filename": "disaggregated_futures_only.csv"},
    "disaggregated_combined": {"id": "kh3c-gbw2", "filename": "disaggregated_combined.csv"},
    "legacy": {"id": "6dca-aqww", "filename": "legacy_futures_only.csv"},
    "legacy_combined": {"id": "jun7-fc8e", "filename": "legacy_combined.csv"},
    "tff": {"id": "gpe5-46if", "filename": "tff_futures_only.csv"},
    "tff_combined": {"id": "yw9f-hn96", "filename": "tff_combined.csv"},
}


class CFTCDownloader:
    BASE_URL = "https://publicreporting.cftc.gov/resource/{dataset_id}.json"
    PAGE_SIZE = 50_000

    def __init__(self, app_token: str, output_dir: Path, dataset: str = "disaggregated"):
        self.app_token = app_token
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.dataset_info = DATASETS[dataset]
        self.dataset_name = dataset
        self.url = self.BASE_URL.format(dataset_id=self.dataset_info["id"])

    def _fetch_page(self, offset: int, where_clause: str | None = None) -> list[dict]:
        headers = {}
        if self.app_token:
            headers["X-App-Token"] = self.app_token
        params = {
            "$limit": self.PAGE_SIZE,
            "$offset": offset,
            "$order": "report_date_as_yyyy_mm_dd ASC",
        }
        if where_clause:
            params["$where"] = where_clause

        response = requests.get(self.url, headers=headers, params=params, timeout=120)

        # If token causes 403, retry without it (unauthenticated but throttled)
        if response.status_code == 403 and self.app_token:
            logger.warning("App token rejected (403). Retrying without token.")
            self.app_token = None
            headers.pop("X-App-Token", None)
            response = requests.get(self.url, headers=headers, params=params, timeout=120)

        response.raise_for_status()
        return response.json()

    def _fetch_all(self, where_clause: str | None = None) -> pd.DataFrame:
        all_records = []
        offset = 0

        while True:
            logger.info(f"Fetching page at offset {offset}...")
            page = self._fetch_page(offset, where_clause)

            if not page:
                break

            all_records.extend(page)
            logger.info(f"Retrieved {len(page)} records (total: {len(all_records)})")

            if len(page) < self.PAGE_SIZE:
                break

            offset += self.PAGE_SIZE

        if not all_records:
            return pd.DataFrame()

        return pd.DataFrame(all_records)

    def download_full_history(self) -> pd.DataFrame:
        """Download all COT data (2006+)."""
        logger.info(f"Downloading full CFTC {self.dataset_name} history...")
        df = self._fetch_all()
        logger.info(f"Downloaded {len(df)} total records")
        return df

    def download_latest(self, since_date: str) -> pd.DataFrame:
        """Download COT data since a given date (YYYY-MM-DD)."""
        where_clause = f"report_date_as_yyyy_mm_dd > '{since_date}'"
        logger.info(f"Downloading CFTC {self.dataset_name} data since {since_date}...")
        df = self._fetch_all(where_clause)
        logger.info(f"Downloaded {len(df)} records since {since_date}")
        return df

    def save(self, df: pd.DataFrame, filename: str | None = None, merge: bool = False):
        """Save DataFrame to CSV in the output directory.

        If merge=True and the file already exists, append new rows and deduplicate.
        """
        if filename is None:
            filename = self.dataset_info["filename"]
        filepath = self.output_dir / filename
        if merge and filepath.exists():
            existing = pd.read_csv(filepath)
            df = pd.concat([existing, df], ignore_index=True)
            df = df.drop_duplicates()
            df = df.sort_values("report_date_as_yyyy_mm_dd").reset_index(drop=True)
        df.to_csv(filepath, index=False)
        logger.info(f"Saved {len(df)} records to {filepath}")
        return filepath


def update_all_datasets(output_dir: Path, app_token: str) -> dict:
    """Auto-detect the latest date in each dataset and download the delta.

    Returns a dict of {dataset_name: {"new_rows": int, "latest_date": str}}.
    """
    results = {}
    for name, info in DATASETS.items():
        filepath = output_dir / info["filename"]

        # Detect the latest date already on disk
        since_date = None
        if filepath.exists():
            existing = pd.read_csv(filepath, usecols=["report_date_as_yyyy_mm_dd"])
            if not existing.empty:
                since_date = existing["report_date_as_yyyy_mm_dd"].max()[:10]

        downloader = CFTCDownloader(app_token=app_token, output_dir=output_dir, dataset=name)

        if since_date:
            df = downloader.download_latest(since_date)
            if not df.empty:
                downloader.save(df, merge=True)
        else:
            df = downloader.download_full_history()
            if not df.empty:
                downloader.save(df)

        # Read back the latest date after save
        latest = "—"
        if filepath.exists():
            saved = pd.read_csv(filepath, usecols=["report_date_as_yyyy_mm_dd"])
            if not saved.empty:
                latest = saved["report_date_as_yyyy_mm_dd"].max()[:10]

        results[name] = {"new_rows": len(df), "latest_date": latest}

    return results


def main():
    parser = argparse.ArgumentParser(description="Download CFTC COT data")
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Download data since this date (YYYY-MM-DD). If omitted, downloads full history.",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        choices=list(DATASETS.keys()),
        default="disaggregated",
        help="Which CFTC report to download (default: disaggregated).",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    creds_path = ROOT_DIR / "cftc_api_info"
    credentials = load_cftc_credentials(creds_path)
    output_dir = ROOT_DIR / "cftc_downloads"

    downloader = CFTCDownloader(
        app_token=credentials["key_id"],
        output_dir=output_dir,
        dataset=args.dataset,
    )

    if args.since:
        df = downloader.download_latest(args.since)
        downloader.save(df, merge=True)
    else:
        df = downloader.download_full_history()
        downloader.save(df)


if __name__ == "__main__":
    main()
