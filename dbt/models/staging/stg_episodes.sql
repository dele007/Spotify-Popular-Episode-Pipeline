SELECT
date AS collection_date,
rank AS daily_rank,
region,
episodeName AS episode_name,
description AS episode_description,
show_name,
show_description,
show_publisher,
duration_ms,
ROUND(duration_ms / 60000.0, 0) as duration_minutes,
languages,
release_date,
release_date_precision,
show_media_type,
show_total_episodes

 
FROM {{ source('podcast_episodes', 'raw_episodes') }}
WHERE languages LIKE '%en%'