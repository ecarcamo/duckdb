SELECT
    coalesce(split_part(filename, '/', 3), 'total') AS taxi_type,
    count(*) AS trips
FROM read_parquet('data/raw/*/*/*.parquet', union_by_name = true, filename = true)
GROUP BY ROLLUP (split_part(filename, '/', 3))
ORDER BY trips;
