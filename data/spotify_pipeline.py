
import os
import io
import re
import time
import kagglehub
import requests
import pandas as pd
from google.cloud import storage
from google.cloud import bigquery
from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError


def download_from_kaggle():
  download_path = kagglehub.dataset_download('daniilmiheev/top-spotify-podcasts-daily-updated')
  files = os.listdir(download_path)
  csv_file = [f for f in files if f.endswith('.csv')][0]
  full_path = os.path.join(download_path, csv_file)
  print(full_path)
  return full_path


PROJECT_ID = "spotify-episode-pipeline"
BUCKET_NAME = "spotify_podcast_bucket"
EPISODES_GCS_PATH = "raw/episodes/top_podcasts.csv"
SHOWS_GCS_PATH = "raw/shows/shows.csv"

def upload_episodes_to_gcs(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.replace('.', '_', regex=False)
    
    # save cleaned version to temp file
    cleaned_path = "/tmp/top_podcasts_cleaned.csv"
    df.to_csv(cleaned_path, index=False)
    
    # upload cleaned version
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(EPISODES_GCS_PATH)
    blob.upload_from_filename(cleaned_path)
    # Confirm where the file ended up
    print(f"Uploaded to gs://{BUCKET_NAME}/{EPISODES_GCS_PATH}")

def get_existing_shows():
    """Check GCS for existing shows file and return show names if it exists"""
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(SHOWS_GCS_PATH)
    if blob.exists():
      try:
        return pd.read_csv(io.BytesIO(blob.download_as_bytes()))

      except Exception as e:
        print(f"Error loading existing shows: {e}")
        return None
    else:
     return None

def get_new_shows(episodes_df, existing_shows_df):
    # filter for English episodes first
    english_episodes = episodes_df[episodes_df['languages'].str.contains('en', case=False, na=False)]
    
    if existing_shows_df is None:
        return english_episodes['show_name'].unique()

    existing_shows = existing_shows_df['show_name'].unique()
    return english_episodes[~english_episodes['show_name'].isin(existing_shows)]['show_name'].unique()

    
def get_itunes_info(show_name):
    response = requests.get(
        "https://itunes.apple.com/search",
        params={
            "term": show_name,
            "media": "podcast",
            "entity": "podcast",
            "limit": 1
        }
    )

    # check for rate limiting before parsing
    if response.status_code == 429:
        print(f"Rate limited on: {show_name}")
        return '429'

    try:
        data = response.json()
    except RequestsJSONDecodeError as e:
        print(f"Error decoding JSON for show '{show_name}': {e}")
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        return None

    if data['resultCount'] == 0:
        print(f"No data found for: {show_name}")
        return {
        'show_name': show_name,
        'primary_genre': None,
        'all_genres': None,
        'genre_ids': None,
        'publisher': None,
        'itunes_found': False # explicitly mark as not found to avoid re-querying in future runs
    }

    result = data['results'][0]
    primary_genre = result.get('primaryGenreName')
    genres = ', '.join(result.get('genres', []))
    artist_name = result.get('artistName')
    genre_ids = ', '.join(result.get('genreIds', []))

    return {
        'show_name': show_name,
        'primary_genre': primary_genre,
        'all_genres': genres,
        'genre_ids': genre_ids,
        'publisher': artist_name,
        'itunes_found': True
    }

def upload_shows_to_gcs(shows_df):
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(SHOWS_GCS_PATH)
    blob.upload_from_string(shows_df.to_csv(index=False), content_type='text/csv')
    # Confirm where the file ended up
    print(f"Uploaded to gs://{BUCKET_NAME}/{SHOWS_GCS_PATH}")


def clean_show_name(show_name):
    cleaned = re.sub(r'[^\w\s\-\'\.\,\&]', '', show_name)
    return cleaned.strip()    

def enrich_shows(show_list, existing_shows_df=None, batch_size=100):
    upload_list = list(existing_shows_df.to_dict('records')) if existing_shows_df is not None else []
    success_count = 0
    skip_count = 0
    
    # break show_list into chunks of batch_size
    chunks = [show_list[i:i + batch_size] for i in range(0, len(show_list), batch_size)]
    print(f"Total shows to process: {len(show_list)} in {len(chunks)} chunks")
    
    for chunk_num, chunk in enumerate(chunks):
        print(f"\nStarting chunk {chunk_num + 1}/{len(chunks)}")
        
        for i, show_name in enumerate(chunk):
            # step 1 - clean the title
            cleaned_name = clean_show_name(show_name)
            
            # step 2 - hit iTunes API with retry logic
            while True:
                result = get_itunes_info(cleaned_name)
                if isinstance(result, dict):
                    # store original show_name so it joins back to episodes
                    result['show_name'] = show_name
                    upload_list.append(result)
                    success_count += 1
                    print(f"✓ Enriched: {show_name}")
                    break
                elif result == '429':
                    print(f"Rate limited, waiting 5 seconds...")
                    time.sleep(5)
                else:
                    skip_count += 1
                    break
            
            if i % 10 == 0:
                print(f"Chunk progress: {i}/{len(chunk)} | Total success: {success_count} | Skipped: {skip_count}")
        
        # upload after each chunk
        combined_df = pd.DataFrame(upload_list)
        upload_shows_to_gcs(combined_df)
        print(f"Chunk {chunk_num + 1} complete — {len(combined_df)} total shows in GCS")
        
        # wait between chunks to avoid rate limiting
        if chunk_num < len(chunks) - 1:
            print(f"Waiting 60 seconds before next chunk...")
            time.sleep(60)
    
    print(f"\nAll chunks complete — Success: {success_count} | Skipped: {skip_count}")
    return pd.DataFrame(upload_list)

def load_episodes_from_gcs():
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(EPISODES_GCS_PATH)
    return pd.read_csv(io.BytesIO(blob.download_as_bytes()))
    


def main():
    # load episodes CSV
    result = download_from_kaggle()

    upload_episodes_to_gcs(result)

    # store episodes data frame
    episodes_df = pd.read_csv(result)
    
    # get existing shows
    existing_shows_df = get_existing_shows()
    # get new shows
    new_shows = get_new_shows(episodes_df, existing_shows_df)
    # if no new shows, exit
    if len(new_shows) == 0:
        print("No new shows found")
        return
    # enrich new shows, will upload to GCS in batches
    enrich_shows(new_shows, existing_shows_df)

if __name__ == "__main__":
    main()