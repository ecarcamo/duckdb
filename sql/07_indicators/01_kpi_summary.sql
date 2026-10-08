SELECT
    count(*) AS trips,
    round(sum(total_amount) / 1e6, 1) AS revenue_musd,
    round(avg(total_amount), 2) AS avg_ticket,
    count(DISTINCT source_year) AS years,
    min(make_date(source_year, source_month, 1)) AS first_month,
    max(make_date(source_year, source_month, 1)) AS last_month
FROM trips_clean;
