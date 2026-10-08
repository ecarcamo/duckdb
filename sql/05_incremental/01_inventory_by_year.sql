SELECT
    split_part(file_name, '/', 3) AS taxi_type,
    CAST(split_part(file_name, '/', 4) AS INTEGER) AS year,
    count(*) AS files,
    sum(num_rows) AS rows_in_metadata
FROM parquet_file_metadata('data/raw/*/*/*.parquet')
GROUP BY ALL
ORDER BY taxi_type DESC, year;
