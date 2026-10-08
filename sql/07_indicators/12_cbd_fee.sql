SELECT
    make_date(source_year, source_month, 1) AS month,
    round(coalesce(sum(cbd_congestion_fee), 0) / 1e6, 2) AS cbd_fee_musd,
    round(100.0 * count(*) FILTER (WHERE cbd_congestion_fee > 0) / count(*), 1) AS pct_trips_with_fee
FROM trips_clean
GROUP BY ALL
ORDER BY month;
