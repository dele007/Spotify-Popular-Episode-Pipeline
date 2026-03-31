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
show_total_episodes,
CASE 
WHEN region LIKE 'ar' THEN 'Argentina'
WHEN region LIKE 'au' THEN 'Australia'
WHEN region LIKE 'at' THEN 'Austria'
WHEN region LIKE 'br' THEN 'Brazil'
WHEN region LIKE 'ca' THEN 'Canada'
WHEN region LIKE 'cl' THEN 'Chile'
WHEN region LIKE 'co' THEN 'Colombia'
WHEN region LIKE 'fr' THEN 'France'
WHEN region LIKE 'de' THEN 'Germany'
WHEN region LIKE 'in' THEN 'India'
WHEN region LIKE 'id' THEN 'Indonesia'
WHEN region LIKE 'ie' THEN 'Ireland'
WHEN region LIKE 'it' THEN 'Italy'
WHEN region LIKE 'jp' THEN 'Japan'
WHEN region LIKE 'mx' THEN 'Mexico'
WHEN region LIKE 'nz' THEN 'New Zealand'
WHEN region LIKE 'ph' THEN 'Philippines'
WHEN region LIKE 'pl' THEN 'Poland'
WHEN region LIKE 'es' THEN 'Spain'
WHEN region LIKE 'nl' THEN 'Netherlands'
WHEN region LIKE 'gb' THEN 'United Kingdom'
WHEN region LIKE 'us' THEN 'United States'
END as region_expanded

FROM {{ source('podcast_episodes', 'raw_episodes') }}
WHERE languages LIKE '%en%' AND show_name IS NOT NULL

# Take out a random episode that was still sticking around.

AND NOT(date = '2026-02-24' AND rank = 176	
AND region = 'ca' AND episodeName LIKE	'%r/Offmychest I Was Forced into a Poly Marriage%')