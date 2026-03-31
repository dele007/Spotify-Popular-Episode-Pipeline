SELECT *
FROM {{ source('podcast_shows', 'raw_shows') }} s
WHERE itunes_found = TRUE