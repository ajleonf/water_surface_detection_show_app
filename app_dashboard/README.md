# Water Surface Detection — App (app_inteligence)

Resumen del dashboard y archivos creados en `wds_dashboard.ipynb`.

## Qué hay en esta carpeta
- `app.py` — Aplicación principal construida con Streamlit + Plotly. Contiene la lógica para cargar geometrías, leer la base de datos SQLite, generar el mapa mundial interactivo y las visualizaciones (series temporales, análisis comparativo, estadísticas, análisis mensual) y un panel lateral con filtros.
- `wds_dashboard.ipynb` — Notebook con documentación, instrucciones, celdas de verificación y fragmentos de código usados para generar y explicar `app.py`.
- `geometries/` — Carpeta con los 76 archivos `.geojson` (cada uno nombrado por su `loc` id). Cada GeoJSON incluye propiedades como `RAM_NAME`/`ram_name`.
- `db_1.db` — Base de datos SQLite (ya presente) con la tabla `water_surface_detection_v3` que contiene las columnas esperadas (`loc`, `sat_id`, `time`/`timestamp`, `area_km2`, `ndwi_area_km2`, etc.).
- `requirements.txt` — Lista de dependencias usadas por el dashboard (Streamlit, Plotly, Pandas, Geopandas, Rasterio, etc.).

> Nota: algunos archivos (modelo, data) pueden estar en subcarpetas o en el nivel superior del repo. Asegúrate de que `app.py`, `db_1.db` y `geometries/` estén en la misma carpeta raíz del runtime (o actualiza `app.py` con rutas absolutas si es necesario).

## Funcionalidades principales del dashboard
- Mapa mundial interactivo con zoom y marcadores por cada ubicación (76). El popup/hover muestra el `Nombre Ramsar` (campo `ram_name`), ID (`loc`), número de observaciones y área promedio.
- Carga automática de todas las geometrías `.geojson` y cálculo de centroides para posicionar marcadores.
- Carga y filtrado de datos desde la tabla `water_surface_detection_v3` en `db_1.db` (filtrado por `error`/`error_vis`, filtros de fecha y por satélite en el sidebar).
- Selector de ubicaciones mejorado que muestra `ID - Nombre Ramsar`, búsqueda por ID y búsqueda parcial por nombre (case-insensitive).
- Vista detallada por ubicación con:
  - Encabezado con el nombre Ramsar y el ID.
  - Series temporales con 3 líneas: Sentinel-1 (`area_km2` para `sat_id == 'S1_GRD'`), Landsat (`area_km2` para `sat_id != 'S1_GRD'`) y NDWI (`ndwi_area_km2`).
  - Análisis comparativo (boxplots + correlación NDWI vs Clasificación).
  - Análisis mensual (promedios por mes por método).
  - Tarjetas de estadísticas (conteos, promedios, máximos, mínimos) por sensor.
- Integración (opcional) para mostrar importancias de features si existe un modelo ExtraTrees cargado (`joblib`), con gráfico de importancias.

## Manejo de codificaciones GeoJSON
`app.py` incluye lectura robusta de GeoJSON tratando codificaciones comunes (UTF-8 por defecto con fallback a `cp1252`/`latin-1`) para asegurarse de que campos con caracteres españoles (ej. `Lagunas de Alcázar de San Juan (Yeguas y Camino de Villafranca)`) se lean correctamente.

## Requisitos y dependencias
Instalar dependencias (recomendado en un virtualenv o conda):

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

(En Windows algunos paquetes geo como `geopandas`/`rasterio` pueden ser más sencillos de instalar con `conda`/`mamba` usando `-c conda-forge`).

## Cómo ejecutar el dashboard
Abrir una terminal en esta carpeta (`app_inteligence`) y ejecutar:

```bash
streamlit run app.py
```

El dashboard abrirá en `http://localhost:8501`.

## Archivos de interés y rutas internas
- `app.py` — lógica principal, leer `db_1.db` y `geometries/` desde `os.getcwd()` por defecto.
- `requirements.txt` — lista de paquetes necesarios.
- `model/` (opcional) — si existe, colocar el archivo `model_extratrees.pkl` u otro modelo aquí para que `app.py` lo cargue y muestre importancias.

## Notas operativas y recomendaciones
- Verifica que los `loc` en `db_1.db` coincidan con los nombres de los archivos `.geojson` (p. ej. `1262` ↔ `1262.geojson`).
- Si el campo con el nombre Ramsar aparece con distinta clave (`ram_name` vs `RAM_NAME`), `app.py` intenta leer ambas variantes; revisa los GeoJSON si hay inconsistencias.
- Si ves problemas de visualización de texto blanco sobre fondo blanco, el CSS en `app.py` fue ajustado para mejorar contraste de métricas.
- Para instalaciones en Windows con problemas en geolibs, usa `conda create -n wsd python=3.11` y `conda install geopandas rasterio -c conda-forge`.

## Contacto
Si necesitas que adapte rutas, nombres de columnas (por ejemplo `time` vs `timestamp`) o añada soporte para otras tablas/columnas, describe el cambio y lo actualizo en `app.py`.

---

_Pequeña guía rápida:_ 1) revisar `requirements.txt`, 2) instalar dependencias, 3) ejecutar `streamlit run app.py`, 4) explorar el mapa y seleccionar ubicaciones.
