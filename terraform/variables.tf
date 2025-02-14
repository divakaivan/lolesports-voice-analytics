locals {
  credentials = "../include/my-creds.json"
}

variable "region" {
  description = "Region"
  default     = "asia-northeast3-a"
}

variable "project" {
  description = "Project"
  default     = "dataengcamp-427114"
}

variable "location" {
    description = "Project Location"
    default = "US"
}

variable "bq_dataset_name" {
    description = "My BigQuery Dataset Name"
    default = "lolesports_voice_analytics"
}

variable "gcs_bucket_name" {
    description = "My Storage Bucket Name"
    default = "lolesports_voice_analytics_files"
}

variable "gcs_storage_class" {
    description = "Bucket Storage Class"
    default = "STANDARD"
}

variable "raw_data_from_video_schema" {
    description = "Schema for raw_data_from_video table"
    default = <<EOF
[
    {
        "name": "ingestion_timestamp",
        "type": "TIMESTAMP",
        "mode": "REQUIRED",
        "description": "Timestamp of when the data was ingested",
        "defaultValueExpression": "CURRENT_TIMESTAMP()"
    },
    {
        "name": "yt_video_title",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "Title of the YouTube video"
    },
    {
        "name": "title",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "Title of the segment"
    },
    {
        "name": "filename",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "Filename of the audio segment"
    },
    {
        "name": "format_name",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "Format of the audio segment"
    },
    {
        "name": "sample_rate",
        "type": "INTEGER",
        "mode": "REQUIRED",
        "description": "Sample rate of the audio segment"
    },
    {
        "name": "channels",
        "type": "INTEGER",
        "mode": "REQUIRED",
        "description": "Number of channels in the audio segment"
    },
    {
        "name": "bits_per_sample",
        "type": "INTEGER",
        "mode": "REQUIRED",
        "description": "Bits per sample in the audio segment"
    },
    {
        "name": "duration",
        "type": "FLOAT",
        "mode": "REQUIRED",
        "description": "Duration of the audio segment"
    },
    {
        "name": "bit_rate",
        "type": "INTEGER",
        "mode": "REQUIRED",
        "description": "Bit rate of the audio segment"
    },
    {
        "name": "size",
        "type": "INTEGER",
        "mode": "REQUIRED",
        "description": "Size of the audio segment"
    },
    {
        "name": "codec_name",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "Codec name of the audio segment"
    },
    {
        "name": "min_speakers",
        "type": "INTEGER",
        "mode": "REQUIRED",
        "description": "Minimum number of speakers in the audio segment"
    },
    {
        "name": "max_speakers",
        "type": "INTEGER",
        "mode": "REQUIRED",
        "description": "Maximum number of speakers in the audio segment"
    },
    {
        "name": "team",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "Team name"
    },
    {
        "name": "text",
        "type": "STRING",
        "mode": "NULLABLE",
        "description": "Transcription of the audio segment"
    },
    {
        "name": "gpt_clarity",
        "type": "INTEGER",
        "mode": "REQUIRED",
        "description": "Clarity rating of the audio segment"
    },
    {
        "name": "gpt_intensity",
        "type": "INTEGER",
        "mode": "REQUIRED",
        "description": "Intensity rating of the audio segment"
    },
    {
        "name": "gpt_summary",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "Summary of the audio segment"
    }
]
EOF

}

variable "team_members_schema" {
    description = "Schema for team_members table"
    default = <<EOF
[
    {
        "name": "player_name",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "Player Name"
    },
    {
        "name": "team",
        "type": "STRING",
        "mode": "REQUIRED",
        "description": "Current Team Name"
    },
    {
        "name": "effective_start_date",
        "type": "DATE",
        "mode": "REQUIRED",
        "description": "Date when the player joined the team"
    },
    {
        "name": "effective_end_date",
        "type": "DATE",
        "mode": "NULLABLE",
        "description": "Date when the player left the team (NULL if active)"
    },
    {
        "name": "is_current",
        "type": "BOOLEAN",
        "mode": "REQUIRED",
        "description": "Indicates whether this is the current team (TRUE = Active, FALSE = Historical)"
    },
    {
        "name": "created_at",
        "type": "TIMESTAMP",
        "mode": "REQUIRED",
        "description": "Record creation timestamp"
    },
    {
        "name": "updated_at",
        "type": "TIMESTAMP",
        "mode": "REQUIRED",
        "description": "Last update timestamp"
    }
]
EOF

}
