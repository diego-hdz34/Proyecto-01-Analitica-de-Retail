import pandas as pd

# 1. CARGA DE DATASETS
df_marketing = pd.read_csv('C:\\Users\\Diego Hernandez\\OneDrive\\Escritorio\\Proyecto 01 Analitica de Retail\\csvCrudos\\campanas_marketing.csv')
df_productos = pd.read_csv('C:\\Users\\Diego Hernandez\\OneDrive\\Escritorio\\Proyecto 01 Analitica de Retail\\csvCrudos\\productos.csv')
df_crm = pd.read_csv('C:\\Users\\Diego Hernandez\\OneDrive\\Escritorio\\Proyecto 01 Analitica de Retail\\csvCrudos\\interacciones_crm.csv')
df_transacciones = pd.read_csv('C:\\Users\\Diego Hernandez\\OneDrive\\Escritorio\\Proyecto 01 Analitica de Retail\\csvCrudos\\transacciones.csv')
df_devoluciones = pd.read_csv('C:\\Users\\Diego Hernandez\\OneDrive\\Escritorio\\Proyecto 01 Analitica de Retail\\csvCrudos\\devoluciones.csv')

# 2. LIMPIEZA: FALSAS CONVERSIONES DE MARKETING
df_marketing['fecha_envio'] = pd.to_datetime(df_marketing['fecha_envio'])
df_transacciones['fecha'] = pd.to_datetime(df_transacciones['fecha'])

# Buscar la fecha de la última transacción registrada por cliente
ultimas_compras = df_transacciones.groupby('cliente_id')['fecha'].max().reset_index()

# Cruzar datos de marketing con transacciones
df_marketing = df_marketing.merge(ultimas_compras, on='cliente_id', how='left')

# Modificar a False si la campaña se envió después de su última compra
mascara_falsa_conversion = (df_marketing['convertido'] == True) & (df_marketing['fecha_envio'] > df_marketing['fecha'])
df_marketing.loc[mascara_falsa_conversion, 'convertido'] = 0

# Limpiar tabla descartando la columna auxiliar de fecha
df_marketing = df_marketing.drop(columns=['fecha'])

# 3. LIMPIEZA: FORMATO DEL MARGEN EN PRODUCTOS
df_productos['margen_bruto_pct'] = pd.to_numeric(df_productos['margen_bruto_pct'], errors='coerce') / 100.0

# 4. LIMPIEZA: VALORES ATÍPICOS EN CRM
mediana_resolucion = df_crm['tiempo_respuesta_hrs'].median()
mascara_outliers = df_crm['tiempo_respuesta_hrs'] > 72
df_crm.loc[mascara_outliers, 'tiempo_respuesta_hrs'] = mediana_resolucion

# 5. LIMPIEZA: ESTANDARIZACIÓN DE DIVISA (USD)
df_transacciones.rename(columns={
    'precio_unitario': 'precio_unitario_usd', 
    'monto_neto': 'monto_neto_usd'
}, inplace=True)

df_devoluciones.rename(columns={
    'monto_devuelto': 'monto_devuelto_usd'
}, inplace=True)

df_productos.rename(columns={
    'costo': 'costo_usd', 
    'precio_lista': 'precio_lista_usd'
}, inplace=True)

# 6. EXPORTACIÓN DE LOS DATOS LIMPIOS
df_marketing.to_csv('campanas_marketing_limpio.csv', index=False)
df_productos.to_csv('productos_limpio.csv', index=False)
df_crm.to_csv('interacciones_crm_limpio.csv', index=False)
df_transacciones.to_csv('transacciones_limpio.csv', index=False)
df_devoluciones.to_csv('devoluciones_limpio.csv', index=False)

# 7. LIMPIEZA Y EXPORTACIÓN DE CLIENTES
df_clientes = pd.read_csv(r'C:\Users\Diego Hernandez\OneDrive\Escritorio\Proyecto 01 Analitica de Retail\csvCrudos\clientes.csv')
df_clientes = df_clientes.drop_duplicates()
df_clientes = df_clientes.dropna(subset=['cliente_id'])
df_clientes.to_csv('clientes_limpio.csv', index=False)
print("Archivo clientes_limpio.csv generado.")

print("Depuración finalizada. Archivos limpios generados exitosamente.")