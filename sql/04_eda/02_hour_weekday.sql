SELECT
    taxi_type,
    isodow(pickup_datetime) AS weekday,
    hour(pickup_datetime) AS hour,
    round(count(*) / count(DISTINCT CAST(pickup_datetime AS DATE)), 1) AS trips_per_day
FROM trips_clean
GROUP BY ALL
ORDER BY taxi_type DESC, weekday, hour;
