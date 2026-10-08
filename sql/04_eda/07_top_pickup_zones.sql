SELECT *
FROM (
    SELECT
        t.taxi_type,
        z.borough,
        z.zone,
        count(*) AS trips,
        round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY t.taxi_type), 2) AS pct_of_type,
        row_number() OVER (PARTITION BY t.taxi_type ORDER BY count(*) DESC) AS rank
    FROM trips_clean AS t
    JOIN zones AS z ON z.location_id = t.PULocationID
    GROUP BY t.taxi_type, z.borough, z.zone
)
WHERE rank <= 10
ORDER BY taxi_type DESC, rank;
