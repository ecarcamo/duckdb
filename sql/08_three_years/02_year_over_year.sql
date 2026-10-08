WITH monthly AS (
    SELECT
        taxi_type,
        source_year AS year,
        source_month AS month,
        count(*) / count(DISTINCT CAST(pickup_datetime AS DATE)) AS trips_per_day,
        avg(total_amount) AS avg_ticket
    FROM trips_clean
    GROUP BY ALL
)
SELECT
    taxi_type,
    year,
    month,
    round(trips_per_day, 0) AS trips_per_day,
    round(100.0 * (trips_per_day / lag(trips_per_day) OVER w - 1), 1) AS pct_change_trips,
    round(avg_ticket, 2) AS avg_ticket,
    round(100.0 * (avg_ticket / lag(avg_ticket) OVER w - 1), 1) AS pct_change_ticket
FROM monthly
WINDOW w AS (PARTITION BY taxi_type, month ORDER BY year)
ORDER BY taxi_type DESC, month, year;
