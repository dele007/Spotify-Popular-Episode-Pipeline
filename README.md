# Spotify Popular Podcast Pipeline

## Problem Statement

With thousands of podcasts available across every genre, finding quality content to listen to is overwhelming. This project builds an end-to-end data pipeline that tracks daily Spotify podcast chart data across English speaking regions, enriches it with genre metadata, and surfaces the most consistently popular shows and standout episodes through an interactive dashboard.

The dashboard answers two questions:
- **What are the most popular podcasts right now?** Ranked by average chart performance across all their episodes
- **Which recent episodes are worth listening to?** Filtered by genre and show with duration and chart performance context

## Architecture

```
Kaggle API          iTunes API
     │                   │
     ▼                   ▼
Google Cloud Storage (Data Lake)
raw/episodes/       raw/shows/
     │                   │
     ▼                   ▼
BigQuery (Data Warehouse)
podcast_episodes    podcast_shows
     │                   │
     └─────────┬─────────┘
               ▼
            dbt
     (staging → intermediate → marts)
               │
               ▼
        Looker Studio
         (Dashboard)
```

## Technologies

| Layer | Tool |
|---|---|
| Infrastructure as Code | Terraform |
| Cloud Provider | Google Cloud Platform |
| Data Lake | Google Cloud Storage |
| Data Warehouse | BigQuery |
| Ingestion & Enrichment | Python |
| Orchestration | Prefect |
| Transformation | dbt Cloud |
| Dashboard | Looker Studio |

## Dataset

- **Source**: [Top Spotify Podcast Episodes (Daily Updated)](https://www.kaggle.com/datasets/daniilmiheev/top-spotify-podcasts-daily-updated) — Kaggle
- **Enrichment**: iTunes Search API for genre metadata
- **Coverage**: Daily top 200 episodes across English speaking regions, 2024 to present
- **Volume**: ~1M+ rows updated weekly

## Pipeline

### Ingestion (`data/spotify_pipeline.py`)
1. Downloads latest episode chart data from Kaggle
2. Uploads raw CSV to GCS under `raw/episodes/`
3. Checks GCS for existing show enrichment data
4. Identifies new shows not yet enriched
5. Hits iTunes Search API for genre metadata on new shows
6. Uploads enriched show data to GCS under `raw/shows/`

### Loading (`data/load_to_bigquery.py`)
1. Loads episodes CSV from GCS to BigQuery
   - Partitioned by `date` for efficient date range queries
   - Clustered by `region` and `show_name` for fast filtering
2. Loads shows CSV from GCS to BigQuery

### Transformation (dbt)
See [dbt/README.md](dbt/README.md) for full model documentation.

### Orchestration (Prefect)
Pipeline runs on a weekly schedule. Each run:
- Downloads latest Kaggle data
- Enriches any new shows via iTunes API
- Loads to BigQuery
- Triggers dbt run

## Dashboard

Built in Looker Studio connecting directly to BigQuery mart tables.

**Tile 1 — Most Popular Shows**
- Shows ranked by average best chart position
- Filterable by genre and region
- Includes ranked episode rate as a quality signal

**Tile 2 — Recent Popular Episodes**
- Episodes ordered by release date
- Shows best rank achieved and days charted
- Filterable by show and genre
- Includes episode duration

## Setup

### Prerequisites
- Google Cloud account with billing enabled
- Terraform installed
- Python 3.9+
- dbt Cloud account
- Kaggle account with API token

### 1. Clone the repository
```bash
git clone https://github.com/your-username/spotify-podcast-pipeline.git
cd spotify-podcast-pipeline
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Set environment variables
```bash
export GOOGLE_APPLICATION_CREDENTIALS="credentials/your-key.json"
export KAGGLE_USERNAME="your-kaggle-username"
export KAGGLE_KEY="your-kaggle-api-key"
export GCS_BUCKET_NAME="your-bucket-name"
export PROJECT_ID="your-gcp-project-id"
```

### 4. Provision infrastructure
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 5. Run the pipeline
```bash
python data/spotify_pipeline.py
python data/load_to_bigquery.py
```

### 6. Run dbt transformations
```bash
cd dbt
dbt run
dbt test
```

## Project Structure

```
spotify-podcast-pipeline/
├── terraform/
│   ├── main.tf
│   └── variables.tf
├── data/
│   ├── spotify_pipeline.py
│   └── load_to_bigquery.py
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   ├── dbt_project.yml
│   └── README.md
├── requirements.txt
└── README.md
```

## Limitations & Known Issues

- iTunes API rate limiting means show genre enrichment is incremental — shows are enriched in batches of 500 per day. Shows not yet enriched default to null genre values in the dashboard.
- The Kaggle dataset starts in 2024 so trend analysis is limited to approximately one year of data.
- Some show names with special characters or emojis may not match correctly in the iTunes API lookup, resulting in missing genre data for those shows.
