from google.cloud import bigquery

PROJECT_ID = "spotify-episode-pipeline"
BUCKET_NAME = "spotify_podcast_bucket"
EPISODES_GCS_PATH = "raw/episodes/top_podcasts.csv"
SHOWS_GCS_PATH = "raw/shows/shows.csv"
EPISODES_DATASET = "podcast_episodes"
SHOWS_DATASET = "podcast_shows"
EPISODES_TABLE = "raw_episodes"
SHOWS_TABLE = "raw_shows"



def load_to_bigquery(gcs_uri, dataset_id, table_id, partition_field=None, clustering_fields=None):
    client = bigquery.Client(project=PROJECT_ID)
    
    job_config = bigquery.LoadJobConfig(
        autodetect=True,
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1, # skip header row
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        max_bad_records=100 # tolerate up to 100 malformed rows
    )
    
    if partition_field: #partitioning is optional, only set if partition_field is provided
        job_config.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field=partition_field
        )
    
    if clustering_fields: #clustering is optional, only set if clustering_fields are provided
        job_config.clustering_fields = clustering_fields
    
    destination = f"{PROJECT_ID}.{dataset_id}.{table_id}" #fully qualified table name
    load_job = client.load_table_from_uri(gcs_uri, destination, job_config=job_config)
    load_job.result() # wait for job to complete
    print(f"Loaded {gcs_uri} to {destination}") #confirm where the file ended up


def main ():
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


if __name__ == "__main__":
    main()
        


