WITH
    final as (
        SELECT 
                YT_VIDEO_TITLE,
                MAX(INGESTION_TIMESTAMP) as INGESTION_TIMESTAMP,
                ARRAY_AGG(FILENAME) as FILENAME_LIST,
                MAX(TEAM) as TEAM
        FROM {{ ref('REF_DATA_FROM_VIDEO') }}
        GROUP BY YT_VIDEO_TITLE
    )
SELECT *
FROM final