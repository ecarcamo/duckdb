SUMMARIZE SELECT *
FROM read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true);
