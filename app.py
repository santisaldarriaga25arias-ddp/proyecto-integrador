"""Dashboard industrial – Proyecto Integrador: Digitalización de Plantas Productivas."""
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import plotly.express as px
    import plotly.graph_objects as go
except ModuleNotFoundError:
    st.error("Falta la dependencia 'plotly'. Verifica que requirements.txt esté en la raíz "
             "del repositorio (junto a app.py), en UTF-8, y reinicia la app.")
    st.stop()

st.set_page_config(page_title="Dashboard Planta Industrial", page_icon="🏭", layout="wide")

st.markdown("""
<style>
[data-testid="stMetric"] {
    background: rgba(0, 180, 216, 0.10);
    border-left: 6px solid #00B4D8;
    border-radius: 12px;
    padding: 14px 18px;
}
[data-testid="stMetricValue"] { font-weight: 700; }
button[data-baseweb="tab"] { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

DATA_PATH = Path(__file__).parent / "dataset_planta_bigdata.csv"
ORDEN_TURNOS = ["Mañana", "Tarde", "Noche"]
GRANULARIDAD = {"15 minutos": "15min", "Hora": "h", "Día": "D"}
LINEA_COLORS = {"Linea 1": "#00B4D8", "Linea 2": "#F77F00", "Linea 3": "#7B2CBF"}
TURNO_COLORS = {"Mañana": "#FFB703", "Tarde": "#FB5607", "Noche": "#3A0CA3"}
ESTADO_COLORS = {"Sin falla": "#2A9D8F", "Con falla": "#E63946"}
C_DEFECTOS, C_FALLA, C_NEUTRO = "#F77F00", "#E63946", "rgba(150,150,150,0.25)"
VARIABLES = {"temperatura": "Temperatura", "vibracion": "Vibración", "presion": "Presión"}


# ------------------------------------------------------------------ datos
@st.cache_data
def cargar_datos() -> pd.DataFrame:
    if not DATA_PATH.exists():
        st.error(f"No se encontró el archivo {DATA_PATH.name} en la raíz del repositorio. "
                 "Verifica que esté subido junto a app.py.")
        st.stop()
    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
    df = df.drop_duplicates()
    df["linea"] = df["linea"].str.replace("_", " ")
    df["turno"] = pd.Categorical(df["turno"], categories=ORDEN_TURNOS, ordered=True)
    return df.sort_values("timestamp").reset_index(drop=True)


def pct(num, den) -> float:
    return (num / den * 100) if den else 0.0


def donut(valor: float, titulo: str, color: str) -> go.Figure:
    """Gráfico circular (dona) para un porcentaje."""
    v = min(max(valor, 0), 100)
    fig = go.Figure(go.Pie(values=[v, 100 - v], hole=0.72, sort=False, direction="clockwise",
                           marker=dict(colors=[color, C_NEUTRO]), textinfo="none",
                           hoverinfo="skip"))
    fig.update_layout(title=dict(text=titulo, x=0.5), showlegend=False, height=300,
                      margin=dict(t=60, b=10, l=10, r=10),
                      annotations=[dict(text=f"<b>{valor:.2f} %</b>", x=0.5, y=0.5,
                                        font_size=28, showarrow=False)])
    return fig


df = cargar_datos()

# ---------------------------------------------------------------- filtros
st.sidebar.header("Filtros")
lineas = st.sidebar.multiselect("Línea de producción", sorted(df["linea"].unique()),
                                default=sorted(df["linea"].unique()))
turnos = st.sidebar.multiselect("Turno", ORDEN_TURNOS, default=ORDEN_TURNOS)
f_min, f_max = df["timestamp"].min().date(), df["timestamp"].max().date()
rango = st.sidebar.date_input("Rango de fechas", value=(f_min, f_max),
                              min_value=f_min, max_value=f_max)
gran_label = st.sidebar.selectbox("Agregación temporal", list(GRANULARIDAD), index=1)
freq = GRANULARIDAD[gran_label]

if isinstance(rango, (tuple, list)):
    ini, fin = (rango[0], rango[-1]) if len(rango) else (f_min, f_max)
else:
    ini = fin = rango

mask = (
    df["linea"].isin(lineas)
    & df["turno"].isin(turnos)
    & (df["timestamp"].dt.date >= ini)
    & (df["timestamp"].dt.date <= fin)
)
dff = df[mask]

st.title("🏭 Dashboard de monitoreo – Planta de producción")
st.markdown(
    "Aplicación para supervisar el desempeño de las tres líneas de producción: "
    "productividad, calidad, variables operativas y fallas, a partir de 30 días de "
    "registros históricos (1 registro por minuto por línea)."
)
st.caption(
    "⚠️ El dataset no documenta las unidades de temperatura, vibración, presión ni del intervalo "
    "de producción; por eso se muestran sin unidades. Las gráficas se agregan según la "
    f"granularidad elegida (actual: {gran_label.lower()})."
)

if dff.empty:
    st.warning("No hay registros con los filtros seleccionados. Ajusta los filtros.")
    st.stop()

tabs = st.tabs(["📊 Resumen general", "🏗️ Producción y calidad", "🌡️ Variables operativas",
                "🚨 Análisis de fallas", "🗂️ Datos", "💡 Hallazgos y recomendaciones"])

# ---------------------------------------------------------- 1. Resumen
with tabs[0]:
    st.subheader("Resumen general de la planta")
    prod_tot = int(dff["produccion"].sum())
    def_tot = int(dff["defectos"].sum())
    fallas = int(dff["falla"].sum())
    c = st.columns(4)
    c[0].metric("Producción total", f"{prod_tot:,}")
    c[1].metric("Producción promedio por registro", f"{dff['produccion'].mean():.2f}")
    c[2].metric("Defectos totales", f"{def_tot:,}")
    c[3].metric("Registros con falla", f"{fallas:,}")
    c = st.columns(2)
    c[0].plotly_chart(donut(pct(def_tot, prod_tot), "Porcentaje de defectos", C_DEFECTOS))
    c[1].plotly_chart(donut(pct(fallas, len(dff)), "% de registros con falla", C_FALLA))
    st.caption(f"{len(dff):,} registros entre {ini} y {fin}.")

    res = dff.groupby("linea", observed=True).agg(
        Producción=("produccion", "sum"), Defectos=("defectos", "sum"),
        Fallas=("falla", "sum"), Registros=("falla", "size"))
    res["% defectos"] = (res["Defectos"] / res["Producción"] * 100).round(2)
    res["% fallas"] = (res["Fallas"] / res["Registros"] * 100).round(2)
    st.markdown("**Comparativo por línea**")
    st.dataframe(res)

# --------------------------------------------- 2. Producción y calidad
with tabs[1]:
    st.subheader("Producción")
    c1, c2 = st.columns(2)
    p_linea = dff.groupby("linea", observed=True)["produccion"].sum().reset_index()
    c1.plotly_chart(px.bar(p_linea, x="linea", y="produccion", color="linea", color_discrete_map=LINEA_COLORS, text_auto=True,
                           title="Producción acumulada por línea",
                           labels={"linea": "Línea", "produccion": "Unidades"}))
    p_turno = dff.groupby("turno", observed=True)["produccion"].agg(["sum", "mean"]).reset_index()
    c2.plotly_chart(px.bar(p_turno, x="turno", y="sum", color="turno", color_discrete_map=TURNO_COLORS, text_auto=True,
                           title="Producción acumulada por turno",
                           labels={"turno": "Turno", "sum": "Unidades"},
                           category_orders={"turno": ORDEN_TURNOS}))
    st.caption("Producción promedio por registro en cada turno: " +
               " | ".join(f"{r.turno}: {r['mean']:.2f}" for _, r in p_turno.iterrows()))

    p_t = (dff.groupby([pd.Grouper(key="timestamp", freq=freq), "linea"], observed=True)
           ["produccion"].sum().reset_index())
    st.plotly_chart(px.line(p_t, x="timestamp", y="produccion", color="linea", color_discrete_map=LINEA_COLORS,
                            title=f"Evolución de la producción ({gran_label.lower()})",
                            labels={"timestamp": "Fecha", "produccion": "Unidades"}))

    st.subheader("Calidad")
    c1, c2, c3 = st.columns(3)
    d_linea = dff.groupby("linea", observed=True).agg(
        defectos=("defectos", "sum"), produccion=("produccion", "sum")).reset_index()
    d_linea["pct"] = d_linea["defectos"] / d_linea["produccion"] * 100
    c1.plotly_chart(px.bar(d_linea, x="linea", y="defectos", color="linea", color_discrete_map=LINEA_COLORS, text_auto=True,
                           title="Defectos por línea"))
    c2.plotly_chart(px.bar(d_linea, x="linea", y="pct", color="linea", color_discrete_map=LINEA_COLORS, text_auto=".2f",
                           title="% de defectos por línea",
                           labels={"pct": "% defectos / producción"}))
    d_turno = dff.groupby("turno", observed=True).agg(
        defectos=("defectos", "sum"), produccion=("produccion", "sum")).reset_index()
    d_turno["pct"] = d_turno["defectos"] / d_turno["produccion"] * 100
    c3.plotly_chart(px.bar(d_turno, x="turno", y="defectos", color="turno", color_discrete_map=TURNO_COLORS, text_auto=True,
                           title="Defectos por turno",
                           category_orders={"turno": ORDEN_TURNOS}))
    st.caption("% de defectos por turno: " +
               " | ".join(f"{r.turno}: {r.pct:.2f} %" for _, r in d_turno.iterrows()))
    n_inc = int((dff["defectos"] > dff["produccion"]).sum())
    if n_inc:
        st.info(f"Nota de calidad de datos: {n_inc:,} registros tienen más defectos que unidades "
                "producidas en el intervalo. Se conservan sin modificar; el % de defectos se "
                "calcula como suma de defectos / suma de producción.")

# ------------------------------------------------ 3. Variables operativas
with tabs[2]:
    st.subheader("Monitoreo de variables operativas")
    st.caption("Promedio por periodo y línea. Línea punteada = promedio global de la selección.")
    for col, nombre in VARIABLES.items():
        v = (dff.groupby([pd.Grouper(key="timestamp", freq=freq), "linea"], observed=True)[col]
             .mean().reset_index())
        fig = px.line(v, x="timestamp", y=col, color="linea", color_discrete_map=LINEA_COLORS,
                      title=f"{nombre} ({gran_label.lower()}, promedio)",
                      labels={"timestamp": "Fecha", col: nombre})
        fig.add_hline(y=dff[col].mean(), line_dash="dot", annotation_text="promedio")
        st.plotly_chart(fig)
    st.markdown("**Estadísticas descriptivas (selección actual)**")
    st.dataframe(dff[list(VARIABLES)].describe().T.round(2))

# --------------------------------------------------- 4. Fallas
with tabs[3]:
    st.subheader("Análisis de fallas")
    f_linea = dff.groupby("linea", observed=True).agg(
        fallas=("falla", "sum"), registros=("falla", "size")).reset_index()
    f_linea["pct"] = f_linea["fallas"] / f_linea["registros"] * 100
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(f_linea, x="linea", y="fallas", color="linea", color_discrete_map=LINEA_COLORS, text_auto=True,
                           title="Registros con falla por línea"))
    c2.plotly_chart(px.bar(f_linea, x="linea", y="pct", color="linea", color_discrete_map=LINEA_COLORS, text_auto=".2f",
                           title="% de registros con falla por línea",
                           labels={"pct": "% registros con falla"}))
    f_t = (dff.groupby([pd.Grouper(key="timestamp", freq=freq), "linea"], observed=True)
           ["falla"].sum().reset_index())
    st.plotly_chart(px.line(f_t, x="timestamp", y="falla", color="linea", color_discrete_map=LINEA_COLORS,
                            title=f"Evolución de registros con falla ({gran_label.lower()})",
                            labels={"timestamp": "Fecha", "falla": "Registros con falla"}))

    st.markdown("**Relación entre variables operativas y fallas**")
    var = st.selectbox("Variable operativa", list(VARIABLES), format_func=VARIABLES.get)
    c1, c2 = st.columns(2)
    tmp = dff.assign(Estado=dff["falla"].map({0: "Sin falla", 1: "Con falla"}))
    c1.plotly_chart(px.box(tmp, x="Estado", y=var, color="Estado", color_discrete_map=ESTADO_COLORS,
                           title=f"{VARIABLES[var]} según estado de falla",
                           labels={var: VARIABLES[var]}))
    try:
        tmp["rango"] = pd.qcut(dff[var], 5, duplicates="drop")
        tasa = tmp.groupby("rango", observed=True)["falla"].mean().mul(100).reset_index()
        tasa["rango"] = tasa["rango"].astype(str)
        c2.plotly_chart(px.bar(tasa, x="rango", y="falla", text_auto=".2f",
                               color_discrete_sequence=[C_FALLA],
                               title=f"% de fallas por quintil de {VARIABLES[var].lower()}",
                               labels={"rango": "Rango (quintiles)", "falla": "% con falla"}))
    except ValueError:
        c2.info("No hay suficientes datos para calcular quintiles.")
    st.caption("Esta relación es una asociación observada en los datos, no prueba causalidad.")

# ------------------------------------------------------ 5. Datos
with tabs[4]:
    st.subheader("Tabla de datos")
    st.caption(f"{len(dff):,} registros con los filtros aplicados.")
    st.dataframe(dff, height=450)
    st.download_button("⬇️ Descargar datos filtrados (CSV)",
                       data=dff.to_csv(index=False).encode("utf-8"),
                       file_name="datos_filtrados.csv", mime="text/csv")

# --------------------------------------- 6. Hallazgos y recomendaciones
with tabs[5]:
    st.subheader("Hallazgos y recomendaciones")
    st.caption("Calculados sobre el periodo completo (30 días, 3 líneas), sin filtros.")

    g = df.groupby("linea").agg(p=("produccion", "sum"), d=("defectos", "sum"),
                                f=("falla", "sum"), n=("falla", "size"))
    g["pd"] = g["d"] / g["p"] * 100
    g["pf"] = g["f"] / g["n"] * 100
    t = df.groupby("turno", observed=True).agg(p=("produccion", "mean"), f=("falla", "mean"),
                                               d=("defectos", "sum"), pt=("produccion", "sum"))
    t["pd"] = t["d"] / t["pt"] * 100
    umbral_v = df["vibracion"].quantile(0.8)
    umbral_t = df["temperatura"].quantile(0.8)
    f_vib = df.loc[df["vibracion"] > umbral_v, "falla"].mean() * 100
    f_vib_ok = df.loc[df["vibracion"] <= umbral_v, "falla"].mean() * 100
    f_tmp = df.loc[df["temperatura"] > umbral_t, "falla"].mean() * 100
    f_tmp_ok = df.loc[df["temperatura"] <= umbral_t, "falla"].mean() * 100
    peor, mejor = g["pf"].idxmax(), g["p"].idxmax()

    st.markdown("### Hallazgos")
    st.markdown(
        f"1. **La {peor} concentra las fallas y la peor calidad.** Tiene {g.loc[peor,'pf']:.2f} % de "
        f"registros con falla (resto de líneas: {g['pf'].drop(peor).min():.2f}–"
        f"{g['pf'].drop(peor).max():.2f} %) y {g.loc[peor,'pd']:.1f} % de defectos frente a "
        f"{g['pd'].drop(peor).min():.1f}–{g['pd'].drop(peor).max():.1f} % en las demás. "
        f"Además es la de menor producción; la de mayor producción es la {mejor} "
        f"({int(g.loc[mejor,'p']):,} unidades).")
    st.markdown(
        f"2. **El turno Noche es el más débil.** Produce {t.loc['Noche','p']:.2f} unidades por "
        f"registro (Mañana: {t.loc['Mañana','p']:.2f}), tiene {t.loc['Noche','f']*100:.2f} % de "
        f"registros con falla (≈2 veces los otros turnos) y {t.loc['Noche','pd']:.1f} % de defectos "
        f"(Mañana: {t.loc['Mañana','pd']:.1f} %).")
    st.markdown(
        f"3. **Vibración y temperatura altas se asocian con más fallas; la presión no.** Con vibración "
        f"en el 20 % superior (> {umbral_v:.2f}) la tasa de falla es {f_vib:.1f} % vs {f_vib_ok:.1f} % "
        f"en el resto; con temperatura en el 20 % superior (> {umbral_t:.1f}) es {f_tmp:.1f} % vs "
        f"{f_tmp_ok:.1f} %. Los registros por quintil de presión muestran una tasa de falla "
        "prácticamente constante.")
    st.markdown("### Recomendaciones")
    st.markdown(
        f"1. **Definir alertas por umbral** de vibración (> {umbral_v:.2f}) y temperatura "
        f"(> {umbral_t:.1f}) para anticipar fallas; validar los umbrales con mantenimiento y "
        "documentar las unidades de medida de los sensores.\n"
        f"2. **Priorizar una revisión de mantenimiento y calidad en la {peor}** (sensores, "
        "calibración, condiciones de operación), por ser la de mayor tasa de fallas y defectos.\n"
        "3. **Investigar el turno Noche** (supervisión, capacitación, condiciones de planta) y "
        "estandarizar prácticas del turno Mañana, que logra la mayor productividad y la menor "
        "tasa de defectos.")
    st.info("Observación de calidad de datos: el % de defectos global es alto (~36 %) y hay "
            "registros con más defectos que producción; conviene validar con la planta cómo se "
            "definen ambas variables antes de usar estas cifras como metas.")
