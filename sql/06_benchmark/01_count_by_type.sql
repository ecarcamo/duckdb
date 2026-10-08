SELECT
    taxi_type,
    count(*) AS trips
FROM trips
GROUP BY taxi_type
ORDER BY taxi_type DESC;
