# Dashboard · Clasificación de la cobertura forestal (Covertype)

Dashboard interactivo en Dash con tres pestañas: contexto y territorio, análisis
exploratorio y modelos de *machine learning* (modelo base, benchmark de 7 algoritmos,
optimización de hiperparámetros, finalista y comparación estadística, interpretabilidad
con SHAP y eficiencia computacional).

## Ejecutar en local

```bash
pip install -r requirements.txt
python app.py            # http://127.0.0.1:8050
```

## Estructura

```
app.py               layout y callbacks
datos_dashboard.py   carga de datos, constantes y plantilla gráfica
datos/               archivos livianos que usa el dashboard (≈ 3 MB)
assets/              estilos, Bootstrap y la ilustración del encabezado
preparar_datos.py    regenera datos/ a partir del proyecto (no se usa en producción)
```

`datos/` se genera con `python dashboard/preparar_datos.py` desde la raíz del proyecto,
después de correr los scripts del benchmark. Usa la misma partición, el mismo
preprocesamiento y la misma semilla que el libro, por lo que todas las cifras coinciden.

## Despliegue en Render

1. Subir el contenido de esta carpeta a un repositorio de GitHub.
2. En Render: **New → Web Service**, conectar el repositorio.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:server --workers 1 --timeout 120`

(El archivo `render.yaml` ya trae esta configuración.)
