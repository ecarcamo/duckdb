WITH common_months AS (
    SELECT CAST(regexp_extract(file, '-(\d{2})\.parquet$', 1) AS INTEGER) AS month
    FROM glob('data/raw/yellow/*/*.parquet')
    GROUP BY month
    HAVING count(*) = (SELECT count(DISTINCT split_part(file, '/', 4)) FROM glob('data/raw/yellow/*/*.parquet'))
),
raw AS (
    SELECT source_year, count(*) AS trips, count(*) FILTER (WHERE payment_type = 0 AND fare_amount < 0 AND total_amount > 0) AS flex_negative_fare
    FROM trips
    WHERE taxi_type = 'yellow' AND source_month IN (SELECT month FROM common_months)
    GROUP BY source_year
),
clean AS (
    SELECT source_year, count(*) AS trips
    FROM trips_clean
    WHERE taxi_type = 'yellow' AND source_month IN (SELECT month FROM common_months)
    GROUP BY source_year
)
SELECT
    source_year AS year,
    raw.trips AS raw_trips,
    clean.trips AS clean_trips,
    round(100.0 * (raw.trips - clean.trips) / raw.trips, 2) AS pct_discarded,
    raw.flex_negative_fare,
    round(100.0 * (raw.trips / lag(raw.trips) OVER (ORDER BY source_year) - 1), 1) AS raw_growth_pct,
    round(100.0 * (clean.trips / lag(clean.trips) OVER (ORDER BY source_year) - 1), 1) AS clean_growth_pct
FROM raw
JOIN clean USING (source_year)
ORDER BY year;
