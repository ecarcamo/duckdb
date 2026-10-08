SELECT
    make_date(source_year, source_month, 1) AS month,
    round(100.0 * count(*) FILTER (WHERE payment_type = 1) / count(*), 1) AS pct_card,
    round(100.0 * count(*) FILTER (WHERE payment_type = 2) / count(*), 1) AS pct_cash,
    round(100.0 * count(*) FILTER (WHERE payment_type = 0) / count(*), 1) AS pct_flex_fare
FROM trips_clean
WHERE taxi_type = 'yellow'
GROUP BY ALL
ORDER BY month;
