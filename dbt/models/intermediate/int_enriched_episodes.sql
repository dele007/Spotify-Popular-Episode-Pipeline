WITH episodes AS (
    SELECT
        *,
        CAST(duration_ms AS INT64) AS duration_ms_int
    FROM {{ ref('stg_episodes') }}
)

SELECT
    episodes.*,
    TIME(
    CAST(FLOOR(duration_ms_int / 3600000) AS INT64),
    CAST(MOD(CAST(duration_ms_int / 60000 AS INT64), 60) AS INT64),
    CAST(MOD(CAST(duration_ms_int / 1000 AS INT64), 60) AS INT64)
) AS duration_formatted,
s.primary_genre,
s.all_genres
FROM episodes
LEFT JOIN {{ref("stg_shows")}} s ON s.show_name = episodes.show_name