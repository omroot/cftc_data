# CFTC Data

Download and explore CFTC Commitments of Traders (COT) reports via the CFTC public API.

## Project Structure

```
cftc_data/
├── src/                  # Core library
│   ├── cftc_config.py    # Credential loader
│   └── cftc_downloader.py# API client & dataset downloader
├── scripts/              # Standalone analysis scripts
│   ├── compare_disaggregated_cftc_to_aggregated_cot.py
│   ├── compare_disaggregated_cftc_to_disaggregated_cot.py
│   └── generate_column_definitions_of_cftc_disaggregated.py
├── dashboard/            # Dash web application
├── cftc_downloads/       # Downloaded CFTC CSV data (gitignored)
├── cot_data/             # External COT reference data (gitignored)
├── cache/output/         # Script output CSVs (gitignored)
├── .env                  # API credentials (gitignored)
├── .env_template         # Credential template
└── requirements.txt
```

## Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API credentials**

   Copy the template and fill in your CFTC API key:

   ```bash
   cp .env_template .env
   ```

   Edit `.env` with your credentials:

   ```
   CFTC_API_KEY_ID=your_api_key_id_here
   CFTC_API_KEY_SECRET=your_api_key_secret_here
   ```

## Usage

### Download data

Download full history for a specific report type:

```bash
python -m src.cftc_downloader --dataset disaggregated
```

Download incremental updates since a date:

```bash
python -m src.cftc_downloader --dataset disaggregated --since 2025-01-01
```

Available datasets: `disaggregated`, `disaggregated_combined`, `legacy`, `legacy_combined`, `tff`, `tff_combined`.

### Scripts

```bash
python scripts/compare_disaggregated_cftc_to_aggregated_cot.py
python scripts/compare_disaggregated_cftc_to_disaggregated_cot.py
python scripts/generate_column_definitions_of_cftc_disaggregated.py
```

### Dashboard

```bash
python dashboard/app.py
```

## Data Sources

All data is sourced from the [CFTC Public Reporting API](https://publicreporting.cftc.gov).
