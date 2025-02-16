WITH
src_data as (
    SELECT
        ingestion_timestamp as INGESTION_TIMESTAMP,
        yt_video_title as YT_VIDEO_TITLE,
        title as SEGMENT_TITLE,
        filename as FILENAME,
        format_name as FORMAT_NAME,
        sample_rate as SAMPLE_RATE,
        channels as CHANNELS,
        bits_per_sample as BITS_PER_SAMPLE,
        duration as DURATION,
        bit_rate as BIT_RATE,
        size as SIZE,
        codec_name as CODEC_NAME,
        min_speakers as MIN_SPEAKERS,
        max_speakers as MAX_SPEAKERS,
        team as TEAM,
        CASE
            WHEN text = '' THEN 'No Transcription'
            ELSE text
        END as TEXT,
        gpt_clarity as GPT_CLARITY,
        gpt_intensity as GPT_INTENSITY,
        CASE -- an empty string is not considered null
            WHEN gpt_summary = '' THEN 'No Summary'
            ELSE gpt_summary
        END as GPT_SUMMARY,
        'SRC.RAW_DATA_FROM_VIDEO' as RECORD_SOURCE
        
    FROM {{ source("SRC", "raw_data_from_video") }}
),

final as (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['INGESTION_TIMESTAMP', 'YT_VIDEO_TITLE', 'SEGMENT_TITLE']) }} as SURR_ID,
        *
    FROM src_data
)
SELECT * FROM final