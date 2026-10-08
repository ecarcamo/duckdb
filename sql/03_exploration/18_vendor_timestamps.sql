SELECT
    taxi_type,
    VendorID AS vendor_id,
    count(*) AS trips,
    count(*) FILTER (WHERE dropoff_datetime = pickup_datetime) AS same_timestamp,
    count(*) FILTER (WHERE dropoff_datetime < pickup_datetime) AS dropoff_before_pickup,
    round(100.0 * count(*) FILTER (WHERE dropoff_datetime <= pickup_datetime) / count(*), 2) AS pct_non_positive_duration
FROM trips
GROUP BY ALL
ORDER BY taxi_type DESC, vendor_id;
