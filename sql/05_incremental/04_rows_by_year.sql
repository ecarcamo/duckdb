SELECT
    r.taxi_type,
    r.source_year AS year,
    r.trips AS raw_trips,
    c.trips AS clean_trips,
    round(100.0 * (r.trips - c.trips) / r.trips, 2) AS pct_discarded,
    r.first_pickup,
    r.last_pickup
FROM (
    SELECT taxi_type, source_year, count(*) AS trips, min(pickup_datetime) AS first_pickup, max(pickup_datetime) AS last_pickup
    FROM trips
    GROUP BY ALL
) AS r
JOIN (
    SELECT taxi_type, source_year, count(*) AS trips
    FROM trips_clean
    GROUP BY ALL
) AS c USING (taxi_type, source_year)
ORDER BY r.taxi_type DESC, year;
