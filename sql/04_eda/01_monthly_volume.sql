SELECT
    taxi_type,
    source_year AS year,
    source_month AS month,
    count(*) AS trips,
    round(count(*) / count(DISTINCT CAST(pickup_datetime AS DATE)), 0) AS trips_per_day,
    round(sum(total_amount), 0) AS revenue,
    round(avg(total_amount), 2) AS avg_total
FROM trips_clean
GROUP BY ALL
ORDER BY taxi_type DESC, year, month;
