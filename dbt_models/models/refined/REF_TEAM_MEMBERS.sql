WITH
    final as (
        SELECT 
            SURR_ID,
            PLAYER_NAME,
            TEAM,
            EFFECTIVE_START_DATE,
            EFFECTIVE_END_DATE,
            IS_CURRENT,
            CREATED_AT,
            UPDATED_AT
        FROM {{ ref('STG_TEAM_MEMBERS') }}
    )
SELECT *
FROM final