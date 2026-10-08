SELECT
    z.zone || ' (' || z.borough || ')' AS zone,
    count(*) AS trips
FROM trips_clean AS t
JOIN zones AS z ON z.location_id = t.PULocationID
WHERE z.borough NOT IN ('Unknown', 'N/A')
GROUP BY ALL
ORDER BY trips DESC
LIMIT 10;
