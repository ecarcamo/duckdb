SELECT
    r.taxi_type,
    r.trips AS raw_trips,
    c.trips AS clean_trips,
    r.trips - c.trips AS discarded_trips,
    round(100.0 * (r.trips - c.trips) / r.trips, 2) AS pct_discarded
FROM (SELECT taxi_type, count(*) AS trips FROM trips GROUP BY ALL) AS r
JOIN (SELECT taxi_type, count(*) AS trips FROM trips_clean GROUP BY ALL) AS c USING (taxi_type)
ORDER BY r.taxi_type DESC;
