SELECT
    taxi_type,
    source_year,
    min(pickup_datetime) AS min_pickup,
    max(pickup_datetime) AS max_pickup,
    count(*) FILTER (WHERE year(pickup_datetime) < source_year) AS pickups_before_file_year,
    count(*) FILTER (WHERE year(pickup_datetime) > source_year) AS pickups_after_file_year
FROM trips
GROUP BY taxi_type, source_year
ORDER BY taxi_type DESC, source_year;
