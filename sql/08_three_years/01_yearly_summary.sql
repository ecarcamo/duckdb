WITH common_months AS (
    SELECT CAST(regexp_extract(file, '-(\d{2})\.parquet$', 1) AS INTEGER) AS month
    FROM glob('data/raw/yellow/*/*.parquet')
    GROUP BY month
    HAVING count(*) = (SELECT count(DISTINCT split_part(file, '/', 4)) FROM glob('data/raw/yellow/*/*.parquet'))
),
airport_zones AS (
    SELECT location_id
    FROM zones
    WHERE service_zone IN ('Airports', 'EWR')
)
SELECT
    source_year AS year,
    min(source_month) || '-' || max(source_month) AS months,
    count(*) AS trips,
    round(count(*) / count(DISTINCT CAST(pickup_datetime AS DATE)), 0) AS trips_per_day,
    round(sum(total_amount) / 1e6, 1) AS revenue_musd,
    round(avg(total_amount), 2) AS avg_ticket,
    round(avg(fare_amount), 2) AS avg_fare,
    round(quantile_cont(trip_distance, 0.5), 2) AS median_miles,
    round(approx_quantile(duration_minutes, 0.5), 1) AS median_minutes,
    round(approx_quantile(trip_distance / (duration_minutes / 60), 0.5), 1) AS median_mph,
    round(100.0 * count(*) FILTER (WHERE taxi_type = 'green') / count(*), 2) AS pct_green,
    round(100.0 * count(*) FILTER (WHERE payment_type = 0) / count(*), 1) AS pct_flex_fare,
    round(100.0 * count(*) FILTER (WHERE payment_type = 1) / count(*), 1) AS pct_card,
    round(100.0 * count(*) FILTER (WHERE payment_type = 2) / count(*), 1) AS pct_cash,
    round(100.0 * count(*) FILTER (
        WHERE PULocationID IN (SELECT location_id FROM airport_zones)
           OR DOLocationID IN (SELECT location_id FROM airport_zones)
    ) / count(*), 1) AS pct_airport,
    round(100.0 * count(*) FILTER (WHERE cbd_congestion_fee > 0) / count(*), 1) AS pct_cbd_fee
FROM trips_clean
WHERE source_month IN (SELECT month FROM common_months)
GROUP BY source_year
ORDER BY year;
