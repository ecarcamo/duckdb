SELECT
    name AS column_name,
    count(*) FILTER (WHERE file_name LIKE '%yellow_tripdata%') AS yellow_files,
    count(*) FILTER (WHERE file_name LIKE '%green_tripdata%') AS green_files,
    min(regexp_extract(file_name, '(\d{4}-\d{2})\.parquet$', 1)) AS first_month,
    string_agg(DISTINCT type, ', ') AS physical_types
FROM parquet_schema('data/raw/*/*/*.parquet')
WHERE type IS NOT NULL
GROUP BY name
ORDER BY yellow_files + green_files DESC, column_name;
