# Ejercicio 4 — Análisis exploratorio con DuckDB

Notebook ejecutado (con gráficas): [notebooks/04_eda.ipynb](../notebooks/04_eda.ipynb).
Consultas: [sql/04_eda/](../sql/04_eda/).

**Datos:** viajes de enero a agosto de 2026, leídos directamente de los Parquet
mediante la vista `trips_clean` (reglas del Ejercicio 3): 28,593,831 viajes
amarillos y 322,606 verdes. Las zonas se obtienen de la vista `zones`
(`taxi_zone_lookup.csv`).

Durante este ejercicio se encontró que el proveedor 7 registra la misma hora de
abordaje y descenso en todos sus viajes, lo que hacía que `trips_clean` lo
eliminara completo; la vista se corrigió antes de calcular los resultados
(ver consulta 18 del Ejercicio 3).

## 4.1 Preguntas y su justificación

| # | Pregunta | Justificación a partir de los datos |
|---|---|---|
| P1 | ¿Cómo cambia el volumen diario de viajes de un mes a otro y cuánto ingreso generan? | Los datos llegan por archivos mensuales y el volumen por archivo varía entre 3.3 y 4.1 millones de filas (Ejercicio 3); conviene saber si es estacionalidad o diferencia de días. |
| P2 | ¿En qué horas y días se concentra la demanda de cada tipo de taxi? | Cada viaje tiene fecha y hora exactas de abordaje; es la dimensión temporal más fina disponible. |
| P3 | ¿Cómo es un viaje típico (distancia, duración, velocidad, monto, pasajeros)? | `SUMMARIZE` mostró colas extremas, así que se necesitan medianas y percentiles, no promedios. |
| P4 | ¿Cómo se distribuyen las distancias? | La mediana es de 1.9 millas pero el máximo limpio es 100: hay que ver la forma de la distribución. |
| P5 | ¿Cómo se distribuye el monto total pagado? | `total_amount` es la medida de ingreso elegida en el Ejercicio 3. |
| P6 | ¿En qué distritos inician los viajes de cada tipo? | Los taxis verdes tienen restringido recoger pasajeros en el centro de Manhattan; los datos deberían reflejarlo. |
| P7 | ¿Cuáles son las zonas con más abordajes? | `PULocationID` tiene 265 zonas; la tabla de zonas permite nombrarlas. |
| P8 | ¿Cómo pagan los pasajeros y cuánto pagan con cada medio? | `payment_type` tiene un 25 % de registros *flex fare* (código 0) en los amarillos. |
| P9 | ¿Cuánta propina se deja con tarjeta y varía según la hora? | Las propinas solo se registran en pagos con tarjeta. |
| P10 | ¿Qué peso tienen los viajes al aeropuerto en volumen e ingresos? | JFK aparece entre las zonas con más abordajes y existe una tarifa fija (`RatecodeID = 2`). |
| P11 | ¿A qué proporción de viajes se le cobra el cargo de congestión de Manhattan (CBD)? | `cbd_congestion_fee` es una columna nueva (2025 en adelante) presente en todos los archivos de 2026. |
| P12 | ¿Cuántos valores atípicos quedan después de la limpieza? | La limpieza solo quitó lo imposible; quedan valores posibles pero raros. |
| P13 | ¿Los proveedores reportan los montos de forma consistente? | La muestra del Ejercicio 3 mostró que el proveedor 1 incluye los recargos dentro de `extra`. |

## 4.2 a 4.4 Consultas y resultados

Todas las consultas leen `trips_clean` (y `zones` cuando hace falta el nombre de
la zona), es decir, los archivos `data/raw/*/*/*.parquet`. Tiempo de cada
consulta sobre 28.9 millones de viajes: entre 0.25 y 5 segundos.

### P1 — Volumen mensual (`01_monthly_volume.sql`)

Viajes, viajes por día con actividad, ingreso total y monto promedio por tipo y mes.

