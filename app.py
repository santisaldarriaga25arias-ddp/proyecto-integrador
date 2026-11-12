
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# --------------------------------------------------
# CONFIGURACIÓN GENERAL
# --------------------------------------------------

st.set_page_config(
    page_title="OILRED | Dashboard industrial",
    page_icon="🏭",
    layout="wide"
)

NAVY = "#142B4A"
BLUE = "#2878B5"
TEAL = "#16A6A1"
ORANGE = "#F39C45"
RED = "#D9534F"

# --------------------------------------------------
# CARGA DE DATOS
# --------------------------------------------------

@st.cache_data
def load_data():

    path = Path(__file__).parent / "data" / "dataset_planta_bigdata.csv"

    data = pd.read_csv(path)

    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        errors="coerce"
    )

    columnas_numericas = [
        "temperatura",
        "vibracion",
        "presion",
        "produccion",
        "defectos",
        "falla"
    ]

    for col in columnas_numericas:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(
        subset=["timestamp", "linea", "turno"]
    )

    return data


df = load_data()

# --------------------------------------------------
# DISEÑO VISUAL
# --------------------------------------------------

st.markdown("""
<style>

.stApp {
    background-color: #F4F7FB;
}

h1, h2, h3 {
    color: #142B4A;
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #E3EAF2;
    padding: 14px 16px;
    border-radius: 12px;
    box-shadow: 0 2px 8px #142b4a0c;
}

div[data-testid="stMetricLabel"] {
    color: #52657A;
}

.hero {
    background: linear-gradient(110deg,#142B4A,#2878B5);
    padding: 24px 28px;
    border-radius: 16px;
    color: white;
    margin-bottom: 18px;
}

.hero h1 {
    color: white;
    margin: 0;
    font-size: 30px;
}

.hero p {
    color: #E8F2FA;
    margin: 6px 0 0 0;
}

.note {
    color: #63758A;
    font-size: 0.86rem;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>🏭 OILRED | Monitoreo industrial</h1>
    <p>
    Centro de análisis de producción, calidad,
    variables operativas y eventos de falla
    </p>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# FILTROS
# --------------------------------------------------

st.sidebar.title("⚙️ Panel de filtros")

st.sidebar.caption(
    "Los filtros se aplican a todas las secciones."
)

lineas = sorted(
    df["linea"].dropna().unique().tolist()
)

turnos = [
    x for x in ["Mañana", "Tarde", "Noche"]
    if x in df["turno"].unique()
]

sel_lineas = st.sidebar.multiselect(
    "Líneas de producción",
    lineas,
    default=lineas
)

sel_turnos = st.sidebar.multiselect(
    "Turnos",
    turnos,
    default=turnos
)

min_date = df["timestamp"].min().date()
max_date = df["timestamp"].max().date()

fechas = st.sidebar.date_input(
    "Rango de fechas",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(fechas, tuple) and len(fechas) == 2:
    fecha_ini, fecha_fin = fechas
elif isinstance(fechas, tuple) and len(fechas) == 1:
    fecha_ini = fecha_fin = fechas[0]
else:
    fecha_ini = fecha_fin = fechas

f = df[
    df["linea"].isin(sel_lineas)
    & df["turno"].isin(sel_turnos)
    & (df["timestamp"].dt.date >= fecha_ini)
    & (df["timestamp"].dt.date <= fecha_fin)
].copy()

if f.empty:
    st.warning(
        "No hay registros para los filtros seleccionados. "
        "Ajusta las líneas, turnos o fechas."
    )
    st.stop()

# --------------------------------------------------
# CÁLCULOS GENERALES
# --------------------------------------------------

f["fecha_hora"] = f["timestamp"].dt.floor("h")
f["fecha"] = f["timestamp"].dt.date

prod_total = f["produccion"].sum()
def_total = f["defectos"].sum()

fallas = int((f["falla"] == 1).sum())

pct_def = (
    def_total / prod_total * 100
    if prod_total else 0
)

pct_falla = (
    fallas / len(f) * 100
    if len(f) else 0
)

# --------------------------------------------------
# SECCIONES DEL DASHBOARD
# --------------------------------------------------

tabs = st.tabs([
    "📊 Resumen general",
    "📦 Producción y calidad",
    "🌡️ Variables operativas",
    "🚨 Análisis de fallas"
])

# ==================================================
# 1. RESUMEN GENERAL
# ==================================================

with tabs[0]:

    st.subheader("Resumen general de la planta")

    st.caption(
        f"Periodo: {fecha_ini:%d/%m/%Y} – "
        f"{fecha_fin:%d/%m/%Y} · "
        f"{len(f):,} registros seleccionados"
    )

    c = st.columns(3)

    c[0].metric(
        "Producción total",
        f"{prod_total:,.0f}"
    )

    c[1].metric(
        "Producción promedio / registro",
        f"{f['produccion'].mean():.2f}"
    )

    c[2].metric(
        "Defectos totales",
        f"{def_total:,.0f}"
    )

    c = st.columns(3)

    c[0].metric(
        "Porcentaje de defectos",
        f"{pct_def:.2f}%"
    )

    c[1].metric(
        "Registros con falla",
        f"{fallas:,}"
    )

    c[2].metric(
        "Registros con falla (%)",
        f"{pct_falla:.2f}%"
    )

    st.divider()

    left, right = st.columns(2)

    by_line = f.groupby(
        "linea",
        as_index=False
    ).agg(
        produccion=("produccion", "sum"),
        fallas=("falla", "sum")
    )

    with left:

        fig = px.bar(
            by_line,
            x="linea",
            y="produccion",
            color="linea",
            text_auto=",",
            title="Producción acumulada por línea",
            color_discrete_sequence=[
                BLUE, TEAL, ORANGE
            ]
        )

        fig.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="Unidades producidas"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:

        by_day = f.groupby(
            f["timestamp"].dt.date,
            as_index=False
        )["produccion"].sum()

        by_day.columns = [
            "fecha",
            "produccion"
        ]

        fig = px.line(
            by_day,
            x="fecha",
            y="produccion",
            markers=True,
            title="Evolución diaria de la producción"
        )

        fig.update_traces(
            line_color=BLUE
        )

        fig.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Unidades producidas"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # HALLAZGOS

    st.subheader("Hallazgos y recomendaciones")

    line_stats = f.groupby("linea").agg(
        produccion=("produccion", "sum"),
        fallas=("falla", "sum"),
        defectos=("defectos", "sum")
    ).copy()

    line_stats["tasa_falla"] = (
        f.groupby("linea")["falla"].mean() * 100
    )

    if not line_stats.empty:

        top_prod = line_stats["produccion"].idxmax()
        top_fail = line_stats["fallas"].idxmax()
        top_rate = line_stats["tasa_falla"].idxmax()

        st.markdown(
            f"- **Productividad:** {top_prod} presenta "
            f"la mayor producción acumulada "
            f"({line_stats.loc[top_prod, 'produccion']:,.0f} unidades) "
            "en el periodo filtrado."
        )

        st.markdown(
            f"- **Eventos de falla:** {top_fail} registra "
            f"la mayor cantidad de eventos "
            f"({line_stats.loc[top_fail, 'fallas']:,.0f}); "
            f"la mayor tasa de registros con falla corresponde "
            f"a {top_rate} "
            f"({line_stats.loc[top_rate, 'tasa_falla']:.2f}%)."
        )

    shift_prod = f.groupby("turno")["produccion"].sum()

    if len(shift_prod):

        st.markdown(
            f"- **Turnos:** el turno con mayor producción "
            f"acumulada es **{shift_prod.idxmax()}** "
            f"({shift_prod.max():,.0f} unidades)."
        )

    st.markdown("**Recomendaciones operativas**")

    st.markdown("""
    1. Priorizar la revisión de la línea con mayor tasa
       de fallas y contrastar sus registros con las
       condiciones operativas.

    2. Hacer seguimiento periódico a producción y
       defectos por turno para identificar cambios
       de desempeño.

    3. Definir límites de alerta con el equipo de
       proceso después de validar las unidades y
       rangos físicos de temperatura, vibración y presión.
    """)

    st.markdown("""
    <p class="note">
    Los hallazgos cambian con los filtros seleccionados.
    Las recomendaciones son acciones sugeridas para investigar;
    no constituyen causalidades demostradas.
    </p>
    """, unsafe_allow_html=True)


# ==================================================
# 2. PRODUCCIÓN Y CALIDAD
# ==================================================

with tabs[1]:

    st.subheader("Análisis de producción y calidad")

    left, right = st.columns(2)

    with left:

        p_line = f.groupby(
            "linea",
            as_index=False
        )["produccion"].sum()

        fig = px.bar(
            p_line,
            x="linea",
            y="produccion",
            color="linea",
            title="Producción acumulada por línea",
            color_discrete_sequence=[
                BLUE, TEAL, ORANGE
            ],
            text_auto=","
        )

        fig.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="Unidades"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:

        p_shift = f.groupby(
            "turno",
            as_index=False
        )["produccion"].sum()

        order = [
            "Mañana",
            "Tarde",
            "Noche"
        ]

        p_shift["turno"] = pd.Categorical(
            p_shift["turno"],
            categories=order,
            ordered=True
        )

        p_shift = p_shift.sort_values("turno")

        fig = px.bar(
            p_shift,
            x="turno",
            y="produccion",
            color="turno",
            title="Producción por turno",
            color_discrete_sequence=[
                BLUE, TEAL, ORANGE
            ],
            text_auto=","
        )

        fig.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="Unidades"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    daily_line = f.groupby(
        [
            pd.Grouper(
                key="timestamp",
                freq="D"
            ),
            "linea"
        ],
        as_index=False
    )["produccion"].sum()

    fig = px.line(
        daily_line,
        x="timestamp",
        y="produccion",
        color="linea",
        markers=True,
        title="Evolución diaria de producción por línea"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.divider()

    st.markdown("#### Calidad")

    c1, c2 = st.columns(2)

    defects_line = f.groupby(
        "linea",
        as_index=False
    )["defectos"].sum()

    with c1:

        fig = px.bar(
            defects_line,
            x="linea",
            y="defectos",
            color="linea",
            title="Defectos por línea",
            color_discrete_sequence=[
                BLUE, TEAL, ORANGE
            ],
            text_auto=","
        )

        fig.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="Unidades defectuosas"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with c2:

        defects_shift = f.groupby(
            "turno",
            as_index=False
        )["defectos"].sum()

        fig = px.bar(
            defects_shift,
            x="turno",
            y="defectos",
            color="turno",
            title="Defectos por turno",
            color_discrete_sequence=[
                BLUE, TEAL, ORANGE
            ],
            text_auto=","
        )

        fig.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="Unidades defectuosas"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.metric(
        "Porcentaje de defectos (defectos / producción)",
        f"{pct_def:.2f}%"
    )

    st.caption(
        "El porcentaje se calcula como defectos totales "
        "divididos entre producción total. No se limita "
        "a 100%, pues se conserva el cálculo directo."
    )


# ==================================================
# 3. VARIABLES OPERATIVAS
# ==================================================

with tabs[2]:

    st.subheader("Monitoreo de variables operativas")

    st.caption(
        "Se muestra el promedio por hora para facilitar "
        "la lectura de la tendencia temporal."
    )

    hourly = (
        f.set_index("timestamp")
        .groupby("linea")[
            [
                "temperatura",
                "vibracion",
                "presion"
            ]
        ]
        .resample("h")
        .mean()
        .reset_index()
    )

    variables = [
        ("temperatura", "Temperatura"),
        ("vibracion", "Vibración"),
        ("presion", "Presión")
    ]

    for variable, label in variables:

        fig = px.line(
            hourly,
            x="timestamp",
            y=variable,
            color="linea",
            title=f"{label} promedio por hora",
            labels={
                "timestamp": "Fecha y hora",
                variable: label,
                "linea": "Línea"
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.info(
        "El archivo no documenta las unidades físicas "
        "de estas variables. Por ello, el dashboard "
        "conserva los valores originales sin asignar "
        "°C, bar, mm/s u otras unidades."
    )


# ==================================================
# 4. ANÁLISIS DE FALLAS
# ==================================================

with tabs[3]:

    st.subheader("Análisis de fallas")

    c1, c2 = st.columns(2)

    fail_line = f.groupby(
        "linea",
        as_index=False
    ).agg(
        registros_falla=("falla", "sum"),
        total_registros=("falla", "size")
    )

    fail_line["porcentaje_falla"] = (
        fail_line["registros_falla"]
        / fail_line["total_registros"] * 100
    )

    with c1:

        fig = px.bar(
            fail_line,
            x="linea",
            y="registros_falla",
            color="linea",
            text_auto=",",
            title="Cantidad de registros con falla por línea",
            color_discrete_sequence=[
                BLUE, TEAL, ORANGE
            ]
        )

        fig.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="Registros con falla"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with c2:

        fig = px.bar(
            fail_line,
            x="linea",
            y="porcentaje_falla",
            color="linea",
            text_auto=".2f",
            title="Porcentaje de registros con falla por línea",
            color_discrete_sequence=[
                BLUE, TEAL, ORANGE
            ]
        )

        fig.update_layout(
            showlegend=False,
            xaxis_title="",
            yaxis_title="Porcentaje (%)"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    fail_daily = f.groupby(
        pd.Grouper(
            key="timestamp",
            freq="D"
        ),
        as_index=False
    )["falla"].sum()

    fig = px.line(
        fail_daily,
        x="timestamp",
        y="falla",
        markers=True,
        title="Evolución diaria de registros con falla"
    )

    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Registros con falla"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.markdown(
        "#### Relación entre variables operativas y fallas"
    )

    variable = st.selectbox(
        "Variable operativa para explorar",
        [
            "temperatura",
            "vibracion",
            "presion"
        ],
        format_func=lambda x: {
            "temperatura": "Temperatura",
            "vibracion": "Vibración",
            "presion": "Presión"
        }[x]
    )

    fig = px.box(
        f,
        x="falla",
        y=variable,
        color="falla",
        points="outliers",
        labels={
            "falla": "Registro con falla (0 = No, 1 = Sí)",
            variable: variable.capitalize()
        },
        title=f"Distribución de {variable} según registro de falla",
        color_discrete_sequence=[
            BLUE,
            RED
        ]
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    corr = f[
        [variable, "falla"]
    ].corr(
        numeric_only=True
    ).iloc[0, 1]

    st.caption(
        f"Correlación lineal de Pearson entre "
        f"{variable} y falla en el subconjunto filtrado: "
        f"{corr:.3f}. Es una asociación descriptiva "
        "y no demuestra causalidad."
    )


# ==================================================
# TABLA Y DESCARGA DE DATOS
# ==================================================

st.divider()

st.subheader("Consulta y descarga de registros")

st.caption(
    "La tabla y el archivo descargable respetan "
    "los filtros globales."
)

st.dataframe(
    f.drop(
        columns=["fecha_hora", "fecha"],
        errors="ignore"
    ),
    use_container_width=True,
    hide_index=True
)

csv = f.drop(
    columns=["fecha_hora", "fecha"],
    errors="ignore"
).to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    "⬇️ Descargar datos filtrados (CSV)",
    data=csv,
    file_name="datos_industriales_filtrados.csv",
    mime="text/csv"
)


# ==================================================
# CALIDAD DE LOS DATOS
# ==================================================

with st.expander("Calidad y estructura de los datos"):

    q1, q2, q3 = st.columns(3)

    q1.metric(
        "Registros cargados",
        f"{len(df):,}"
    )

    q2.metric(
        "Valores faltantes",
        f"{int(df.isna().sum().sum()):,}"
    )

    q3.metric(
        "Filas duplicadas",
        f"{int(df.duplicated().sum()):,}"
    )

    st.write("Tipos de datos:")

    st.dataframe(
        df.dtypes.astype(str).rename("tipo").to_frame(),
        use_container_width=True
    )

    st.write("Estadísticas descriptivas:")

    st.dataframe(
        df.describe().T,
        use_container_width=True
    )


# --------------------------------------------------
# PIE DE PÁGINA
# --------------------------------------------------

st.markdown("""
<p class="note">
Fuente: dataset_planta_bigdata.csv suministrado
para el Proyecto Integrador.
<br>
Herramientas: Python, Pandas, Streamlit y Plotly.
</p>
""", unsafe_allow_html=True)


   
