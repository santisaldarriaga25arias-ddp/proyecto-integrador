
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="OILRED | Dashboard Industrial",
    page_icon="🏭",
    layout="wide"
)

# Configuración visual
st.markdown("""
<style>
.stApp {
    background-color: #F4F7FB;
}
h1, h2, h3 {
    color: #142B4A;
}
div[data-testid="stMetric"] {
    background-color: white;
    border: 1px solid #E3EAF2;
    padding: 15px;
    border-radius: 12px;
}
.hero {
    background: linear-gradient(110deg, #142B4A, #2878B5);
    padding: 25px;
    border-radius: 15px;
    color: white;
}
.hero h1 {
    color: white;
}
.hero p {
    color: #E8F2FA;
}
</style>
""", unsafe_allow_html=True)


# Cargar datos
@st.cache_data
def cargar_datos():
    ruta = Path(__file__).parent / "data" / "dataset_planta_bigdata.csv"
    df = pd.read_csv(ruta)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"], errors="coerce"
    )

    columnas = [
        "temperatura", "vibracion", "presion",
        "produccion", "defectos", "falla"
    ]

    for columna in columnas:
        df[columna] = pd.to_numeric(
            df[columna], errors="coerce"
        )

    df = df.dropna(
        subset=["timestamp", "linea", "turno"]
    )

    return df


df = cargar_datos()


# Encabezado
st.markdown("""
<div class="hero">
    <h1>🏭 OILRED | Monitoreo Industrial</h1>
    <p>
    Dashboard de supervisión y análisis de producción,
    calidad, variables operativas y fallas.
    </p>
</div>
""", unsafe_allow_html=True)


# FILTROS
st.sidebar.title("⚙️ Panel de filtros")

lineas = sorted(df["linea"].unique().tolist())
turnos = sorted(df["turno"].unique().tolist())

seleccion_lineas = st.sidebar.multiselect(
    "Líneas de producción",
    lineas,
    default=lineas
)

seleccion_turnos = st.sidebar.multiselect(
    "Turnos",
    turnos,
    default=turnos
)

fecha_min = df["timestamp"].min().date()
fecha_max = df["timestamp"].max().date()

