PIVOT (
    SELECT
        name AS column_name,
        split_part(file_name, '/', 3) || '_' || split_part(file_name, '/', 4) AS taxi_year
    FROM parquet_schema('data/raw/*/*/*.parquet')
    WHERE type IS NOT NULL
)
ON taxi_year
USING count(*)
ORDER BY column_name;