| Mes | Amarillo: viajes/día | Amarillo: monto prom. | Verde: viajes/día | Verde: monto prom. |
|---|---|---|---|---|
| Ene | 114,854 | 29.62 | 1,249 | 24.29 |
| Feb | 116,072 | 30.40 | 1,276 | 24.40 |
| Mar | 122,923 | 30.21 | 1,370 | 24.91 |
| Abr | 124,106 | 30.05 | 1,411 | 25.37 |
| May | **127,844** | 30.50 | 1,387 | 25.85 |
| Jun | 123,173 | 30.55 | **1,413** | 26.13 |
| Jul | 109,272 | 30.09 | 1,269 | 26.21 |
| Ago | 103,349 | 30.10 | 1,247 | 26.46 |

**Interpretación:** la demanda sube durante la primavera y cae en julio y
agosto; en agosto los amarillos tienen 19 % menos viajes diarios que en mayo. El
monto promedio de los amarillos es estable (≈ 30 USD), mientras que el de los
verdes sube de forma continua (24.29 → 26.46, +9 %). Los ingresos de los
amarillos van de 96 a 121 millones de USD por mes.

### P2 — Hora y día de la semana (`02_hour_weekday.sql`)

Viajes promedio por hora para cada combinación de día (`isodow`, 1 = lunes) y hora.

**Interpretación:**
- **Amarillos:** el mínimo es a las 3–4 a. m. de lunes a jueves (menos de 700
  viajes por hora). El máximo es entre las 17 y las 22 h, con más de 8,000 viajes
  por hora los miércoles, jueves y sábados. Los viernes y sábados la noche se extiende: a la
  medianoche del sábado hay 6,626 viajes por hora y a la 1 a. m. del domingo
  5,617, de 2 a 7 veces lo que se ve a esa hora de lunes a jueves.
- **Verdes:** patrón de traslado laboral, con picos a las 8–9 h (≈ 100 viajes
  por hora) y a las 16–18 h (hasta 128) de lunes a viernes, y mucha menos
  actividad en la noche y el fin de semana.

### P3 — Perfil del viaje típico (`03_trip_profile.sql`)

| Métrica | Amarillo | Verde |
|---|---|---|
| Distancia mediana | 1.92 mi | 2.14 mi |
| Distancia p90 | 8.68 mi | 7.51 mi |
| Duración mediana | 14.1 min | 13.3 min |
| Duración p90 | 33.5 min | 32.6 min |
| Velocidad mediana | 9.3 mph | 10.1 mph |
| Monto mediano | 23.58 USD | 20.52 USD |
| Monto p90 | 54.65 USD | 44.85 USD |
| Pasajeros promedio | 1.25 | 1.30 |
| Viajes con un pasajero | 82.3 % | 82.8 % |

**Interpretación:** el viaje típico es corto (2 millas, 14 minutos) y de una
sola persona. La velocidad mediana de menos de 10 mph refleja el tráfico de
Manhattan. Los verdes son algo más largos en la mediana pero tienen una cola
más corta (menos viajes de aeropuerto).

### P4 — Distribución de distancias (`04_distance_distribution.sql`)

| Millas | Amarillo % | Verde % |
|---|---|---|
| 0–1 | 21.04 | 13.77 |
| 1–2 | 30.31 | 32.51 |
| 2–3 | 15.73 | 20.02 |
| 3–5 | 13.35 | 15.50 |
| 5–10 | 11.93 | 12.44 |
| 10–20 | 6.79 | 5.23 |
| 20+ | 0.85 | 0.53 |

**Interpretación:** distribución asimétrica a la derecha. El 51 % de los viajes
amarillos mide menos de 2 millas; uno de cada cinco, menos de una milla (viajes
cortos dentro de Midtown). El 7.6 % supera las 10 millas, que es donde están los
viajes de aeropuerto.

### P5 — Distribución del monto total (`05_fare_distribution.sql`)

Intervalos de 5 USD hasta 150.

**Interpretación:** la moda está entre 15 y 20 USD para ambos tipos (22.4 % de
los amarillos y 23.7 % de los verdes). Los amarillos tienen una meseta entre 80
y 105 USD que no aparece en los verdes: corresponde a los 667,290 viajes con
`RatecodeID = 2` (tarifa fija de 70 USD entre JFK y Manhattan), cuyo total
promedio, con recargos, peajes y propina, es 94.87 USD.

