SELECT
    make_date(source_year, source_month, 1) AS month,
    round(100.0 * count(*) FILTER (WHERE taxi_type = 'green') / count(*), 2) AS green_pct
FROM trips_clean
GROUP BY ALL
ORDER BY month;
