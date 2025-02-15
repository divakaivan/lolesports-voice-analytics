WITH
    final as (
        SELECT 
            FILENAME,
            TEXT,
            GPT_CLARITY,
            GPT_INTENSITY,
            GPT_SUMMARY,
            GAME_TOTAL_TOKENS,
            GAME_DURATION_SEC,
            AVG_GAME_CLARITY,
            AVG_GAME_INTENSITY
        FROM {{ ref('REF_DATA_FROM_VIDEO') }}
    )
SELECT *
FROM final