fechas = st.sidebar.date_input(
    "Rango de fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)

if isinstance(fechas, (tuple, list)):
    if len(fechas) == 2:
        inicio, fin = fechas
    elif len(fechas) == 1:
        inicio = fin = fechas[0]
    else:
        inicio, fin = fecha_min, fecha_max
else:
    inicio = fin = fechas

datos = df[
    (df["linea"].isin(seleccion_lineas)) &
    (df["turno"].isin(seleccion_turnos)) &
    (df["timestamp"].dt.date >= inicio) &
    (df["timestamp"].dt.date <= fin)
].copy()

if datos.empty:
    st.warning("No existen registros para los filtros seleccionados.")
    st.stop()


# CÁLCULO DE KPI
produccion_total = datos["produccion"].sum()
produccion_promedio = datos["produccion"].mean()
defectos_total = datos["defectos"].sum()

porcentaje_defectos = (
    defectos_total / produccion_total * 100
    if produccion_total > 0 else 0
)

registros_falla = int((datos["falla"] == 1).sum())

porcentaje_falla = (
    registros_falla / len(datos) * 100
)


# NAVEGACIÓN
resumen, produccion, variables, fallas = st.tabs([
    "📊 Resumen general",
    "📦 Producción y calidad",
    "🌡️ Variables operativas",
    "🚨 Análisis de fallas"
])


# ==================================================
# 1. RESUMEN GENERAL
# ==================================================

with resumen:

    st.header("Resumen general de la planta")

    st.caption(
        f"Periodo analizado: {inicio} hasta {fin} | "
        f"{len(datos):,} registros"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Producción total",
        f"{produccion_total:,.0f}"
    )

    col2.metric(
        "Producción promedio",
        f"{produccion_promedio:.2f}"
    )

    col3.metric(
        "Defectos totales",
        f"{defectos_total:,.0f}"
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Porcentaje de defectos",
        f"{porcentaje_defectos:.2f}%"
    )

    col5.metric(
        "Registros con falla",
        f"{registros_falla:,}"
    )

    col6.metric(
        "Porcentaje de fallas",
        f"{porcentaje_falla:.2f}%"
    )

    st.divider()

    izquierda, derecha = st.columns(2)

    with izquierda:

        produccion_linea = datos.groupby(
            "linea", as_index=False
        )["produccion"].sum()

        fig = px.bar(
            produccion_linea,
            x="linea",
            y="produccion",
            color="linea",
            title="Producción acumulada por línea",
            text_auto=","
        )

        fig.update_layout(showlegend=False)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with derecha:

        produccion_dia = datos.groupby(
            datos["timestamp"].dt.date
        )["produccion"].sum().reset_index()

        produccion_dia.columns = [
            "fecha", "produccion"
        ]

        fig = px.line(
            produccion_dia,
            x="fecha",
            y="produccion",
            markers=True,
            title="Evolución diaria de producción"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # Hallazgos dinámicos
    st.subheader("Hallazgos y recomendaciones")

    estadisticas = datos.groupby("linea").agg(
        produccion=("produccion", "sum"),
        fallas=("falla", "sum")
    )

    tasa_fallas = datos.groupby("linea")[
        "falla"
    ].mean() * 100

    linea_productiva = estadisticas["produccion"].idxmax()
    linea_fallas = estadisticas["fallas"].idxmax()
    linea_tasa = tasa_fallas.idxmax()

    st.markdown(
        f"- La línea con mayor producción es **{linea_productiva}**, "
        f"con {estadisticas.loc[linea_productiva, 'produccion']:,.0f} unidades."
    )

    st.markdown(
        f"- La línea con más registros de falla es **{linea_fallas}**, "
        f"con {estadisticas.loc[linea_fallas, 'fallas']:,.0f} eventos."
    )

    st.markdown(
        f"- La mayor tasa de fallas corresponde a **{linea_tasa}**, "
        f"con {tasa_fallas.loc[linea_tasa]:.2f}%."
    )

    st.markdown("**Recomendaciones:**")

    st.write(
        "1. Priorizar la inspección de la línea con mayor tasa de fallas."
    )

    st.write(
        "2. Monitorear la producción y los defectos por turno."
    )

    st.write(
        "3. Establecer límites de alerta para las variables operativas "
        "después de validar sus unidades físicas."
    )


# ==================================================
# 2. PRODUCCIÓN Y CALIDAD
# ==================================================

with produccion:

    st.header("Análisis de producción y calidad")

    col1, col2 = st.columns(2)

    with col1:

        por_linea = datos.groupby(
            "linea", as_index=False
        )["produccion"].sum()

        fig = px.bar(
            por_linea,
            x="linea",
            y="produccion",
            color="linea",
            title="Producción por línea",
            text_auto=","
        )

        fig.update_layout(showlegend=False)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        por_turno = datos.groupby(
            "turno", as_index=False
        )["produccion"].sum()

        fig = px.bar(
            por_turno,
            x="turno",
            y="produccion",
            color="turno",
            title="Producción por turno",
            text_auto=","
        )

        fig.update_layout(showlegend=False)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    evolucion = datos.groupby([
        pd.Grouper(key="timestamp", freq="D"),
        "linea"
    ], as_index=False)["produccion"].sum()

    fig = px.line(
        evolucion,
        x="timestamp",
        y="produccion",
        color="linea",
        markers=True,
        title="Evolución de producción por línea"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    st.subheader("Análisis de calidad")

    col1, col2 = st.columns(2)

    with col1:

        defectos_linea = datos.groupby(
            "linea", as_index=False
        )["defectos"].sum()

        fig = px.bar(
            defectos_linea,
            x="linea",
            y="defectos",
            color="linea",
            title="Defectos por línea",
            text_auto=","
        )

        fig.update_layout(showlegend=False)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        defectos_turno = datos.groupby(
            "turno", as_index=False
        )["defectos"].sum()

        fig = px.bar(
            defectos_turno,
            x="turno",
            y="defectos",
            color="turno",
            title="Defectos por turno",
            text_auto=","
        )

        fig.update_layout(showlegend=False)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.metric(
        "Porcentaje de defectos",
        f"{porcentaje_defectos:.2f}%"
    )


# ==================================================
# 3. VARIABLES OPERATIVAS
# ==================================================

with variables:

    st.header("Monitoreo de variables operativas")

    st.info(
        "Las unidades físicas de las variables no están "
        "documentadas en el archivo original."
    )

    datos_hora = datos.set_index(
        "timestamp"
    ).groupby("linea")[
        ["temperatura", "vibracion", "presion"]
    ].resample("h").mean().reset_index()

    variables_operativas = [
        ("temperatura", "Temperatura"),
        ("vibracion", "Vibración"),
        ("presion", "Presión")
    ]

    for variable, nombre in variables_operativas:

        fig = px.line(
            datos_hora,
            x="timestamp",
            y=variable,
            color="linea",
            title=f"{nombre} promedio por hora",
            labels={
                "timestamp": "Fecha y hora",
                variable: nombre,
                "linea": "Línea"
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ==================================================
# 4. ANÁLISIS DE FALLAS
# ==================================================

with fallas:

    st.header("Análisis de fallas")

    col1, col2 = st.columns(2)

    fallas_linea = datos.groupby(
        "linea"
    ).agg(
        fallas=("falla", "sum"),
        registros=("falla", "size")
    ).reset_index()

    fallas_linea["porcentaje"] = (
        fallas_linea["fallas"] /
        fallas_linea["registros"] * 100
    )

    with col1:

        fig = px.bar(
            fallas_linea,
            x="linea",
            y="fallas",
            color="linea",
            title="Registros con falla por línea",
            text_auto=","
        )

        fig.update_layout(showlegend=False)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with col2:

        fig = px.bar(
            fallas_linea,
            x="linea",
            y="porcentaje",
            color="linea",
            title="Porcentaje de fallas por línea",
            text_auto=".2f"
        )

        fig.update_layout(showlegend=False)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    fallas_dia = datos.groupby(
        pd.Grouper(key="timestamp", freq="D")
    )["falla"].sum().reset_index()

    fig = px.line(
        fallas_dia,
        x="timestamp",
        y="falla",
        markers=True,
        title="Evolución diaria de fallas"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.subheader(
        "Relación entre variables operativas y fallas"
    )

    variable = st.selectbox(
        "Selecciona una variable",
        ["temperatura", "vibracion", "presion"]
    )

    fig = px.box(
        datos,
        x="falla",
        y=variable,
        color="falla",
        points="outliers",
        title=f"{variable.capitalize()} según registro de falla"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    correlacion = datos[
        [variable, "falla"]
    ].corr().iloc[0, 1]

    st.write(
        f"Correlación de Pearson: {correlacion:.3f}"
    )

    st.caption(
        "La correlación es descriptiva y no demuestra causalidad."
    )


# ==================================================
# TABLA DE DATOS Y DESCARGA
# ==================================================

st.divider()

st.header("Consulta de registros")

st.dataframe(
    datos,
    use_container_width=True,
    hide_index=True
)

csv = datos.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label="⬇️ Descargar datos filtrados (CSV)",
    data=csv,
    file_name="datos_industriales_filtrados.csv",
    mime="text/csv"
)


# ==================================================
# INFORMACIÓN DE CALIDAD DE DATOS
# ==================================================

with st.expander("Información y calidad de los datos"):

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Registros",
        f"{len(df):,}"
    )

    col2.metric(
        "Valores faltantes",
        f"{df.isna().sum().sum():,}"
    )

    col3.metric(
        "Filas duplicadas",
        f"{df.duplicated().sum():,}"
    )

    st.write("Tipos de datos:")

    st.dataframe(
        df.dtypes.astype(str).to_frame("Tipo"),
        use_container_width=True
    )

    st.write("Estadísticas descriptivas:")

    st.dataframe(
        df.describe().T,
        use_container_width=True
    )


st.caption(
    "OILRED | Proyecto Integrador – Digitalización de Plantas Productivas"
)

