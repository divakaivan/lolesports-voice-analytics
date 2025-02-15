WITH
src_data as (
    SELECT
        player_name as PLAYER_NAME,
        team as TEAM,
        effective_start_date as EFFECTIVE_START_DATE,
        effective_end_date as EFFECTIVE_END_DATE,
        is_current as IS_CURRENT,
        created_at as CREATED_AT,
        updated_at as UPDATED_AT,
        'SRC.TEAM_MEMBERS' as RECORD_SOURCE
        
    FROM {{ source("staging", "team_members") }}
),

final as (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['PLAYER_NAME', 'TEAM', 'EFFECTIVE_START_DATE']) }} as SURR_ID,
        *
    FROM src_data
)
SELECT * FROM final