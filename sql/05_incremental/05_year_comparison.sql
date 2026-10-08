WITH common_months AS (
    SELECT CAST(regexp_extract(file, '-(\d{2})\.parquet$', 1) AS INTEGER) AS month
    FROM glob('data/raw/yellow/*/*.parquet')
    GROUP BY month
    HAVING count(*) = (SELECT count(DISTINCT split_part(file, '/', 4)) FROM glob('data/raw/yellow/*/*.parquet'))
)
SELECT
    taxi_type,
    source_year AS year,
    min(source_month) || '-' || max(source_month) AS months,
    count(*) AS trips,
    round(count(*) / count(DISTINCT CAST(pickup_datetime AS DATE)), 0) AS trips_per_day,
    round(avg(total_amount), 2) AS avg_total,
    round(quantile_cont(trip_distance, 0.5), 2) AS median_miles,
    round(quantile_cont(duration_minutes, 0.5), 1) AS median_minutes,
    round(100.0 * count(*) FILTER (WHERE payment_type = 1) / count(*), 1) AS pct_card,
    round(100.0 * count(*) FILTER (WHERE payment_type = 2) / count(*), 1) AS pct_cash,
    round(100.0 * count(*) FILTER (WHERE cbd_congestion_fee > 0) / count(*), 1) AS pct_cbd_fee
FROM trips_clean
WHERE source_month IN (SELECT month FROM common_months)
GROUP BY taxi_type, source_year
ORDER BY taxi_type DESC, year;
