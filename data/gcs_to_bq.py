from google.cloud import bigquery

PROJECT_ID = "spotify-episode-pipeline"
BUCKET_NAME = "spotify_podcast_bucket"
EPISODES_GCS_PATH = "raw/episodes/top_podcasts.csv"
SHOWS_GCS_PATH = "raw/shows/shows.csv"
EPISODES_DATASET = "podcast_episodes"
SHOWS_DATASET = "podcast_shows"
EPISODES_TABLE = "raw_episodes"
SHOWS_TABLE = "raw_shows"


def load_to_bigquery(gcs_uri, dataset_id, table_id):
    client = bigquery.Client(project=PROJECT_ID)
    
    job_config = bigquery.LoadJobConfig(
        autodetect=True,
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,  # skip header row
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        max_bad_records=100  # tolerate up to 100 malformed rows
    )
    
    destination = f"{PROJECT_ID}.{dataset_id}.{table_id}"
    
    load_job = client.load_table_from_uri(
        gcs_uri,
        destination,
        job_config=job_config
    )
    
    load_job.result()  # wait for job to complete
    print(f"Loaded {gcs_uri} to {destination}")


def main ():
    load_to_bigquery(
        f"gs://{BUCKET_NAME}/{EPISODES_GCS_PATH}",
        EPISODES_DATASET,
        EPISODES_TABLE
        )

    load_to_bigquery(
        f"gs://{BUCKET_NAME}/{SHOWS_GCS_PATH}",
        SHOWS_DATASET,
        SHOWS_TABLE
    )


if __name__ == "__main__":
    main()
        


