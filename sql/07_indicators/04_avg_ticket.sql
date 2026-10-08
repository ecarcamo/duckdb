SELECT
    make_date(source_year, source_month, 1) AS month,
    taxi_type,
    round(avg(total_amount), 2) AS avg_ticket
FROM trips_clean
GROUP BY ALL
ORDER BY month, taxi_type;
