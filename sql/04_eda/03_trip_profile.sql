SELECT
    taxi_type,
    count(*) AS trips,
    round(quantile_cont(trip_distance, 0.5), 2) AS median_miles,
    round(quantile_cont(trip_distance, 0.9), 2) AS p90_miles,
    round(quantile_cont(duration_minutes, 0.5), 1) AS median_minutes,
    round(quantile_cont(duration_minutes, 0.9), 1) AS p90_minutes,
    round(quantile_cont(trip_distance / (duration_minutes / 60), 0.5), 1) AS median_mph,
    round(quantile_cont(total_amount, 0.5), 2) AS median_total,
    round(quantile_cont(total_amount, 0.9), 2) AS p90_total,
    round(avg(passenger_count), 2) AS avg_passengers,
    round(100.0 * count(*) FILTER (WHERE passenger_count = 1) / count(passenger_count), 1) AS pct_single_passenger
FROM trips_clean
GROUP BY taxi_type
ORDER BY taxi_type DESC;
