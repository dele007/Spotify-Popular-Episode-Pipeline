terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.16.0"
    }
  }
}

provider "google" {
  # Configuration options
  project = var.bq_project
  region  = "us-central1"
}




resource "google_storage_bucket" "spotify-podcast-bucket" {
  name          = var.gcs_bucket_name
  location      = var.location
  force_destroy = true
  uniform_bucket_level_access = true


  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}





resource "google_bigquery_dataset" "podcast-episodes" {
  dataset_id = var.bq_dataset_name
  location = var.location
}

resource "google_bigquery_dataset" "podcast-shows" {
  dataset_id = var.bq_dataset_name2
  location = var.location
}

resource "google_bigquery_dataset" "podcast_transformed" {
  dataset_id = var.bq_dataset_name3
  location   = var.location
}