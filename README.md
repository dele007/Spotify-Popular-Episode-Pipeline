# Spotify Popular Podcast Pipeline

## Problem Statement

With thousands of podcasts available across every genre, finding quality content to listen to is overwhelming. This project builds an end-to-end data pipeline that tracks the top English Spotify podcasts, enriches it with genre metadata, and surfaces the most consistently popular shows and standout episodes during a specifed time period on an interactive dashboard. The aim is to provide a way to easily explore popular shows within a genre to aid the podcast
discovery process. Any bad selections after that point is fully on me.

The dashboard answers two questions:
- **What are the most popular podcasts right now?** Ranked by average chart performance across all their episodes and
number of episodes that have made the Top 200 chart.
- **Which episodes of a podcast are worth listening to if you're listening to it for the first time?** Sorted by top chart ranking and filtered by genre, country/region, and show with episode duration.

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
- **Coverage**: Daily top 200 episodes, filtered to only English speaking podcasts, September 2024 to present
- **Volume**: ~1M+ rows updated weekly

## Pipeline

### Ingestion (`data/spotify_pipeline.py`)
1. Downloads latest episode chart data from Kaggle
2. Uploads raw CSV to GCS under `raw/episodes/`
3. Checks GCS for existing show enrichment data
4. Identifies new shows not yet enriched
5. Hits iTunes Search API for genre metadata on new shows
6. Uploads enriched show data to GCS under `raw/shows/`

### Loading (`data/gcs_to_bq.py`)
1. Loads episodes CSV from GCS to BigQuery
   - Partitioned by `date` for efficient date range queries
   - Clustered by `region` and `show_name` for fast filtering
2. Loads shows CSV from GCS to BigQuery

### Transformation (dbt)
See [dbt/README.md](dbt/README.md) for full model documentation.

### Orchestration (Prefect & dbt)
Pipeline runs on a weekly schedule. Each run:
- Downloads latest Kaggle data
- Enriches any new shows via iTunes API
- Loads to BigQuery
- Triggers dbt build an hour after the data gets loaded into BigQuery

## Dashboard

Built in Looker Studio connecting directly to BigQuery mart tables.

**Tile 1 — Most Popular Shows**
- Shows ranked by average best chart position and ranked episodes since September 2024
- Filterable by genre and region
- Ranked episode total acts as as a quality signal and rewards podcasts that have episodes chart frequently 

**Tile 2 — Most Popular Episodes**
- Episodes ordered by release date (latest to earliest)
- Episode's best rank achieved and days charted
- Filterable by show and genre
- Includes episode duration
- Includes countries where popular episdoes have reached the Top 200 daily rank
- Timeline of chart placement during selected timespan

## Setup

### Prerequisites
- Google Cloud account with billing enabled
- Terraform installed
- Python 3.11+ (I setup all of this on 3.14.2, but should be fine with previous versions)
- dbt Cloud account (Maybe Core is okay, I set mine up on Cloud)
- Kaggle account with API token
- Prefect Cloud account

### 1. Clone the repository
```bash
git clone https://github.com/dele007/Spotify-Popular-Episode-Pipeline.git
cd spotify-podcast-pipeline
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Authenticate with GCP
```bash
gcloud auth application-default login
```

### 4. Set environment variables
```bash
export KAGGLE_API_TOKEN="your-kaggle-api-key" (will need to export a key from Kaggle after creating an account)
export PROJECT_ID="your-gcp-project-id"
export BUCKET_NAME="your-bucket-name"
```

### 5. Provision infrastructure
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 6. Run the pipeline manually
```bash
python prefect/orchestration.py
```
### 7. Deploy schedule with Prefect
```bash
prefect cloud login
prefect deploy (Follow the prompts)
```

### 8. Run dbt transformations
**Manually via dbt Cloud**
1. Login to dbt cloud
2. Go to project
3. Make sure it's connected to dbt folder in Github repo
4. Run:
     - dbt run
     - dbt test

**Or if you have dbt Core installed:**
```bash
cd dbt
dbr init
dbt run
dbt test
```
It's possible I left things out through this method since I went the Cloud route.

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
├── prefect/
     ├── orchestration.py
├── requirements.txt
└── README.md
```

## Dashboard
[Spotify Podcast Popularity Dashboard](https://lookerstudio.google.com/reporting/b6e24452-e17c-4632-b995-b49394179f95/page/YhZtF)

## Limitations & Known Issues

- At the moment I can only pull total episodes for a podcast and not just episodes released within the timespan of my data.
Ideally I'd be able to include the rate of episodes that  charted within the timespan as an indicator of a podcast's quality.
- Getting genre data for podcasts was not as straightforward as I'd thought. Given my proficiency with Python and the timeline
of this project, I prioritized a solution that felt economically viable long-term and showed results immediately. Basically
ListenNotes doesn't make it easy to pull info on a free-tier membership (fair), so I needed to pivot.
- iTunes API rate limiting means show genre enrichment is incremental — shows are enriched in batches of 100 in order to make
sure shows that have info pulled are updated before running into rate limits. Shows not yet enriched default to null genre values
in the dashboard so won't be included until the script is run again. Shows that aren't found are labeled as such, so if they later
have info added to iTunes, they won't be added into the data as the code currently exists.
- The Kaggle dataset starts in 2024 so trend analysis is limited to just over a year of data. So popular podcasts that ended before
Sept 2024 (e.g. Reply All) unfortunately won't be included unless they have an old episode resurge.
- Some show names with special characters or emojis may not match correctly in the iTunes API lookup, resulting in missing genre data
for those shows. The function I have that cleans name may not be able to capture edge cases.
- A podcast that has an episode do well in multiple regions/countries, will show up multiple times in the top episodes
table. Unless filtered down to a single country/region, if a timespan is long enough, the table can get overwhelming
and not as useful as intended.
- As mentioned at the top, these are for podcasts that are available in English, as I am a native speaker and designed this with my own
personal use given the constraints on getting genre data. Ideally it would be possible to have language as a filter as well (maybe someday?)
