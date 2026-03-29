-- tokpipe reference SQL queries
-- Use these with DuckDB, SQLite, or any SQL engine that can read CSV/Parquet.
-- Load your tokpipe CSV output first:
--   CREATE TABLE videos AS SELECT * FROM read_csv_auto('report.csv');

-- ============================================================
-- ENGAGEMENT
-- ============================================================

-- Average engagement rate
SELECT AVG(engagement_rate) AS avg_engagement
FROM videos;

-- Engagement rate by category (requires classify column)
SELECT category,
       COUNT(*) AS videos,
       AVG(engagement_rate) AS avg_engagement,
       MEDIAN(engagement_rate) AS median_engagement
FROM videos
GROUP BY category
ORDER BY avg_engagement DESC;

-- Top 10 videos by engagement
SELECT *
FROM videos
ORDER BY engagement_rate DESC
LIMIT 10;

-- ============================================================
-- TIMING
-- ============================================================

-- Best posting hour (by median engagement)
SELECT EXTRACT(HOUR FROM post_date) AS hour,
       COUNT(*) AS videos,
       MEDIAN(engagement_rate) AS median_engagement
FROM videos
WHERE post_date IS NOT NULL
GROUP BY hour
ORDER BY median_engagement DESC;

-- Best day of week
SELECT DAYNAME(post_date) AS day_of_week,
       COUNT(*) AS videos,
       MEDIAN(engagement_rate) AS median_engagement
FROM videos
WHERE post_date IS NOT NULL
GROUP BY day_of_week
ORDER BY median_engagement DESC;

-- ============================================================
-- GROWTH
-- ============================================================

-- Daily views
SELECT CAST(post_date AS DATE) AS day,
       SUM(views) AS total_views,
       COUNT(*) AS videos_posted
FROM videos
WHERE post_date IS NOT NULL
GROUP BY day
ORDER BY day;

-- 7-day rolling average of views
SELECT day,
       total_views,
       AVG(total_views) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rolling_7d
FROM (
    SELECT CAST(post_date AS DATE) AS day,
           SUM(views) AS total_views
    FROM videos
    WHERE post_date IS NOT NULL
    GROUP BY day
) daily
ORDER BY day;

-- ============================================================
-- CONTENT ANALYSIS
-- ============================================================

-- Videos with zero engagement (debug)
SELECT *
FROM videos
WHERE engagement_rate = 0 AND views > 0;

-- Correlation between views and engagement
SELECT CORR(views, engagement_rate) AS views_engagement_corr
FROM videos
WHERE views > 0;

-- Videos above 90th percentile engagement
SELECT *
FROM videos
WHERE engagement_rate > (SELECT PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY engagement_rate) FROM videos)
ORDER BY engagement_rate DESC;
