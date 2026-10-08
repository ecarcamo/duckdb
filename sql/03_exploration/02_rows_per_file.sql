SELECT
    regexp_extract(file_name, '([a-z]+_tripdata_\d{4}-\d{2})\.parquet$', 1) AS file,
    num_rows,
    num_row_groups,
    round(sum(total_compressed_size) / 1024 / 1024, 1) AS compressed_mib,
    round(sum(total_uncompressed_size) / 1024 / 1024, 1) AS uncompressed_mib
FROM parquet_metadata('data/raw/*/*/*.parquet')
JOIN parquet_file_metadata('data/raw/*/*/*.parquet') USING (file_name)
GROUP BY ALL
ORDER BY file;
