SELECT
    name AS column_name,
    string_agg(DISTINCT type, ', ') AS physical_types,
    count(DISTINCT type) AS type_count
FROM parquet_schema('data/raw/*/*/*.parquet')
WHERE type IS NOT NULL
GROUP BY name
HAVING count(DISTINCT type) > 1
ORDER BY column_name;
