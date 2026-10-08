SELECT
    make_date(source_year, source_month, 1) AS month,
    round(100.0 * count(*) FILTER (WHERE cbd_congestion_fee > 0) / count(*), 1) AS pct_trips_with_fee,
    round(coalesce(sum(cbd_congestion_fee), 0) / 1e6, 2) AS cbd_fee_musd,
    round(avg(total_amount), 2) AS avg_ticket
FROM trips_clean
WHERE taxi_type = 'yellow'
GROUP BY ALL
ORDER BY month;
