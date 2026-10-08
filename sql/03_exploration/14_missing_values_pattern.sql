SELECT
    taxi_type,
    payment_type,
    passenger_count IS NULL AS passenger_count_missing,
    count(*) AS trips,
    round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY taxi_type), 2) AS pct_of_type
FROM trips
GROUP BY taxi_type, payment_type, passenger_count IS NULL
ORDER BY taxi_type DESC, trips DESC;
