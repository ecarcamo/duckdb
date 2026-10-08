WITH classified AS (
    SELECT
        t.source_year,
        t.total_amount,
        'Airports' IN (pu.service_zone, do_.service_zone)
            OR 'EWR' IN (pu.service_zone, do_.service_zone) AS is_airport
    FROM trips_clean AS t
    LEFT JOIN zones AS pu ON pu.location_id = t.PULocationID
    LEFT JOIN zones AS do_ ON do_.location_id = t.DOLocationID
)
SELECT
    CAST(source_year AS VARCHAR) AS year,
    round(100.0 * count(*) FILTER (WHERE is_airport) / count(*), 2) AS pct_trips,
    round(100.0 * sum(total_amount) FILTER (WHERE is_airport) / sum(total_amount), 2) AS pct_revenue
FROM classified
GROUP BY source_year
ORDER BY year;
