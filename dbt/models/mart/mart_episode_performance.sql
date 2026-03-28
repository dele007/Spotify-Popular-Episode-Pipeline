SELECT
    episode_name,
    show_name,
    primary_genre,
    release_date,
    MIN(daily_rank) AS best_rank,
    COUNT(*) AS days_charted,
    duration_ms,
    duration_minutes,
    duration_formatted

FROM {{ ref('int_enriched_episodes') }}
GROUP BY 1, 2, 3, 4, 7, 8,9
ORDER BY release_date DESC