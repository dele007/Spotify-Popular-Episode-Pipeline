SELECT
string_field_0 AS show_name,
string_field_1 AS primary_genre,
string_field_2 AS all_genres,
string_field_3 AS genre_ids,
string_field_4 AS publisher,

FROM {{ source('podcast_shows', 'raw_shows') }} s
