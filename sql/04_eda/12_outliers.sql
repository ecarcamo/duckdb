WITH metrics AS (
    SELECT
        taxi_type,
        trip_distance / (duration_minutes / 60) AS mph,
        fare_amount / trip_distance AS fare_per_mile,
        total_amount
    FROM trips_clean
),
limits AS (
    SELECT
        taxi_type,
        quantile_cont(total_amount, 0.25) AS q1,
        quantile_cont(total_amount, 0.75) AS q3
    FROM metrics
    GROUP BY taxi_type
)
SELECT
    m.taxi_type,
    count(*) AS trips,
    round(l.q3 + 1.5 * (l.q3 - l.q1), 2) AS total_iqr_upper_limit,
    count(*) FILTER (WHERE m.total_amount > l.q3 + 1.5 * (l.q3 - l.q1)) AS total_above_iqr,
    round(100.0 * count(*) FILTER (WHERE m.total_amount > l.q3 + 1.5 * (l.q3 - l.q1)) / count(*), 2) AS pct_total_above_iqr,
    count(*) FILTER (WHERE m.mph > 80) AS speed_over_80mph,
    count(*) FILTER (WHERE m.mph < 1) AS speed_under_1mph,
    count(*) FILTER (WHERE m.fare_per_mile > 50) AS fare_over_50_per_mile
FROM metrics AS m
JOIN limits AS l USING (taxi_type)
GROUP BY m.taxi_type, l.q1, l.q3
ORDER BY m.taxi_type DESC;
