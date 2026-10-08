SELECT
    make_date(source_year, source_month, 1) AS month,
    taxi_type,
    round(count(*) / count(DISTINCT CAST(pickup_datetime AS DATE)), 0) AS trips_per_day
FROM trips_clean
GROUP BY ALL
ORDER BY month, taxi_type;
