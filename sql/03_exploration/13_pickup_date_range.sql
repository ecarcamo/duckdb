SELECT
    taxi_type,
    min(pickup_datetime) AS min_pickup,
    max(pickup_datetime) AS max_pickup,
    count(*) FILTER (WHERE year(pickup_datetime) < 2026) AS pickups_before_2026,
    count(*) FILTER (WHERE pickup_datetime > TIMESTAMP '2026-09-01') AS pickups_after_aug_2026
FROM trips
GROUP BY taxi_type
ORDER BY taxi_type DESC;