### P6 — Distrito de abordaje (`06_borough_by_type.sql`)

| Distrito | Amarillo % | Verde % |
|---|---|---|
| Manhattan | 86.72 | 59.51 |
| Queens | 8.81 | 22.04 |
| Brooklyn | 3.56 | 15.78 |
| Bronx | 0.77 | 2.48 |

**Interpretación:** los amarillos son un servicio de Manhattan. Los que salen de
Queens recorren en promedio 11.26 millas y cuestan 67.65 USD porque en su mayoría
son salidas de JFK y LaGuardia. Los verdes reparten su operación entre los
distritos exteriores y el norte de Manhattan.

### P7 — Zonas con más abordajes (`07_top_pickup_zones.sql`)

- **Amarillos:** Upper East Side South (4.47 %), Midtown Center (4.16 %), Upper
  East Side North (3.99 %) y JFK Airport (3.97 %); las diez primeras suman 34 %
  de los viajes. Nueve de las diez están en Manhattan.
- **Verdes:** East Harlem North (26.98 %) y East Harlem South (12.99 %) suman el
  40 % de los viajes; luego Forest Hills, Central Park y Morningside Heights.

**Interpretación:** la demanda de los verdes está mucho más concentrada: dos
zonas contiguas del norte de Manhattan explican dos de cada cinco viajes.

### P8 — Medio de pago (`08_payment_mix.sql`)

| Medio | Amarillo % | Monto prom. | Verde % | Monto prom. |
|---|---|---|---|---|
| Tarjeta de crédito | 65.64 | 29.97 | 65.62 | 25.66 |
| Flex fare / desconocido (0) | 24.63 | 32.43 | — | — |
| Efectivo | 9.10 | 25.92 | 19.41 | 20.84 |
| Nulo | — | — | 14.66 | 30.88 |
| Disputa | 0.42 | 28.94 | 0.08 | 19.59 |
| Sin cargo | 0.21 | 24.29 | 0.22 | 17.67 |

**Interpretación:** dos de cada tres viajes se pagan con tarjeta en ambos tipos.
El efectivo pesa el doble en los verdes (19.4 % frente a 9.1 %), coherente con
su presencia en barrios fuera del centro. Los viajes *flex fare* tienen el
monto promedio más alto (32.43 USD) y casi no registran propina (0.40 USD), lo
que confirma que son un tipo de registro distinto.

### P9 — Propinas con tarjeta (`09_tip_behavior.sql`)

**Interpretación:** con tarjeta, entre el 84 % y el 94 % de los viajes amarillos
deja propina, salvo de 4 a 6 a. m. (73–78 %). La propina equivale al 21 % de la
tarifa durante el día y sube a 23.5 % entre las 18 y 19 h; el mínimo es 15.8 % a
las 5 a. m. Los verdes siguen el mismo patrón con valores ligeramente menores en
la noche.

### P10 — Viajes de aeropuerto (`10_airport_trips.sql`)

| Tipo | % de viajes | % de ingresos | Monto prom. | Millas prom. | Minutos prom. |
|---|---|---|---|---|---|
| Amarillo — aeropuerto | 8.15 | 21.04 | 77.95 | 12.94 | 37.7 |
| Amarillo — urbano | 91.85 | 78.96 | 25.96 | 2.67 | 15.9 |
| Verde — aeropuerto | 3.34 | 6.36 | 48.44 | 7.32 | 21.0 |
| Verde — urbano | 96.66 | 93.64 | 24.67 | 3.21 | 17.1 |

**Interpretación:** un viaje amarillo de aeropuerto vale tres veces uno urbano;
con 8 % de los viajes genera la quinta parte del ingreso.

### P11 — Cargo de congestión CBD (`11_cbd_congestion_fee.sql`)

