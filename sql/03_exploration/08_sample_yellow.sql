SELECT *
FROM read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true)
USING SAMPLE reservoir(5 ROWS) REPEATABLE (42);
