# 🏭 Dashboard Industrial – Monitoreo de Planta de Producción

**Proyecto Integrador · Digitalización de Plantas Productivas**

Aplicación web interactiva desarrollada en **Python + Streamlit** para supervisar el desempeño de una planta con **3 líneas de producción** y **3 turnos**, a partir de 30 días de operación (1 al 30 de octubre de 2026): **129.600 registros** (1 por minuto por línea) del archivo `dataset_planta_bigdata.csv`.

| | |
| --- | --- |
| 🔗 **Dashboard público** | https://nombre-proyecto.streamlit.app *(reemplazar)* |
| 💻 **Repositorio** | https://github.com/usuario/repositorio *(reemplazar)* |
| 🎥 **Video de sustentación** | (https://youtu.be/fNjBx3lLCVU?si=tIp9Kb1V50O5MFIU) |

## 👷 Ingenieros encargados

1. Isabel Cuadro Bracho
2. Paulina Hernández
3. Santiago Saldarriaga

---

## 🎯 Objetivo

Convertir los datos históricos de la planta en información útil para la supervisión: comparar líneas y turnos, vigilar variables operativas, entender los defectos y las fallas, y apoyar decisiones con hallazgos y recomendaciones basados en los datos.

## ✨ Funcionalidades

La app tiene **siete pestañas** y una barra lateral de filtros.

| Pestaña | Contenido |
| --- | --- |
| 📊 **Resumen general** | 6 KPI (producción total y promedio, defectos totales y %, registros con falla y %). Los porcentajes se muestran en **gráficos circulares (dona)**. Incluye un **semáforo** de estado de la planta y un comparativo por línea. |
| 🏗️ **Producción y calidad** | Producción por línea, por turno y en el tiempo; **carrera animada** de producción acumulada día a día (▶); producción promedio por hora del día; defectos y % de defectos por línea y turno. |
| 🌡️ **Variables operativas** | Tres series temporales independientes (temperatura, vibración y presión) con promedio de referencia y estadísticas descriptivas. |
| 🚨 **Análisis de fallas** | Fallas por línea, % por línea, evolución temporal, **mapa de calor línea × turno**, relación variable operativa vs. falla (boxplot y % de fallas por quintil) y **simulador de riesgo histórico**. |
| 🧠 **Análisis avanzado** *(extra)* | **Índice de salud** por línea (radar), **detector de anomalías** con sensibilidad ajustable, **mapa 3D** de condiciones operativas, matriz de correlación, producción por operario y mapa de calor de fallas día × hora. |
| 🗂️ **Datos** | Tabla interactiva con los registros filtrados y **descarga en CSV**. |
| 💡 **Hallazgos y recomendaciones** | 3 hallazgos y 3 recomendaciones calculados a partir de los datos. |

### Filtros (barra lateral)
- Línea de producción (una, varias o todas)
- Turno (uno o varios)
- Rango de fechas
- Agregación temporal de las gráficas (15 minutos, hora o día)

Todos los KPI, gráficas, la tabla y la descarga respetan los filtros.

### Extras añadidos
- Banner animado y tarjetas con efectos al pasar el mouse.
- Paleta de colores **Sandbox** (`#1CBBC4`, `#4FD190`, `#FFB762`, `#FF9459`) con un color fijo para cada línea y turno.
- Semáforo de planta, carrera animada, radar de salud, detector de anomalías, mapa 3D y simulador de riesgo histórico.
- Nota desplegable "ℹ️ Notas sobre los datos" dentro de la app.

---

## 🔍 Hallazgos principales (periodo completo)

1. **La Línea 3 concentra las fallas y la peor calidad:** 6,29 % de registros con falla (Línea 1: 2,60 %; Línea 2: 2,82 %) y 41,2 % de defectos (33,3 % y 35,8 % en las otras). También es la de menor producción.
2. **El turno Noche es el más débil:** produce 6,14 unidades por registro (Mañana: 6,88) y tiene 5,85 % de registros con falla, casi el doble que Mañana (3,03 %) y Tarde (2,83 %). El punto más crítico es la Línea 3 en turno Noche (8,3 %).
3. **Vibración y temperatura altas se asocian con más fallas; la presión no.** En el quintil más alto de vibración la tasa de falla es de ~10 % frente a 2–3 % en el resto; en temperatura, ~9,6 % frente a ~2,5 %. Por quintiles de presión la tasa es prácticamente constante.

## ✅ Recomendaciones

1. Definir **alertas por umbral** de vibración y temperatura, validadas con mantenimiento, y documentar las unidades de los sensores.
2. Priorizar una **revisión de mantenimiento y calidad en la Línea 3**.
3. **Investigar el turno Noche** y estandarizar las prácticas del turno Mañana, que tiene la mayor productividad y menos defectos.

---

## 📁 Estructura del repositorio

```
├── app.py                        # Aplicación Streamlit
├── requirements.txt              # Dependencias
├── README.md                     # Este archivo
├── dataset_planta_bigdata.csv    # Datos de la planta
└── .devcontainer/                # Configuración opcional de entorno (Codespaces)
```

## ▶️ Ejecución local

```bash
git clone https://github.com/usuario/repositorio.git
cd repositorio
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Dependencias (`requirements.txt`):

```
streamlit>=1.35
pandas>=2.2
plotly>=5.20
```

## ☁️ Despliegue en Streamlit Community Cloud

1. Subir el repositorio público a GitHub (con `app.py`, `requirements.txt` y el CSV en la raíz).
2. Entrar a <https://share.streamlit.io> con la cuenta de GitHub.
3. **Create app** → seleccionar el repositorio, la rama `main` y el archivo principal `app.py`.
4. **Deploy** y verificar la URL pública.

---

## 📝 Notas y decisiones sobre los datos

- **Calidad de los datos:** sin valores faltantes ni duplicados; las 3 líneas y los 3 turnos tienen el mismo número de registros.
- **Turnos según la hora:** Mañana 06–13 h, Tarde 14–21 h, Noche 22–05 h.
- **Unidades:** el dataset no documenta las unidades de temperatura, vibración, presión ni del intervalo de producción, por lo que se muestran **sin unidades**.
- **% de defectos** = suma de defectos / suma de producción. Hay **542 registros con más defectos que unidades producidas**; se conservan sin modificar y la app lo avisa. El % global (~36,5 %) es alto y conviene validar con la planta cómo se definen ambas variables.
- **% de registros con falla** = registros con `falla = 1` / total de registros.
- **Agregación temporal:** como hay 1 registro por minuto, las gráficas se agrupan por hora (por defecto) para que sean legibles.
- **Índice de salud:** indicador comparativo propio del dashboard. Cada eje (productividad, calidad, confiabilidad, estabilidad de vibración y de temperatura) se normaliza respecto a la mejor línea de la selección y el índice es su promedio. No es un estándar industrial.
- **Simulador y anomalías:** el simulador muestra la frecuencia histórica de fallas bajo ciertas condiciones; no es una predicción. Las anomalías se detectan con puntajes z por línea. La relación entre variables y fallas es una asociación observada, no prueba causalidad.
- Los hallazgos de la pestaña correspondiente se calculan con el periodo completo, sin filtros.

## 🛠️ Tecnologías

Python · Pandas · Streamlit · Plotly · GitHub · Streamlit Community Cloud
