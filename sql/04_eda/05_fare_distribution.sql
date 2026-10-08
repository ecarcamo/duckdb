SELECT
    taxi_type,
    least(floor(total_amount / 5) * 5, 150) AS total_bucket,
    count(*) AS trips,
    round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY taxi_type), 2) AS pct_of_type
FROM trips_clean
GROUP BY taxi_type, total_bucket
ORDER BY taxi_type DESC, total_bucket;
