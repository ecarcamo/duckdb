SUMMARIZE SELECT *
FROM read_parquet('data/raw/green/*/*.parquet', union_by_name = true);
