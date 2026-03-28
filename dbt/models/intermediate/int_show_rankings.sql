WITH best_rank AS (
    SELECT show_name, episode_name, MIN(daily_rank) AS best_rank, MAX(show_total_episodes) as total_episodes
    FROM {{ref("stg_episodes")}} e
    GROUP by show_name, episode_name
)

SELECT 
s.show_name,
s.primary_genre,
s.all_genres,
s.genre_ids,
s.publisher,
ROUND(AVG(b.best_rank), 2) AS avg_rank,
COUNT(episode_name) AS ranked_episodes,
MAX(total_episodes) AS total_episodes,
ROUND( COUNT(episode_name) / MAX(total_episodes), 4) AS ranked_episode_rate
FROM {{ref("stg_shows")}} s
LEFT JOIN best_rank b  ON b.show_name = s.show_name
GROUP BY s.show_name, s.primary_genre, s.all_genres, s.genre_ids, s.publisher