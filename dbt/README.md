# dbt Project — Spotify Podcast Pipeline

## Overview

This dbt project transforms raw Spotify podcast chart data and iTunes show metadata into clean, analytics-ready tables for dashboard consumption.

## Model Lineage

```
sources
├── podcast_episodes.raw_episodes     (Spotify daily top 200 chart data)
└── podcast_shows.raw_shows           (iTunes genre enrichment data)
        │
        ▼
staging
├── stg_episodes                      (cleaned episodes, English only)
└── stg_shows                         (renamed columns from iTunes enrichment)
        │
        ▼
intermediate
├── int_enriched_episodes             (episodes joined to show genre data)
└── int_show_rankings                 (show level aggregations)
        │
        ▼
marts
├── mart_show_rankings                (most popular shows by average rank)
└── mart_recent_episodes              (most popular recent episodes)
```

## Modeling Decisions

### Staging
- `stg_episodes` filters for English language only using the `languages` column
- `stg_shows` renames auto-generated BigQuery column names to meaningful ones
- Both models use `{{ source() }}` references for lineage tracking

### Intermediate
- `int_enriched_episodes` uses a `LEFT JOIN` to preserve episodes for shows not found in iTunes — missing genre data appears as null and is handled downstream
- `int_show_rankings` uses a two step aggregation: each episode's best rank first, then averaged per show. This measures consistent quality rather than rewarding volume
- `ranked_episode_rate` stored as 4 decimal float for clean percentage conversion in dashboard

### Marts
- Materialized as **tables** for fast dashboard query performance
- `mart_show_rankings` ordered by `avg_best_rank` ascending — lower rank number means higher chart position
- `mart_recent_episodes` ordered by `release_date` descending for a "what's new and popular" discovery experience

### Why Average Best Rank?
Average best rank was chosen over straight average because it rewards shows that consistently produce high charting episodes rather than penalizing shows that appear frequently with varying performance.

## Running dbt

```bash
# run all models
dbt run

# run specific layer
dbt run --select staging
dbt run --select intermediate
dbt run --select marts

# run tests
dbt test

# generate documentation
dbt docs generate
dbt docs serve
```

## Tests

Tests are defined in `schema.yml` files within each model folder. Key tests:
- `not_null` on core columns like `show_name`, `episode_name`, `daily_rank`
- `unique` on `show_name` in `stg_shows` and mart tables
