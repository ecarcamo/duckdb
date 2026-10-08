WITH classified AS (
    SELECT
        t.taxi_type,
        CASE
            WHEN 'Airports' IN (pu.service_zone, do_.service_zone) OR 'EWR' IN (pu.service_zone, do_.service_zone)
                THEN 'Aeropuerto'
            ELSE 'Urbano'
        END AS trip_kind,
        t.total_amount,
        t.trip_distance,
        t.duration_minutes
    FROM trips_clean AS t
    LEFT JOIN zones AS pu ON pu.location_id = t.PULocationID
    LEFT JOIN zones AS do_ ON do_.location_id = t.DOLocationID
)
SELECT
    taxi_type,
    trip_kind,
    count(*) AS trips,
    round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY taxi_type), 2) AS pct_trips,
    round(100.0 * sum(total_amount) / sum(sum(total_amount)) OVER (PARTITION BY taxi_type), 2) AS pct_revenue,
    round(avg(total_amount), 2) AS avg_total,
    round(avg(trip_distance), 2) AS avg_miles,
    round(avg(duration_minutes), 1) AS avg_minutes
FROM classified
GROUP BY taxi_type, trip_kind
ORDER BY taxi_type DESC, trip_kind;
