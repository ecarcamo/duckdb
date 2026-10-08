SELECT
    taxi_type,
    source_month AS month,
    count(*) AS trips,
    round(100.0 * count(*) FILTER (WHERE cbd_congestion_fee > 0) / count(*), 2) AS pct_with_cbd_fee,
    round(sum(cbd_congestion_fee), 0) AS cbd_fee_collected
FROM trips_clean
GROUP BY ALL
ORDER BY taxi_type DESC, month;
