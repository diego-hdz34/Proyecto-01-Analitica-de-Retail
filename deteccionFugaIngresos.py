import pandas as pd
import os

# 1. Preparación del Entorno
os.makedirs('resultados_fase3', exist_ok=True)
print("Cargando datos para Fase 3 (Devoluciones, CRM y Churn)...")

# Carga de datos limpios
clientes = pd.read_csv(r'C:\Users\Diego Hernandez\OneDrive\Escritorio\Proyecto 01 Analitica de Retail\csvLimpios\clientes_limpio.csv')
productos = pd.read_csv(r'C:\Users\Diego Hernandez\OneDrive\Escritorio\Proyecto 01 Analitica de Retail\csvLimpios\productos_limpio.csv')
transacciones = pd.read_csv(r'C:\Users\Diego Hernandez\OneDrive\Escritorio\Proyecto 01 Analitica de Retail\csvLimpios\transacciones_limpio.csv')
devoluciones = pd.read_csv(r'C:\Users\Diego Hernandez\OneDrive\Escritorio\Proyecto 01 Analitica de Retail\csvLimpios\devoluciones_limpio.csv')
crm = pd.read_csv(r'C:\Users\Diego Hernandez\OneDrive\Escritorio\Proyecto 01 Analitica de Retail\csvLimpios\interacciones_crm_limpio.csv')

# Convertir fecha a datetime
transacciones['fecha'] = pd.to_datetime(transacciones['fecha'])
fecha_max_global = transacciones['fecha'].max()

# 2. Análisis del Patrón de Devoluciones
print("Analizando devoluciones anómalas...")
# Cruces seguros: evitan renombrar columnas duplicadas a _x y _y
df_dev = devoluciones.merge(transacciones, on='transaccion_id', how='left', suffixes=('', '_dup'))
df_dev = df_dev.loc[:, ~df_dev.columns.str.endswith('_dup')]

df_dev = df_dev.merge(productos, on='producto_id', how='left', suffixes=('', '_dup'))
df_dev = df_dev.loc[:, ~df_dev.columns.str.endswith('_dup')]

df_dev = df_dev.merge(clientes, on='cliente_id', how='left', suffixes=('', '_dup'))
df_dev = df_dev.loc[:, ~df_dev.columns.str.endswith('_dup')]

# Calcular tasa de devoluciones por categoría y segmento
ventas_base = transacciones.merge(productos, on='producto_id', suffixes=('', '_dup'))
ventas_base = ventas_base.loc[:, ~ventas_base.columns.str.endswith('_dup')]
ventas_base = ventas_base.merge(clientes, on='cliente_id', suffixes=('', '_dup'))
ventas_base = ventas_base.loc[:, ~ventas_base.columns.str.endswith('_dup')]

total_ventas = ventas_base.groupby(['categoria', 'segmento'])['transaccion_id'].count().reset_index(name='total_compras')
total_devoluciones = df_dev.groupby(['categoria', 'segmento'])['transaccion_id'].count().reset_index(name='total_devueltos')

tasas_dev = total_ventas.merge(total_devoluciones, on=['categoria', 'segmento'], how='left').fillna(0)
tasas_dev['tasa_devolucion_pct'] = (tasas_dev['total_devueltos'] / tasas_dev['total_compras']) * 100
tasas_dev = tasas_dev.sort_values(by='tasa_devolucion_pct', ascending=False)
tasas_dev.to_csv('resultados_fase3/tasas_devolucion_categorias.csv', index=False)

# Clientes recurrentes en devoluciones (>1 devolución)
clientes_dev = df_dev.groupby('cliente_id').size().reset_index(name='cantidad_devoluciones')
clientes_dev = clientes_dev[clientes_dev['cantidad_devoluciones'] > 1].sort_values(by='cantidad_devoluciones', ascending=False)
clientes_dev.to_csv('resultados_fase3/clientes_recurrentes_devoluciones.csv', index=False)

# 3. Interacciones CRM vs Comportamiento de Compra
print("Cruzando tickets de CRM con frecuencia de compra...")
meses_totales = max(1, (fecha_max_global - transacciones['fecha'].min()).days / 30)
freq_compras = transacciones.groupby('cliente_id').size().reset_index(name='total_compras')
freq_compras['compras_por_mes'] = freq_compras['total_compras'] / meses_totales

# Identificar clientes con quejas NO resueltas
clientes_con_queja_abierta = crm[crm['resolucion'] == 'No Resuelto']['cliente_id'].unique()
freq_compras['queja_no_resuelta'] = freq_compras['cliente_id'].isin(clientes_con_queja_abierta)

impacto_crm = freq_compras.groupby('queja_no_resuelta')['compras_por_mes'].mean().reset_index()
impacto_crm.columns = ['Tuvo_Queja_No_Resuelta', 'Frecuencia_Compra_Mensual_Promedio']
impacto_crm.to_csv('resultados_fase3/impacto_crm_frecuencia.csv', index=False)

# 4. Clientes en Riesgo de Churn e Impacto Económico
print("Evaluando riesgo de Churn y proyecciones económicas...")
ultimas_compras = transacciones.groupby('cliente_id')['fecha'].max().reset_index()
ultimas_compras['dias_inactivo'] = (fecha_max_global - ultimas_compras['fecha']).dt.days

# Filtrar clientes en riesgo (> 90 días sin comprar)
clientes_riesgo = ultimas_compras[ultimas_compras['dias_inactivo'] > 90].copy()

valor_clientes = transacciones.groupby('cliente_id')['monto_neto_usd'].sum().reset_index()
clientes_riesgo = clientes_riesgo.merge(valor_clientes, on='cliente_id', how='left')
clientes_riesgo = clientes_riesgo.merge(clientes, on='cliente_id', how='left')

# Segmento de mayor valor en riesgo
segmentos_riesgo = clientes_riesgo.groupby('segmento').agg(
    clientes_en_riesgo=('cliente_id', 'count'),
    valor_historico_riesgo=('monto_neto_usd', 'sum')
).reset_index().sort_values(by='valor_historico_riesgo', ascending=False)
segmentos_riesgo.to_csv('resultados_fase3/segmentos_riesgo_churn.csv', index=False)

# Proyección a 6 meses de ingresos perdidos
clientes_riesgo['gasto_mensual_promedio'] = clientes_riesgo['monto_neto_usd'] / meses_totales
clientes_riesgo['ingreso_perdido_proyectado_6m'] = clientes_riesgo['gasto_mensual_promedio'] * 6

proyeccion_fugas = clientes_riesgo[['cliente_id', 'segmento', 'dias_inactivo', 'gasto_mensual_promedio', 'ingreso_perdido_proyectado_6m']]
proyeccion_fugas = proyeccion_fugas.sort_values(by='ingreso_perdido_proyectado_6m', ascending=False)
proyeccion_fugas.to_csv('resultados_fase3/impacto_economico_fugas.csv', index=False)

perdida_total_6m = proyeccion_fugas['ingreso_perdido_proyectado_6m'].sum()
print(f"Impacto económico total proyectado (Fugas a 6 meses): ${perdida_total_6m:,.2f}")
print("¡Fase 3 completada! Todos los datasets están listos en la carpeta 'resultados_fase3'.")