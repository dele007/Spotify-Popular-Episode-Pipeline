SELECT *
FROM {{ ref("int_show_rankings") }}
ORDER BY avg_rank ASC, ranked_episode_rate DESC