"""
Water Surface Detection Dashboard
Interactive Global Monitoring System
Author: Expert Data Visualization Team
Date: October 2025
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import geopandas as gpd
import json
import os
from datetime import datetime
from sqlalchemy import create_engine
import numpy as np

# ==================== CONFIGURACIÓN DE LA PÁGINA ====================
st.set_page_config(
    page_title="Water Surface Detection Dashboard",
    page_icon="https://img.icons8.com/fluency/96/000000/water.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== ESTILOS PERSONALIZADOS ====================
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #798EA8;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric label {
        color: #95A6BF !important;
        font-weight: 600 !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #1f77b4 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    .stMetric [data-testid="stMetricDelta"] {
        color: #27ae60 !important;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    h1 {
        color: #C5D0FA;
        font-weight: 700;
    }
    h2 {
        color: #95A6BF;
        font-weight: 600;
    }
    h3 {
        color: #34495e;
        font-weight: 600;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    /* Mejorar contraste en markdown dentro de columnas */
    .element-container {
        color: #95A6BF;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== FUNCIONES DE CARGA DE DATOS ====================

@st.cache_data
def load_database():
    """Carga la base de datos SQLite"""
    try:
        db_path = os.path.join(os.getcwd(), 'db_1.db')
        engine = create_engine(f'sqlite:///{db_path}')
        
        # Cargar todos los datos
        query = """
        SELECT 
            loc,
            sat_id,
            time,
            area_km2,
            ndwi_area_km2
        FROM water_surface_detection_v3
        WHERE (error = 0 OR error_vis = 0)
        ORDER BY time
        """
        df = pd.read_sql(query, engine)
        df['time'] = pd.to_datetime(df['time'])
        
        return df
    except Exception as e:
        st.error(f"Error al cargar la base de datos: {e}")
        return pd.DataFrame()

@st.cache_data
def load_geometries():
    """Carga todas las geometrías GeoJSON"""
    try:
        geometries_path = os.path.join(os.getcwd(), 'geometries')
        geojson_files = [f for f in os.listdir(geometries_path) if f.endswith('.geojson')]
        
        geometries = {}
        for file in geojson_files:
            loc_id = file.replace('.geojson', '')
            file_path = os.path.join(geometries_path, file)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
                geometries[loc_id] = geojson_data
        
        return geometries
    except Exception as e:
        st.error(f"Error al cargar geometrías: {e}")
        return {}

@st.cache_data
def create_locations_dataframe(geometries, data_df):
    """Crea un DataFrame con información de ubicaciones"""
    locations = []
    
    for loc_id, geojson in geometries.items():
        # Extraer coordenadas del centroide
        if geojson['type'] == 'FeatureCollection':
            features = geojson['features']
        else:
            features = [geojson]
        
        if features:
            # Extraer el nombre RAM_NAME de las propiedades
            ram_name = features[0].get('properties', {}).get('RAM_NAME', 'N/A')
            
            # Calcular centroide aproximado
            coords = features[0]['geometry']['coordinates']
            
            if features[0]['geometry']['type'] == 'Polygon':
                coords_array = np.array(coords[0])
            elif features[0]['geometry']['type'] == 'MultiPolygon':
                coords_array = np.array(coords[0][0])
            else:
                coords_array = np.array(coords)
            
            centroid_lon = np.mean(coords_array[:, 0])
            centroid_lat = np.mean(coords_array[:, 1])
            
            # Obtener estadísticas de la base de datos
            loc_data = data_df[data_df['loc'] == loc_id]
            
            if not loc_data.empty:
                locations.append({
                    'loc': loc_id,
                    'ram_name': ram_name,
                    'lat': centroid_lat,
                    'lon': centroid_lon,
                    'total_observations': len(loc_data),
                    'sentinel1_obs': len(loc_data[loc_data['sat_id'] == 'S1_GRD']),
                    'landsat_obs': len(loc_data[loc_data['sat_id'] != 'S1_GRD']),
                    'avg_area': loc_data['area_km2'].mean(),
                    'max_area': loc_data['area_km2'].max(),
                    'min_area': loc_data['area_km2'].min()
                })
    
    return pd.DataFrame(locations)

# ==================== FUNCIONES DE VISUALIZACIÓN ====================

def create_world_map(locations_df, selected_loc=None):
    """Crea mapa mundial interactivo con Plotly"""
    
    fig = go.Figure()
    
    # Añadir marcadores para todas las ubicaciones
    fig.add_trace(go.Scattergeo(
        lon=locations_df['lon'],
        lat=locations_df['lat'],
        text=locations_df['ram_name'],
        mode='markers',
        marker=dict(
            size=10,
            color='blue',
            line=dict(width=1, color='white'),
            opacity=0.7
        ),
        customdata=locations_df[['loc', 'ram_name', 'total_observations', 'avg_area']],
        hovertemplate='<b>%{customdata[1]}</b><br>' +
                      'ID: %{customdata[0]}<br>' +
                      'Observaciones: %{customdata[2]}<br>' +
                      'Área promedio: %{customdata[3]:.2f} km²<br>' +
                      '<extra></extra>',
        name='Ubicaciones'
    ))
    
    # Resaltar ubicación seleccionada
    if selected_loc is not None:
        selected_data = locations_df[locations_df['loc'] == selected_loc]
        if not selected_data.empty:
            fig.add_trace(go.Scattergeo(
                lon=selected_data['lon'],
                lat=selected_data['lat'],
                mode='markers',
                marker=dict(
                    size=20,
                    color='red',
                    symbol='star',
                    line=dict(width=2, color='white')
                ),
                name='Ubicación Seleccionada',
                showlegend=True
            ))
    
    # Configurar el layout del mapa
    fig.update_layout(
        title={
            'text': '🌍 Mapa de Ubicaciones Ramsar',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#1f77b4', 'family': 'Arial Black'}
        },
        geo=dict(
            projection_type='natural earth',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            coastlinecolor='rgb(204, 204, 204)',
            showocean=True,
            oceancolor='rgb(230, 245, 255)',
            showcountries=True,
            countrycolor='rgb(204, 204, 204)',
            showlakes=True,
            lakecolor='rgb(200, 230, 255)',
        ),
        height=600,
        margin=dict(l=0, r=0, t=80, b=0)
    )
    
    return fig

def create_time_series_chart(data_df, loc_id):
    """Crea gráfico de series temporales con tres líneas"""
    
    loc_data = data_df[data_df['loc'] == loc_id].copy()
    
    if loc_data.empty:
        return None
    
    # Preparar datos para las tres líneas
    sentinel1_data = loc_data[loc_data['sat_id'] == 'S1_GRD'].sort_values('time')
    landsat_data = loc_data[loc_data['sat_id'] != 'S1_GRD'].sort_values('time')
    
    # Crear figura
    fig = go.Figure()
    
    # Línea 1: Sentinel-1 área
    if not sentinel1_data.empty:
        fig.add_trace(go.Scatter(
            x=sentinel1_data['time'],
            y=sentinel1_data['area_km2'],
            mode='lines+markers',
            name='Sentinel-1 (Área SAR)',
            line=dict(color='#3498db', width=2),
            marker=dict(size=6),
            hovertemplate='<b>Sentinel-1</b><br>' +
                          'Fecha: %{x|%Y-%m-%d}<br>' +
                          'Área: %{y:.2f} km²<br>' +
                          '<extra></extra>'
        ))
    
    # Línea 2: Landsat área
    if not landsat_data.empty:
        fig.add_trace(go.Scatter(
            x=landsat_data['time'],
            y=landsat_data['area_km2'],
            mode='lines+markers',
            name='Landsat (Área NIR)',
            line=dict(color='#e74c3c', width=2),
            marker=dict(size=6),
            hovertemplate='<b>Landsat - NIR</b><br>' +
                          'Fecha: %{x|%Y-%m-%d}<br>' +
                          'Área: %{y:.2f} km²<br>' +
                          '<extra></extra>'
        ))
    
    # Línea 3: Landsat NDWI área
    if not landsat_data.empty:
        fig.add_trace(go.Scatter(
            x=landsat_data['time'],
            y=landsat_data['ndwi_area_km2'],
            mode='lines+markers',
            name='Landsat (Área NDWI)',
            line=dict(color='#2ecc71', width=2),
            marker=dict(size=6),
            hovertemplate='<b>Landsat - NDWI</b><br>' +
                          'Fecha: %{x|%Y-%m-%d}<br>' +
                          'Área: %{y:.2f} km²<br>' +
                          '<extra></extra>'
        ))
    
    # Layout
    fig.update_layout(
        title={
            'text': f'📊 Series Temporales de Área de Agua - Ubicación {loc_id}',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#95A6BF'}
        },
        xaxis_title='Fecha',
        yaxis_title='Área (km²)',
        hovermode='x unified',
        template='plotly_white',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='lightgray',
            rangeslider=dict(visible=True)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray'
        )
    )
    
    return fig

def create_statistics_cards(data_df, loc_id):
    """Crea tarjetas de estadísticas para una ubicación"""
    
    loc_data = data_df[data_df['loc'] == loc_id]
    
    if loc_data.empty:
        return None, None, None, None
    
    sentinel1_data = loc_data[loc_data['sat_id'] == 'S1_GRD']
    landsat_data = loc_data[loc_data['sat_id'] != 'S1_GRD']
    
    # Estadísticas generales
    total_obs = len(loc_data)
    date_range = f"{loc_data['time'].min().strftime('%Y-%m-%d')} - {loc_data['time'].max().strftime('%Y-%m-%d')}"
    
    # Estadísticas Sentinel-1
    if not sentinel1_data.empty:
        s1_avg = sentinel1_data['area_km2'].mean()
        s1_max = sentinel1_data['area_km2'].max()
        s1_min = sentinel1_data['area_km2'].min()
        s1_obs = len(sentinel1_data)
    else:
        s1_avg = s1_max = s1_min = s1_obs = 0
    
    # Estadísticas Landsat
    if not landsat_data.empty:
        ls_avg = landsat_data['area_km2'].mean()
        ls_max = landsat_data['area_km2'].max()
        ls_min = landsat_data['area_km2'].min()
        ls_obs = len(landsat_data)
        
        ndwi_avg = landsat_data['ndwi_area_km2'].mean()
        ndwi_max = landsat_data['ndwi_area_km2'].max()
        ndwi_min = landsat_data['ndwi_area_km2'].min()
    else:
        ls_avg = ls_max = ls_min = ls_obs = 0
        ndwi_avg = ndwi_max = ndwi_min = 0
    
    return {
        'general': {
            'total_obs': total_obs,
            'date_range': date_range,
            's1_obs': s1_obs,
            'ls_obs': ls_obs
        },
        'sentinel1': {
            'avg': s1_avg,
            'max': s1_max,
            'min': s1_min,
            'obs': s1_obs
        },
        'landsat': {
            'avg': ls_avg,
            'max': ls_max,
            'min': ls_min,
            'obs': ls_obs
        },
        'ndwi': {
            'avg': ndwi_avg,
            'max': ndwi_max,
            'min': ndwi_min
        }
    }

def create_comparison_chart(data_df, loc_id):
    """Crea gráfico de comparación entre métodos"""
    
    loc_data = data_df[data_df['loc'] == loc_id]
    landsat_data = loc_data[loc_data['sat_id'] != 'S1_GRD']
    
    if landsat_data.empty:
        return None
    
    # Crear subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Distribución de Áreas', 'Correlación NDWI vs NIR'),
        specs=[[{'type': 'box'}, {'type': 'scatter'}]]
    )
    
    # Box plot
    fig.add_trace(
        go.Box(y=landsat_data['area_km2'], name='NIR', marker_color='#e74c3c'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Box(y=landsat_data['ndwi_area_km2'], name='NDWI', marker_color='#2ecc71'),
        row=1, col=1
    )
    
    # Scatter plot
    fig.add_trace(
        go.Scatter(
            x=landsat_data['ndwi_area_km2'],
            y=landsat_data['area_km2'],
            mode='markers',
            marker=dict(
                size=8,
                color=landsat_data['time'].astype(np.int64),
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Tiempo")
            ),
            text=landsat_data['time'].dt.strftime('%Y-%m-%d'),
            hovertemplate='<b>Fecha: %{text}</b><br>' +
                          'NDWI: %{x:.2f} km²<br>' +
                          'Clasificación: %{y:.2f} km²<br>' +
                          '<extra></extra>',
            showlegend=False
        ),
        row=1, col=2
    )
    
    # Línea de referencia 1:1
    max_val = max(landsat_data['area_km2'].max(), landsat_data['ndwi_area_km2'].max())
    fig.add_trace(
        go.Scatter(
            x=[0, max_val],
            y=[0, max_val],
            mode='lines',
            line=dict(color='gray', dash='dash'),
            name='Línea 1:1',
            showlegend=True
        ),
        row=1, col=2
    )
    
    # fig.update_xaxes(title_text="Área (km²)", row=1, col=1)
    fig.update_yaxes(title_text="Área (km²)", row=1, col=1)
    fig.update_xaxes(title_text="NDWI Área (km²)", row=1, col=2)
    fig.update_yaxes(title_text="Clasificación Área (km²)", row=1, col=2)
    
    fig.update_layout(
        title_text=f"📈 Análisis Comparativo de Métodos - Ubicación {loc_id}",
        height=500,
        showlegend=True,
        template='plotly_white'
    )
    
    return fig

def create_monthly_analysis(data_df, loc_id):
    """Crea análisis por mes"""
    
    loc_data = data_df[data_df['loc'] == loc_id].copy()
    
    if loc_data.empty:
        return None
    
    loc_data['month'] = loc_data['time'].dt.month
    loc_data['month_name'] = loc_data['time'].dt.strftime('%B')
    
    # Agrupar por mes
    sentinel1_monthly = loc_data[loc_data['sat_id'] == 'S1_GRD'].groupby('month')['area_km2'].mean()
    landsat_monthly = loc_data[loc_data['sat_id'] != 'S1_GRD'].groupby('month')['area_km2'].mean()
    ndwi_monthly = loc_data[loc_data['sat_id'] != 'S1_GRD'].groupby('month')['ndwi_area_km2'].mean()
    
    months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
              'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    fig = go.Figure()
    
    if not sentinel1_monthly.empty:
        fig.add_trace(go.Bar(
            x=[months[i-1] for i in sentinel1_monthly.index],
            y=sentinel1_monthly.values,
            name='Sentinel-1 (VV, VH)',
            marker_color='#3498db'
        ))
    
    if not landsat_monthly.empty:
        fig.add_trace(go.Bar(
            x=[months[i-1] for i in landsat_monthly.index],
            y=landsat_monthly.values,
            name='Landsat (NIR)',
            marker_color='#e74c3c'
        ))
    
    if not ndwi_monthly.empty:
        fig.add_trace(go.Bar(
            x=[months[i-1] for i in ndwi_monthly.index],
            y=ndwi_monthly.values,
            name='Landsat (NDWI)',
            marker_color='#2ecc71'
        ))
    
    fig.update_layout(
        title=f'📅 Análisis Mensual Promedio - Ubicación {loc_id}',
        xaxis_title='Mes',
        yaxis_title='Área Promedio (km²)',
        barmode='group',
        template='plotly_white',
        height=400
    )
    
    return fig

# ==================== APLICACIÓN PRINCIPAL ====================

def main():
    # Header
    st.title("Water Surface Detection Dashboard")
    st.markdown("### Sistema de Monitoreo Nacional de Superficies de Agua en Humedales Ramsar")
    st.markdown("---")
    
    # Cargar datos
    with st.spinner('🔄 Cargando datos...'):
        data_df = load_database()
        geometries = load_geometries()
        
        if data_df.empty or not geometries:
            st.error("❌ No se pudieron cargar los datos. Verifica las rutas de los archivos.")
            return
        
        locations_df = create_locations_dataframe(geometries, data_df)
    
    st.success(f'✅ Datos cargados: {len(locations_df)} ubicaciones, {len(data_df)} observaciones')
    
    # Sidebar
    with st.sidebar:
        #st.image("https://img.icons8.com/fluency/96/000000/water.png", width=80)
        st.title("🎛️ Panel de Control")
        st.markdown("---")
        
        # Selección de ubicación
        st.subheader("📍 Seleccionar Ubicación")
        
        # Crear diccionario de ID -> Nombre completo para el selector
        location_options = ['Todas'] + [
            f"{row['loc']} - {row['ram_name']}" 
            for _, row in locations_df.sort_values('loc').iterrows()
        ]
        
        # Opción de búsqueda
        search_option = st.radio(
            "Método de selección:",
            ["Lista desplegable", "Búsqueda por ID", "Búsqueda por nombre"]
        )
        
        if search_option == "Lista desplegable":
            selected_option = st.selectbox(
                "Ubicación:",
                options=location_options,
                index=0
            )
            # Extraer solo el ID de la opción seleccionada
            if selected_option == 'Todas':
                selected_loc = 'Todas'
            else:
                selected_loc = selected_option.split(' - ')[0]
        elif search_option == "Búsqueda por ID":
            search_id = st.text_input("Ingresa el ID de la ubicación:")
            if search_id and search_id in locations_df['loc'].values:
                selected_loc = search_id
                loc_name = locations_df[locations_df['loc'] == search_id].iloc[0]['ram_name']
                st.success(f"✅ {loc_name}")
            elif search_id:
                st.warning("ID no encontrado")
                selected_loc = 'Todas'
            else:
                selected_loc = 'Todas'
        else:  # Búsqueda por nombre
            search_name = st.text_input("Ingresa el nombre (búsqueda parcial):")
            if search_name:
                # Búsqueda case-insensitive
                matches = locations_df[
                    locations_df['ram_name'].str.contains(search_name, case=False, na=False)
                ]
                if not matches.empty:
                    if len(matches) == 1:
                        selected_loc = matches.iloc[0]['loc']
                        st.success(f"✅ {matches.iloc[0]['ram_name']} (ID: {selected_loc})")
                    else:
                        st.info(f"Se encontraron {len(matches)} coincidencias:")
                        selected_match = st.selectbox(
                            "Selecciona una ubicación:",
                            options=matches['loc'].tolist(),
                            format_func=lambda x: f"{x} - {matches[matches['loc']==x].iloc[0]['ram_name']}"
                        )
                        selected_loc = selected_match
                else:
                    st.warning("No se encontraron coincidencias")
                    selected_loc = 'Todas'
            else:
                selected_loc = 'Todas'
        
        st.markdown("---")
        
        # Filtros adicionales
        st.subheader("🔍 Filtros")
        
        # Filtro de fecha
        if not data_df.empty:
            min_date = data_df['time'].min().date()
            max_date = data_df['time'].max().date()
            
            date_range = st.date_input(
                "Rango de fechas:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
        
        # Filtro de satélite
        sat_filter = st.multiselect(
            "Satélites:",
            options=['Sentinel-1', 'Landsat'],
            default=['Sentinel-1', 'Landsat']
        )
        
        st.markdown("---")
        
        # Información del sistema
        st.subheader("ℹ️ Información")
        st.info(
            f"""
            **Total de ubicaciones:** {len(locations_df)}  
            **Total de observaciones:** {len(data_df)}  
            **Rango temporal:** {data_df['time'].min().strftime('%Y-%m-%d')} a {data_df['time'].max().strftime('%Y-%m-%d')}
            """
        )
    
    # Aplicar filtros
    filtered_df = data_df.copy()
    
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['time'].dt.date >= date_range[0]) &
            (filtered_df['time'].dt.date <= date_range[1])
        ]
    
    if 'Sentinel-1' not in sat_filter:
        filtered_df = filtered_df[filtered_df['sat_id'] != 'S1_GRD']
    if 'Landsat' not in sat_filter:
        filtered_df = filtered_df[filtered_df['sat_id'] == 'S1_GRD']
    
    # Contenido principal
    if selected_loc == 'Todas':
        # Vista general
        st.header("🗺️ Vista General Localizaciones Ramsar")
        
        # Mapa mundial
        world_map = create_world_map(locations_df)
        st.plotly_chart(world_map, use_container_width=True)
        
        # Estadísticas globales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🌍 Ubicaciones Totales",
                len(locations_df),
                delta=None
            )
        
        with col2:
            st.metric(
                "📊 Observaciones Totales",
                f"{len(filtered_df):,}",
                delta=None
            )
        
        with col3:
            sentinel1_count = len(filtered_df[filtered_df['sat_id'] == 'S1_GRD'])
            st.metric(
                "🛰️ Observaciones Sentinel-1",
                f"{sentinel1_count:,}",
                delta=None
            )
        
        with col4:
            landsat_count = len(filtered_df[filtered_df['sat_id'] != 'S1_GRD'])
            st.metric(
                "🛰️ Observaciones Landsat",
                f"{landsat_count:,}",
                delta=None
            )
        
        st.markdown("---")
        
        # Tabla de ubicaciones
        st.subheader("📋 Tabla de Ubicaciones")
        
        # Reorganizar columnas para mejor legibilidad
        display_columns = ['loc', 'ram_name', 'total_observations', 'sentinel1_obs', 
                          'landsat_obs', 'avg_area', 'max_area', 'min_area']
        
        # Renombrar columnas para mejor presentación
        column_names = {
            'loc': 'ID',
            'ram_name': 'Nombre Ramsar',
            'total_observations': 'Total Obs.',
            'sentinel1_obs': 'Sentinel-1',
            'landsat_obs': 'Landsat',
            'avg_area': 'Área Prom. (km²)',
            'max_area': 'Área Máx. (km²)',
            'min_area': 'Área Mín. (km²)'
        }
        
        st.dataframe(
            locations_df[display_columns].sort_values('total_observations', ascending=False).rename(columns=column_names),
            use_container_width=True,
            hide_index=True
        )
        
    else:
        # Vista detallada de ubicación
        selected_loc_data = locations_df[locations_df['loc'] == selected_loc]
        if not selected_loc_data.empty:
            ram_name = selected_loc_data.iloc[0]['ram_name']
            st.header(f"📍 {ram_name}")
            st.subheader(f"ID: {selected_loc}")
        else:
            st.header(f"📍 Análisis Detallado - Ubicación {selected_loc}")
        
        # Mapa con ubicación seleccionada
        world_map = create_world_map(locations_df, selected_loc)
        st.plotly_chart(world_map, use_container_width=True)
        
        # Obtener estadísticas
        stats = create_statistics_cards(filtered_df, selected_loc)
        
        if stats:
            # Métricas principales
            st.subheader("📊 Estadísticas Generales")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "📅 Total Observaciones",
                    stats['general']['total_obs']
                )
            
            with col2:
                st.metric(
                    "🛰️ Sentinel-1",
                    stats['general']['s1_obs']
                )
            
            with col3:
                st.metric(
                    "🛰️ Landsat",
                    stats['general']['ls_obs']
                )
            
            with col4:
                st.metric(
                    "📆 Rango Temporal",
                    f"{stats['general']['total_obs']} días"
                )
            
            st.markdown("---")
            
            # Estadísticas detalladas por sensor
            st.subheader("📈 Estadísticas por Sensor")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 🔵 Sentinel-1 (SAR)")
                if stats['sentinel1']['obs'] > 0:
                    st.metric("Área Promedio", f"{stats['sentinel1']['avg']:.2f} km²")
                    st.metric("Área Máxima", f"{stats['sentinel1']['max']:.2f} km²")
                    st.metric("Área Mínima", f"{stats['sentinel1']['min']:.2f} km²")
                else:
                    st.info("Sin datos disponibles")
            
            with col2:
                st.markdown("### 🔴 Landsat (NIR)")
                if stats['landsat']['obs'] > 0:
                    st.metric("Área Promedio", f"{stats['landsat']['avg']:.2f} km²")
                    st.metric("Área Máxima", f"{stats['landsat']['max']:.2f} km²")
                    st.metric("Área Mínima", f"{stats['landsat']['min']:.2f} km²")
                else:
                    st.info("Sin datos disponibles")
            
            with col3:
                st.markdown("### 🟢 Landsat (NDWI)")
                if stats['landsat']['obs'] > 0:
                    st.metric("Área Promedio", f"{stats['ndwi']['avg']:.2f} km²")
                    st.metric("Área Máxima", f"{stats['ndwi']['max']:.2f} km²")
                    st.metric("Área Mínima", f"{stats['ndwi']['min']:.2f} km²")
                else:
                    st.info("Sin datos disponibles")
            
            st.markdown("---")
            
            # Gráfico de series temporales
            st.subheader("📈 Series Temporales")
            time_series_fig = create_time_series_chart(filtered_df, selected_loc)
            if time_series_fig:
                st.plotly_chart(time_series_fig, use_container_width=True)
            else:
                st.warning("No hay datos suficientes para generar el gráfico de series temporales")
            
            st.markdown("---")
            
            # Análisis comparativo
            st.subheader("🔬 Análisis Comparativo")
            comparison_fig = create_comparison_chart(filtered_df, selected_loc)
            if comparison_fig:
                st.plotly_chart(comparison_fig, use_container_width=True)
            else:
                st.warning("No hay datos Landsat suficientes para el análisis comparativo")
            
            st.markdown("---")
            
            # Análisis mensual
            st.subheader("📅 Análisis Estacional")
            monthly_fig = create_monthly_analysis(filtered_df, selected_loc)
            if monthly_fig:
                st.plotly_chart(monthly_fig, use_container_width=True)
            else:
                st.warning("No hay datos suficientes para el análisis mensual")
            
        else:
            st.warning(f"No hay datos disponibles para la ubicación {selected_loc}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            <p>Water Surface Detection Dashboard v1.0 | Desarrollado con Streamlit y Plotly</p>
            <p>© 2025 - Sistema de Monitoreo Global de Agua</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
