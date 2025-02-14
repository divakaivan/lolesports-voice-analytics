WITH with_token_count AS (
    SELECT 
        *,
        BYTE_LENGTH(TEXT) / 4 as TOKEN_COUNT,
        REGEXP_REPLACE(SEGMENT_TITLE, '\\s\\(.*\\)', '') as GAME_IDENTIFIER
    FROM {{ ref('STG_RAW_DATA_FROM_VIDEO') }}
),
game_level_aggregations AS (
    SELECT 
        {{ dbt_utils.generate_surrogate_key(['YT_VIDEO_TITLE', 'GAME_IDENTIFIER']) }} AS GAME_ID,
        SUM(TOKEN_COUNT) AS GAME_TOTAL_TOKENS,
        SUM(DURATION) AS GAME_DURATION,
        ROUND(AVG(GPT_CLARITY), 2) AS AVG_GAME_CLARITY,
        ROUND(AVG(GPT_INTENSITY), 2) AS AVG_GAME_INTENSITY
    FROM with_token_count
    WHERE GAME_IDENTIFIER LIKE 'Game %'
    GROUP BY GAME_ID
)

SELECT 
    wtc.SURR_ID,
    wtc.INGESTION_TIMESTAMP,
    wtc.YT_VIDEO_TITLE,
    wtc.SEGMENT_TITLE,
    wtc.FILENAME,
    wtc.FORMAT_NAME,
    wtc.SAMPLE_RATE,
    wtc.CHANNELS,
    wtc.BITS_PER_SAMPLE,
    wtc.DURATION,
    wtc.BIT_RATE,
    wtc.SIZE,
    wtc.CODEC_NAME,
    wtc.MIN_SPEAKERS,
    wtc.MAX_SPEAKERS,
    wtc.TEAM,
    wtc.TEXT,
    wtc.GPT_CLARITY,
    wtc.GPT_INTENSITY,
    wtc.GPT_SUMMARY,
    wtc.RECORD_SOURCE,
    COALESCE(gla.GAME_ID, '-1') as GAME_ID,
    COALESCE(gla.GAME_TOTAL_TOKENS, 0.00) as GAME_TOTAL_TOKENS,
    COALESCE(gla.GAME_DURATION, 0.00) as GAME_DURATION_SEC,
    COALESCE(gla.AVG_GAME_CLARITY, -1.00) as AVG_GAME_CLARITY,
    COALESCE(gla.AVG_GAME_INTENSITY, -1.00) as AVG_GAME_INTENSITY
FROM with_token_count wtc
LEFT JOIN game_level_aggregations gla
    ON {{ dbt_utils.generate_surrogate_key(['YT_VIDEO_TITLE', 'GAME_IDENTIFIER']) }} = gla.GAME_ID
