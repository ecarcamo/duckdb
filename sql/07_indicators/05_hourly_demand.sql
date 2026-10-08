SELECT
    hour(pickup_datetime) AS hour,
    taxi_type,
    round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY taxi_type), 2) AS pct_of_trips
FROM trips_clean
GROUP BY hour(pickup_datetime), taxi_type
ORDER BY hour, taxi_type;