**Interpretación:** entre el 67 % y el 77 % de los viajes amarillos paga el cargo
de 0.75 USD por entrar a la zona de congestión de Manhattan (al sur de la calle
60), con un aumento en junio a agosto. Solo entre el 7 % y el 10 % de los verdes
lo paga. Los amarillos aportan cerca de 2 millones de USD mensuales por este
concepto.

### P12 — Valores atípicos (`12_outliers.sql`)

| Métrica | Amarillo | Verde |
|---|---|---|
| Límite superior IQR del monto total | 59.90 USD | 51.57 USD |
| Viajes sobre ese límite | 2,442,689 (8.54 %) | 21,394 (6.63 %) |
| Velocidad > 80 mph | 7,187 | 1,037 |
| Velocidad < 1 mph | 173,556 | 774 |
| Tarifa > 50 USD por milla | 302,311 | 3,873 |

**Interpretación:** los atípicos por IQR del monto no son errores: son
principalmente viajes de aeropuerto (P10), por lo que no se eliminan. Las
velocidades mayores a 80 mph sí son registros con distancia o tiempo erróneos,
pero son menos del 0.03 %. Los viajes de menos de 1 mph y los de más de
50 USD por milla corresponden a trayectos muy cortos con tarifa mínima o
recargos fijos (un viaje de 0.1 millas cuesta al menos la bajada de bandera y
los recargos) y a viajes atascados en tráfico.

### P13 — Consistencia de montos por proveedor (`13_vendor_consistency.sql`)

| Tipo | Proveedor | Viajes | Coinciden con recargos | Coinciden sin recargos |
|---|---|---|---|---|
| Amarillo | 1 | 5,373,610 | 13.80 % | 83.90 % |
| Amarillo | 2 | 22,801,117 | 76.33 % | 4.86 % |
| Amarillo | 6 | 58,744 | 0.00 % | 0.00 % |
| Amarillo | 7 | 360,360 | 57.06 % | 1.50 % |
| Verde | 1 | 26,881 | 2.74 % | 4.01 % |
| Verde | 2 | 261,252 | 98.42 % | 67.09 % |
| Verde | 6 | 34,473 | 0.00 % | 0.00 % |

**Interpretación:** cada proveedor reporta los recargos de forma distinta. El
proveedor 1 los incluye dentro de `extra` (coincide sin sumarlos), el 2 los
reporta por separado y el 6 reporta una tarifa simbólica (2.90 USD) que no
explica el total. Por eso el análisis usa `total_amount` y no reconstruye el
ingreso sumando componentes.

## 4.5 Hallazgos relevantes

1. **Los viajes de aeropuerto generan una quinta parte del ingreso.** Son el
   8.2 % de los viajes amarillos y el 21.0 % de sus ingresos (77.95 USD de
   promedio contra 25.96 USD de un viaje urbano). La tarifa fija de JFK produce
   una meseta visible entre 80 y 105 USD en la distribución de montos y explica
   la mayoría de los atípicos por IQR.
2. **Amarillos y verdes atienden mercados distintos.** El 86.7 % de los viajes
   amarillos empieza en Manhattan y al 67–77 % se le cobra el cargo CBD; los
   verdes se concentran en East Harlem (40 % de los viajes), Queens y Brooklyn,
   y solo al 7–10 % se le cobra ese cargo. Los verdes usan el doble de efectivo.
3. **Patrones horarios opuestos.** El amarillo es un servicio de tarde y noche,
   con viernes y sábados activos hasta la madrugada; el verde sigue un patrón de
   traslado al trabajo con picos a las 8 y a las 17 horas de lunes a viernes.
4. **La demanda cae en verano.** Los viajes amarillos diarios bajan 19 % de mayo
   a agosto, mientras el monto promedio por viaje se mantiene en 30 USD.
5. **La calidad de los datos depende del proveedor.** Una cuarta parte de los
   viajes amarillos son registros *flex fare* sin pasajeros ni tarifa, el
   proveedor 7 no registra la hora de descenso y los proveedores reportan los
   recargos de maneras incompatibles. Analizar sin revisar el proveedor habría
   eliminado 367 mil viajes válidos o mezclado componentes de tarifa.
