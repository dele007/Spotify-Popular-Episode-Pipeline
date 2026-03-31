from prefect import task, flow
from prefect.schedules.schedules import CronSchedule


import sys
sys.path.append("data/")

from spotify_pipeline import download_from_kaggle, upload_episodes_to_gcs, get_existing_shows, get_new_shows, get_itunes_info, enrich_shows, load_episodes_from_gcs
from gcs_to_bq import BUCKET_NAME, EPISODES_GCS_PATH, EPISODES_DATASET, EPISODES_TABLE, SHOWS_GCS_PATH, SHOWS_DATASET, SHOWS_TABLE, load_to_bigquery

import os


# Run the flow every Monday at 12:00 AM
weekly_schedule = CronSchedule(cron="0 0 * * 1")

KAGGLE_API_TOKEN = os.getenv("KAGGLE_API_TOKEN")
if not KAGGLE_API_TOKEN:
    raise ValueError("KAGGLE_API_TOKEN environment variable is not set.")

@task(log_prints=True)
def ingest_episodes():
    result = download_from_kaggle()
    upload_episodes_to_gcs(result)
    return result

@task(log_prints=True)
def enrich_show_data():
    episodes_df = load_episodes_from_gcs()
    existing_shows_df = get_existing_shows()
    show_list = get_new_shows(episodes_df, existing_shows_df)
    if len(show_list) == 0:
        print("No new shows found")
        return None, None
    enrich_shows(show_list, existing_shows_df, batch_size=100)
  
@task(log_prints=True)
def load_to_bq():
    load_to_bigquery(
        f"gs://{BUCKET_NAME}/{EPISODES_GCS_PATH}",
        EPISODES_DATASET,
        EPISODES_TABLE,
        partition_field="date",
        clustering_fields=["region", "show_name"]
)

    load_to_bigquery(
        f"gs://{BUCKET_NAME}/{SHOWS_GCS_PATH}",
        SHOWS_DATASET,
        SHOWS_TABLE
    )

@flow(name="Spotify Podcast Pipeline", schedule=weekly_schedule)
def spotify_pipeline_flow():
    ingest_episodes()
    enrich_show_data()
    load_to_bq()

if __name__ == "__main__":
    spotify_pipeline_flow()