SELECT
    make_date(source_year, source_month, 1) AS month,
    taxi_type,
    round(100.0 * sum(tip_amount) / sum(fare_amount), 2) AS tip_pct_of_fare
FROM trips_clean
WHERE payment_type = 1
  AND fare_amount > 0
GROUP BY ALL
ORDER BY month, taxi_type;
