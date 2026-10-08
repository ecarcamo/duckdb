SELECT
    taxi_type,
    source_month,
    coalesce(request_source, '(nulo)') AS request_source,
    count(*) AS trips
FROM trips
WHERE source_year = 2026
GROUP BY ALL
ORDER BY taxi_type DESC, source_month, trips DESC;
