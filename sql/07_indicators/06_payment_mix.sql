SELECT
    CAST(source_year AS VARCHAR) AS year,
    CASE payment_type
        WHEN 1 THEN 'Tarjeta'
        WHEN 2 THEN 'Efectivo'
        WHEN 0 THEN 'Flex fare'
        ELSE 'Otro o nulo'
    END AS payment,
    round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY source_year), 2) AS pct_of_trips
FROM trips_clean
GROUP BY source_year, payment
ORDER BY year, pct_of_trips DESC;
