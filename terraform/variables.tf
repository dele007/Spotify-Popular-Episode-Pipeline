variable "bq_project" {
  description = "The GCP project for the Spotify podcast BigQuery dataset."
  default     = "spotify-episode-pipeline"
}

variable "bq_dataset_name" {
  description = "The top 200 podcast episodes on Spotify on a daily basis starting Sept 2024"
  default     = "podcast_episodes"
}

variable "bq_dataset_name2" {
  description = "Descriptive info for podcasts."
  default     = "podcast_shows"
}

variable "bq_dataset_name3" {
  description = "Transformed podcast data."
  default     = "podcast_transformed"
}

variable "location" {
  description = "The location of the GCS bucket."
  default     = "US-CENTRAL1"
}

variable "gcs_bucket_name" {
  description = "Bucket containing the top 200 Spotify episodes on a daily basis. Also has general show info"
  default     = "spotify_podcast_bucket"
}

variable "gcs_storage_class" {
  description = "The class of the GCS bucket."
  default     = "STANDARD"
}

