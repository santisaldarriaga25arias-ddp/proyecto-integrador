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
    background: rgba(28, 187, 196, 0.12);
    border-left: 6px solid #1CBBC4;
    border-radius: 12px;
    padding: 14px 18px;
}
[data-testid="stMetric"] { transition: transform .2s, box-shadow .2s; animation: fadein .8s ease; }
[data-testid="stMetric"]:hover { transform: translateY(-4px); box-shadow: 0 8px 22px rgba(28,187,196,.35); }
@keyframes fadein { from {opacity:0; transform: translateY(12px);} to {opacity:1; transform:none;} }
@keyframes shine { 0% {background-position: 0% 50%;} 50% {background-position: 100% 50%;} 100% {background-position: 0% 50%;} }
.hero { background: linear-gradient(120deg,#1CBBC4,#4FD190,#FFB762,#FF9459); background-size: 300% 300%;
        animation: shine 12s ease infinite; border-radius: 18px; padding: 22px 28px; color: #fff; margin-bottom: 14px; }
.hero p { margin: 0 0 10px 0; font-size: 1.05rem; text-shadow: 0 1px 3px rgba(0,0,0,.25); }
.chip { display:inline-block; background: rgba(255,255,255,.25); border-radius: 20px; padding: 4px 14px;
        margin: 3px 6px 3px 0; font-size: .9rem; font-weight: 600; }
[data-testid="stMetricValue"] { font-weight: 700; }
button[data-baseweb="tab"] { font-weight: 600; }
h1 { background: linear-gradient(90deg, #1CBBC4, #4FD190, #FFB762, #FF9459);
     -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
</style>
""", unsafe_allow_html=True)

DATA_PATH = Path(__file__).parent / "dataset_planta_bigdata.csv"
INTEGRANTES = ["Isabel Cuadro Bracho", "Paulina Hernández", "Santiago Saldarriaga"]
ORDEN_TURNOS = ["Mañana", "Tarde", "Noche"]
GRANULARIDAD = {"15 minutos": "15min", "Hora": "h", "Día": "D"}
# Paleta "Sandbox": 1CBBC4 (turquesa), 4FD190 (verde), FFB762 (amarillo), FF9459 (naranja)
LINEA_COLORS = {"Linea 1": "#1CBBC4", "Linea 2": "#4FD190", "Linea 3": "#FFB762"}
TURNO_COLORS = {"Mañana": "#FFB762", "Tarde": "#FF9459", "Noche": "#1CBBC4"}
ESTADO_COLORS = {"Sin falla": "#4FD190", "Con falla": "#FF9459"}
C_DEFECTOS, C_FALLA, C_NEUTRO = "#FFB762", "#FF9459", "rgba(150,150,150,0.25)"
ESCALA_RIESGO = [[0, "#4FD190"], [0.5, "#FFB762"], [1, "#FF9459"]]
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

st.sidebar.markdown("---")
st.sidebar.markdown("**👷 Ingenieros encargados**")
for nombre in INTEGRANTES:
    st.sidebar.markdown(f"- {nombre}")

st.title("🏭 Dashboard de monitoreo – Planta de producción")
chips = "".join(f'<span class="chip">👷 {n}</span>' for n in INTEGRANTES)
datos = "".join(f'<span class="chip">{t}</span>' for t in
                [f"📅 {f_min} → {f_max}", f"🧾 {len(df):,} registros", "🏭 3 líneas", "⏱️ 3 turnos"])
st.markdown(
    '<div class="hero"><p>Supervisa productividad, calidad, variables operativas y fallas de la planta '
    "en un solo lugar: filtra, explora y descubre dónde actuar.</p>"
    f"{datos}<br>{chips}</div>", unsafe_allow_html=True)

with st.expander("ℹ️ Notas sobre los datos"):
    st.markdown(
        "- **Unidades:** el dataset no documenta las unidades de temperatura, vibración, presión "
        "ni del intervalo de producción, por eso se muestran sin unidades.\n"
        f"- **Agregación:** los datos son de 1 registro por minuto; las gráficas se agrupan por "
        f"**{gran_label.lower()}** (cámbialo en la barra lateral)."
    )

if dff.empty:
    st.warning("No hay registros con los filtros seleccionados. Ajusta los filtros.")
    st.stop()

tabs = st.tabs(["📊 Resumen general", "🏗️ Producción y calidad", "🌡️ Variables operativas",
                "🚨 Análisis de fallas", "🧠 Análisis avanzado", "🗂️ Datos",
                "💡 Hallazgos y recomendaciones"])

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
    base = df["falla"].mean() * 100          # referencia: toda la planta, todo el periodo
    actual = pct(fallas, len(dff))
    ratio = actual / base if base else 0
    msg = (f"{actual:.2f} % de registros con falla en la selección "
           f"(referencia, planta completa: {base:.2f} %).")
    if ratio <= 1.0:
        st.success(f"🟢 **Operación normal.** {msg}")
    elif ratio <= 1.5:
        st.warning(f"🟡 **Atención.** {msg}")
    else:
        st.error(f"🔴 **Crítico.** {msg}")
    st.caption("Semáforo: verde si la tasa de falla ≤ referencia, amarillo hasta 1,5 veces, rojo por encima.")
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

    acum = (dff.assign(dia=dff["timestamp"].dt.strftime("%Y-%m-%d"))
            .groupby(["dia", "linea"])["produccion"].sum().unstack(fill_value=0).cumsum()
            .stack().rename("acumulado").reset_index())
    st.plotly_chart(px.bar(acum, x="linea", y="acumulado", color="linea", animation_frame="dia",
                           color_discrete_map=LINEA_COLORS, text_auto=True,
                           range_y=[0, acum["acumulado"].max() * 1.1],
                           title="🏁 Carrera de producción acumulada día a día (pulsa ▶)",
                           labels={"linea": "Línea", "acumulado": "Unidades acumuladas"}))

    hh = (dff.assign(hora=dff["timestamp"].dt.hour)
          .groupby(["hora", "turno"], observed=True)["produccion"].mean().reset_index())
    st.plotly_chart(px.line(hh, x="hora", y="produccion", color="turno", markers=True,
                            color_discrete_map=TURNO_COLORS,
                            title="Producción promedio por hora del día (se aprecian los turnos)",
                            labels={"hora": "Hora del día", "produccion": "Unidades por registro"}))

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

    hm = (dff.groupby(["linea", "turno"], observed=True)["falla"].mean().mul(100)
          .reset_index().pivot(index="linea", columns="turno", values="falla"))
    hm = hm.reindex(columns=[t for t in ORDEN_TURNOS if t in hm.columns])
    st.plotly_chart(px.imshow(hm, text_auto=".2f", color_continuous_scale=ESCALA_RIESGO,
                              aspect="auto", title="Mapa de calor: % de registros con falla (línea × turno)",
                              labels={"color": "% falla", "x": "Turno", "y": "Línea"}))

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

# ------------------------------------------------ 5. Análisis avanzado
with tabs[4]:
    st.subheader("🧠 Análisis avanzado")
    st.caption("Herramientas extra de supervisión. Respetan los filtros de la barra lateral.")

    # --- Índice de salud
    st.markdown("### 🩺 Índice de salud por línea")
    gl = dff.groupby("linea").agg(prod=("produccion", "sum"), d=("defectos", "sum"),
                                  f=("falla", "mean"), vstd=("vibracion", "std"),
                                  tstd=("temperatura", "std"))
    gl["pdef"] = gl["d"] / gl["prod"]

    def inv(x):  # menor es mejor: la mejor línea obtiene 100
        return (x.min() / x * 100).replace([float("inf")], 100).fillna(100)

    sc = pd.DataFrame({"Productividad": gl["prod"] / gl["prod"].max() * 100,
                       "Calidad": inv(gl["pdef"]), "Confiabilidad": inv(gl["f"]),
                       "Estab. vibración": inv(gl["vstd"]),
                       "Estab. temperatura": inv(gl["tstd"])}).fillna(100)
    cats = list(sc.columns)
    sc["Índice"] = sc[cats].mean(axis=1)
    radar = go.Figure()
    for ln in sc.index:
        vals = sc.loc[ln, cats].tolist()
        radar.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=cats + cats[:1], fill="toself",
                                        name=ln, line_color=LINEA_COLORS.get(ln), opacity=0.6))
    radar.update_layout(polar=dict(radialaxis=dict(range=[0, 100])),
                        title="Radar de desempeño (100 = mejor línea)")
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(radar)
    for ln, val in sc["Índice"].sort_values(ascending=False).items():
        c2.metric(f"{ln} – índice de salud", f"{val:.0f} / 100")
    st.caption("Cada eje se normaliza frente a la mejor línea de la selección; el índice es el "
               "promedio de los cinco ejes. Es un indicador comparativo propio de este dashboard, "
               "no un estándar industrial.")

    # --- Anomalías
    st.markdown("### 🚨 Detector de anomalías")
    a1, a2 = st.columns(2)
    var_a = a1.selectbox("Variable a vigilar", list(VARIABLES), format_func=VARIABLES.get,
                         key="var_anom")
    zmax = a2.slider("Sensibilidad (desviaciones estándar respecto a la media de su línea)",
                     2.0, 5.0, 3.0, 0.5)
    g_a = dff.groupby("linea")[var_a]
    z = (dff[var_a] - g_a.transform("mean")) / g_a.transform("std")
    es_an = z.abs() >= zmax
    an, normal = dff[es_an], dff[~es_an]
    m = st.columns(3)
    m[0].metric("Anomalías detectadas", f"{len(an):,}")
    m[1].metric("% del total", f"{pct(len(an), len(dff)):.2f} %")
    base_f = dff["falla"].mean() * 100
    if len(an):
        tf = an["falla"].mean() * 100
        m[2].metric("% de esas anomalías con falla", f"{tf:.2f} %",
                    delta=f"{tf / base_f:.1f}× el promedio" if base_f else None,
                    delta_color="inverse")
    pl = pd.concat([normal.sample(min(4000, len(normal)), random_state=1).assign(Tipo="Normal"),
                    an.sample(min(3000, len(an)), random_state=1).assign(Tipo="Anomalía")])
    st.plotly_chart(px.scatter(pl, x="timestamp", y=var_a, color="Tipo", opacity=0.7,
                               color_discrete_map={"Normal": "#1CBBC4", "Anomalía": "#FF9459"},
                               title=f"Anomalías de {VARIABLES[var_a].lower()} (muestra para fluidez)",
                               labels={"timestamp": "Fecha", var_a: VARIABLES[var_a]}))

    # --- 3D
    st.markdown("### 🧊 Mapa 3D de condiciones operativas")
    fl, ok = dff[dff["falla"] == 1], dff[dff["falla"] == 0]
    mu = pd.concat([fl.sample(min(1500, len(fl)), random_state=1),
                    ok.sample(min(2500, len(ok)), random_state=1)])
    mu = mu.assign(Estado=mu["falla"].map({0: "Sin falla", 1: "Con falla"}))
    f3 = px.scatter_3d(mu, x="temperatura", y="vibracion", z="presion", color="Estado",
                       color_discrete_map=ESTADO_COLORS, opacity=0.7,
                       title="Temperatura × Vibración × Presión (arrastra para rotar)")
    f3.update_traces(marker_size=3)
    f3.update_layout(height=560)
    st.plotly_chart(f3)
    st.caption("Muestra aleatoria de hasta 4.000 registros (todas las fallas posibles hasta 1.500).")

    # --- Correlación y operarios
    c1, c2 = st.columns(2)
    cor = dff[["temperatura", "vibracion", "presion", "produccion", "defectos", "falla"]].corr().round(2)
    c1.plotly_chart(px.imshow(cor, text_auto=True, zmin=-1, zmax=1, aspect="auto",
                              color_continuous_scale=["#1CBBC4", "#FFFFFF", "#FF9459"],
                              title="Matriz de correlación"))
    op = dff.groupby("operario").agg(prod=("produccion", "mean"), f=("falla", "mean")).reset_index()
    op["f"] *= 100
    c2.plotly_chart(px.bar(op, x="operario", y="prod", text_auto=".2f",
                           color_discrete_sequence=["#4FD190"],
                           title="Producción promedio por operario",
                           labels={"prod": "Unidades por registro", "operario": "Operario"}))

    # --- Heatmap día × hora
    hd = (dff.assign(dia=dff["timestamp"].dt.strftime("%m-%d"), hora=dff["timestamp"].dt.hour)
          .pivot_table(index="dia", columns="hora", values="falla", aggfunc="sum"))
    st.plotly_chart(px.imshow(hd, aspect="auto", color_continuous_scale=ESCALA_RIESGO,
                              title="Mapa de calor de fallas: día × hora del día",
                              labels={"x": "Hora", "y": "Día", "color": "Fallas"}))

# ------------------------------------------------------ 6. Datos
with tabs[5]:
    st.subheader("Tabla de datos")
    st.caption(f"{len(dff):,} registros con los filtros aplicados.")
    st.dataframe(dff, height=450)
    st.download_button("⬇️ Descargar datos filtrados (CSV)",
                       data=dff.to_csv(index=False).encode("utf-8"),
                       file_name="datos_filtrados.csv", mime="text/csv")

# --------------------------------------- 6. Hallazgos y recomendaciones
with tabs[6]:
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
