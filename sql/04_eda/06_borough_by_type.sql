SELECT
    t.taxi_type,
    coalesce(z.borough, 'Unknown') AS pickup_borough,
    count(*) AS trips,
    round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY t.taxi_type), 2) AS pct_of_type,
    round(avg(t.trip_distance), 2) AS avg_miles,
    round(avg(t.total_amount), 2) AS avg_total
FROM trips_clean AS t
LEFT JOIN zones AS z ON z.location_id = t.PULocationID
GROUP BY t.taxi_type, pickup_borough
ORDER BY t.taxi_type DESC, trips DESC;
