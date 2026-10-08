SELECT
    taxi_type,
    CASE payment_type
        WHEN 0 THEN 'Flex fare / desconocido'
        WHEN 1 THEN 'Tarjeta de crédito'
        WHEN 2 THEN 'Efectivo'
        WHEN 3 THEN 'Sin cargo'
        WHEN 4 THEN 'Disputa'
        WHEN 5 THEN 'Desconocido'
        WHEN 6 THEN 'Viaje anulado'
        ELSE 'Nulo'
    END AS payment,
    count(*) AS trips,
    round(100.0 * count(*) / sum(count(*)) OVER (PARTITION BY taxi_type), 2) AS pct_of_type,
    round(avg(total_amount), 2) AS avg_total,
    round(avg(tip_amount), 2) AS avg_tip
FROM trips_clean
GROUP BY taxi_type, payment
ORDER BY taxi_type DESC, trips DESC;
