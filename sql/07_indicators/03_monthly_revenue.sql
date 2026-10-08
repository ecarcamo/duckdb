SELECT
    make_date(source_year, source_month, 1) AS month,
    taxi_type,
    round(sum(total_amount) / 1e6, 2) AS revenue_musd
FROM trips_clean
GROUP BY ALL
ORDER BY month, taxi_type;
