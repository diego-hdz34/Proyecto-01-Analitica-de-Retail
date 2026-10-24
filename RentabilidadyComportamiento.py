import pandas as pd
import os

# 1. Preparación del Entorno
os.makedirs('resultados_fase2', exist_ok=True)
print("Cargando y consolidando datos...")

# Carga de datos limpios desde el directorio raíz actual
clientes = pd.read_csv(r'C:\Users\Diego Hernandez\OneDrive\Escritorio\Proyecto 01 Analitica de Retail\csvLimpios\clientes_limpio.csv')
productos = pd.read_csv(r'C:\Users\Diego Hernandez\OneDrive\Escritorio\Proyecto 01 Analitica de Retail\csvLimpios\productos_limpio.csv')
transacciones = pd.read_csv(r'C:\Users\Diego Hernandez\OneDrive\Escritorio\Proyecto 01 Analitica de Retail\csvLimpios\transacciones_limpio.csv')

# 2. Consolidación (Merge modelo estrella)
df = transacciones.merge(clientes, on='cliente_id', how='left')
df = df.merge(productos, on='producto_id', how='left')
df['fecha'] = pd.to_datetime(df['fecha'])

# Calcular costos y márgenes usando las divisas estandarizadas
df['costo_total'] = df['cantidad'] * df['costo_usd']
df['margen_bruto'] = df['monto_neto_usd'] - df['costo_total']

# 3. Rentabilidad por Segmentos, Categorías y Canales
print("Calculando rentabilidad...")
rentabilidad = df.groupby(['segmento', 'categoria', 'canal'])['margen_bruto'].sum().reset_index()
rentabilidad = rentabilidad.sort_values(by='margen_bruto', ascending=False)
rentabilidad.to_csv('resultados_fase2/rentabilidad_segmentos.csv', index=False)

# 4. Customer Lifetime Value (CLV) y Detección de Declive
print("Calculando CLV y tendencias...")
metricas_clv = df.groupby('segmento').agg(
    ingresos_totales=('monto_neto_usd', 'sum'),
    total_pedidos=('transaccion_id', 'nunique'),
    clientes_unicos=('cliente_id', 'nunique')
).reset_index()

metricas_clv['ticket_promedio'] = metricas_clv['ingresos_totales'] / metricas_clv['total_pedidos']
metricas_clv['frecuencia_anual'] = (metricas_clv['total_pedidos'] / metricas_clv['clientes_unicos']) / 2
metricas_clv['CLV_estimado'] = metricas_clv['ticket_promedio'] * metricas_clv['frecuencia_anual'] * 3

# Detección de declive (Últimos 6 meses vs 6 meses previos)
fecha_max = df['fecha'].max()
hace_6_meses = fecha_max - pd.DateOffset(months=6)
hace_12_meses = fecha_max - pd.DateOffset(months=12)

ventas_rec = df[df['fecha'] > hace_6_meses].groupby('segmento')['monto_neto_usd'].sum()
ventas_prev = df[(df['fecha'] <= hace_6_meses) & (df['fecha'] > hace_12_meses)].groupby('segmento')['monto_neto_usd'].sum()

tendencia = ((ventas_rec - ventas_prev) / ventas_prev * 100).fillna(0).reset_index()
tendencia.columns = ['segmento', 'variacion_porcentual_ventas']

clv_final = metricas_clv.merge(tendencia, on='segmento', how='left')
clv_final.to_csv('resultados_fase2/clv_y_tendencias.csv', index=False)

# 5. Estacionalidad de las Ventas
print("Analizando estacionalidad...")
df['mes_año'] = df['fecha'].dt.to_period('M')
estacionalidad = df.groupby(['mes_año', 'categoria', 'canal'])['cantidad'].sum().reset_index()
estacionalidad.to_csv('resultados_fase2/estacionalidad_ventas.csv', index=False)

# 6. Efecto Real de los Descuentos
print("Evaluando impacto de descuentos...")
df['tiene_descuento'] = df['descuento'] > 0
analisis_descuentos = df.groupby('tiene_descuento').agg(
    volumen_unidades_vendidas=('cantidad', 'sum'),
    margen_bruto_total=('margen_bruto', 'sum'),
    margen_promedio_por_item=('margen_bruto', 'mean')
).reset_index()
analisis_descuentos.to_csv('resultados_fase2/impacto_descuentos.csv', index=False)

print("¡Proceso completado! Archivos generados en la carpeta 'resultados_fase2'.")