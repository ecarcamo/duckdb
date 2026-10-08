SELECT
    hour(pickup_datetime) AS hour,
    round(approx_quantile(trip_distance / (duration_minutes / 60), 0.5), 1) AS median_mph,
    round(approx_quantile(duration_minutes, 0.5), 1) AS median_minutes
FROM trips_clean
WHERE duration_minutes >= 1
GROUP BY ALL
ORDER BY hour;
