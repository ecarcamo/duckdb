SELECT
    taxi_type,
    hour(pickup_datetime) AS hour,
    count(*) AS card_trips,
    round(100.0 * count(*) FILTER (WHERE tip_amount > 0) / count(*), 1) AS pct_with_tip,
    round(100.0 * sum(tip_amount) / sum(fare_amount), 1) AS tip_pct_of_fare
FROM trips_clean
WHERE payment_type = 1
  AND fare_amount > 0
GROUP BY ALL
ORDER BY taxi_type DESC, hour;
