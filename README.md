# proyecto-integrador
# 🏭 Dashboard Industrial – Monitoreo de Planta de Producción

Proyecto Integrador · Asignatura: **Digitalización de Plantas Productivas**

Aplicación web en **Streamlit** para analizar 30 días de operación (01–30 oct 2026) de una planta con
3 líneas de producción y 3 turnos, a partir de `data/dataset_planta_bigdata.csv`
(129 600 registros, 1 por minuto por línea).

🔗 **Dashboard público:** https://nombre-proyecto.streamlit.app  <!-- reemplazar -->
🎥 **Video de sustentación:** https://youtu.be/  <!-- reemplazar -->

## Integrantes

1. Isabel Cuadro Bracho
2. Paulina Hernandez
3. Santiago Saldarriaga

## Funcionalidades

| Sección | Contenido |
| --- | --- |
| Resumen general | 6 KPI (producción total y promedio, defectos y %, registros con falla y %) + comparativo por línea |
| Producción y calidad | Producción por línea, turno y en el tiempo; defectos y % de defectos por línea y turno |
| Variables operativas | Series temporales independientes de temperatura, vibración y presión |
| Análisis de fallas | Fallas por línea, % por línea, evolución temporal y relación variable operativa vs. falla |
| Datos | Tabla interactiva y descarga CSV de los datos filtrados |
| Hallazgos y recomendaciones | 3 hallazgos y 3 recomendaciones calculados a partir de los datos |

**Filtros (barra lateral):** línea (una, varias o todas), turno, rango de fechas y agregación
temporal (15 min / hora / día). Todos los KPI, gráficas, la tabla y la descarga respetan los filtros.

## Estructura del repositorio

```
dashboard-industrial/
├── app.py
├── requirements.txt
├── README.md
└── data/
    └── dataset_planta_bigdata.csv
```

## Ejecución local

```bash
git clone https://github.com/<usuario>/<repositorio>.git
cd <repositorio>
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Despliegue en Streamlit Community Cloud

1. Subir el repositorio (público) a GitHub.
2. Entrar a <https://share.streamlit.io> e iniciar sesión con GitHub.
3. **Create app** → seleccionar repositorio, rama `main` y archivo principal `app.py`.
4. **Deploy** y verificar la URL pública.

## Decisiones y notas sobre los datos

- Sin valores faltantes ni duplicados. Las 3 líneas y los 3 turnos tienen el mismo número de registros.
- Turnos según la hora: Mañana 06–13 h, Tarde 14–21 h, Noche 22–05 h.
- **Unidades:** el dataset no documenta las unidades de temperatura, vibración, presión ni del
  intervalo de producción, por lo que se presentan sin unidades.
- **% de defectos** = suma de defectos / suma de producción. Hay 542 registros con más defectos que
  producción; se conservan sin modificar y se avisa en el dashboard.
- **% de registros con falla** = registros con `falla = 1` / total de registros.
- La relación variable–falla es una asociación observada, no prueba causalidad.
- Los hallazgos se calculan con el periodo completo, sin filtros.

## Tecnologías

Python · Pandas · Streamlit · Plotly · GitHub · Streamlit Community Cloud
