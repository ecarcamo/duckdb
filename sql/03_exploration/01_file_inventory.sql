SELECT
    split_part(file, '/', 3) AS taxi_type,
    split_part(file, '/', 4) AS year,
    count(*) AS files,
    min(regexp_extract(file, '(\d{4}-\d{2})\.parquet$', 1)) AS first_month,
    max(regexp_extract(file, '(\d{4}-\d{2})\.parquet$', 1)) AS last_month
FROM glob('data/raw/*/*/*.parquet')
GROUP BY ALL
ORDER BY ALL;
