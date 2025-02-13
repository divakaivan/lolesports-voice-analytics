terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "5.34.0"
    }
  }
}

provider "google" {
  credentials = local.credentials
  project = var.project
  region  = var.region
}

resource "google_storage_bucket" "lolesports_voice_analytics_files" {
  name          = var.gcs_bucket_name
  location      = var.location

  storage_class = var.gcs_storage_class
  uniform_bucket_level_access = true

  versioning {
    enabled     = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30  // days
    }
  }

  force_destroy = true
}

resource "google_bigquery_dataset" "lolesports_voice_analytics" {
  dataset_id = var.bq_dataset_name
  location = var.location
}

resource "google_bigquery_table" "team_members" {
  dataset_id = google_bigquery_dataset.lolesports_voice_analytics.dataset_id
  table_id   = "team_members"
  table_constraints {
    primary_key {
      columns = ["player_name", "team", "effective_start_date"]
      }
  }

  schema = var.team_members_schema
  deletion_protection=false

}


resource "google_bigquery_table" "raw_data_from_video" {
  dataset_id = google_bigquery_dataset.lolesports_voice_analytics.dataset_id
  table_id   = "raw_data_from_video"
  table_constraints {
    primary_key {
      columns = ["yt_video_title", "ingestion_timestamp"]
    }
  }

  schema = var.raw_data_from_video_schema
  deletion_protection=false

}
