WITH
    final as (
        SELECT 
            YT_VIDEO_TITLE,
            SEGMENT_TITLE,
            FILENAME,
            FORMAT_NAME,
            SAMPLE_RATE,
            CHANNELS,
            BITS_PER_SAMPLE,
            DURATION,
            BIT_RATE,
            SIZE,
            CODEC_NAME,
            MIN_SPEAKERS,
            MAX_SPEAKERS
        FROM {{ ref('REF_DATA_FROM_VIDEO') }}
    )
SELECT *
FROM final