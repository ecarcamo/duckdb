SELECT
    taxi_type,
    CASE
        WHEN trip_distance < 1 THEN '0-1'
        WHEN trip_distance < 2 THEN '1-2'
        WHEN trip_distance < 3 THEN '2-3'
        WHEN trip_distance < 5 THEN '3-5'
        WHEN trip_distance < 10 THEN '5-10'
        WHEN trip_distance < 20 THEN '10-20'
        ELSE '20+'
    END AS miles,
    min(trip_distance) AS bucket_start,
    count(*) AS trips,
    round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY taxi_type), 2) AS pct_of_type
FROM trips_clean
GROUP BY taxi_type, miles
ORDER BY taxi_type DESC, bucket_start;
