WITH checks AS (
    SELECT
        taxi_type,
        count(*) AS total_trips,
        count(*) FILTER (
            WHERE pickup_datetime < make_timestamp(source_year, source_month, 1, 0, 0, 0)
               OR pickup_datetime >= make_timestamp(source_year, source_month, 1, 0, 0, 0) + INTERVAL 1 MONTH
        ) AS pickup_outside_file_month,
        count(*) FILTER (WHERE dropoff_datetime <= pickup_datetime) AS non_positive_duration,
        count(*) FILTER (WHERE dropoff_datetime > pickup_datetime + INTERVAL 6 HOUR) AS duration_over_6h,
        count(*) FILTER (WHERE trip_distance = 0) AS zero_distance,
        count(*) FILTER (WHERE trip_distance > 100) AS distance_over_100mi,
        count(*) FILTER (WHERE fare_amount < 0 OR total_amount < 0) AS negative_amount,
        count(*) FILTER (WHERE total_amount > 1000) AS total_over_1000,
        count(*) FILTER (WHERE passenger_count IS NULL) AS null_passenger_count,
        count(*) FILTER (WHERE passenger_count = 0) AS zero_passengers,
        count(*) FILTER (WHERE RatecodeID = 99) AS ratecode_99,
        count(*) FILTER (WHERE payment_type = 0) AS payment_type_0,
        count(*) FILTER (WHERE PULocationID IN (264, 265) OR DOLocationID IN (264, 265)) AS unknown_zone
    FROM trips
    GROUP BY taxi_type
)
SELECT
    taxi_type,
    issue,
    affected_trips,
    round(100.0 * affected_trips / total_trips, 3) AS pct_of_trips
FROM checks
UNPIVOT (affected_trips FOR issue IN (
    pickup_outside_file_month, non_positive_duration, duration_over_6h, zero_distance,
    distance_over_100mi, negative_amount, total_over_1000, null_passenger_count,
    zero_passengers, ratecode_99, payment_type_0, unknown_zone
))
ORDER BY taxi_type DESC, pct_of_trips DESC;
