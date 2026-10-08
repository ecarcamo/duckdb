SELECT
    taxi_type,
    count(*) AS trips,
    round(avg(total_amount), 2) AS avg_total,
    round(avg(trip_distance), 2) AS avg_miles
FROM trips
WHERE pickup_datetime >= TIMESTAMP '2026-01-15'
  AND pickup_datetime < TIMESTAMP '2026-01-16'
GROUP BY taxi_type
ORDER BY taxi_type DESC;
