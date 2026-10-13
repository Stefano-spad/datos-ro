import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Datos RO", page_icon="📊", layout="wide")

# ------------------------------------------------------------------
# CONFIGURACIÓN: nombres de archivo y columnas
# ------------------------------------------------------------------
NOMBRE_CSV = "Datos_RO_corregido.csv"
COL_GEN = "Fecha de Generación del Reclamo"
COL_CIERRE = "Fecha de Cierre Reclamo"
COL_ESTADO = "Estado del Reclamo"
COL_MOTIVO = "Motivo del Reclamo"
COL_SUCURSAL = "Sucursal Origen"
COL_AGENTE = "Agente Asignado al Reclamo"
COL_DIAS = "Días hasta Finalización"   # columna nueva (calculada)
COL_TIEMPO = "Tiempo de cierre"        # columna nueva (calculada)
MOTIVO_ROJO = "1-Exceso de Consumo o Monto Factura"

ORDEN_TIEMPO = ["Rápido", "Medio", "Lento", "Tardío", "Revisar fecha"]
COLOR_TIEMPO = {
    "Rápido": "#2E7D32",         # verde
    "Medio": "#F9A825",          # amarillo
    "Lento": "#EF6C00",          # naranja
    "Tardío": "#6A1B9A",         # violeta
    "Revisar fecha": "#757575",  # gris
}
PALETA = ["#1565C0", "#00897B", "#F9A825", "#6A1B9A", "#EF6C00",
          "#00ACC1", "#7CB342", "#C2185B", "#5D4037", "#3949AB",
          "#546E7A", "#8E24AA"]
TEXTURAS = ["/", "\\", "x", "-", "|", "+", ".", "/", "\\", "x", "-", "|"]

# ------------------------------------------------------------------
# ESTILO: fondo celeste con textura
# ------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #D6EEFB;
        background-image:
            radial-gradient(rgba(21, 101, 192, 0.16) 1.6px, transparent 1.6px),
            repeating-linear-gradient(45deg, rgba(255,255,255,0.40) 0 10px,
                                      transparent 10px 20px);
        background-size: 24px 24px, auto;
    }
    [data-testid="stSidebar"] {
        background-color: #A9DBF5;
        background-image:
            radial-gradient(rgba(13, 59, 102, 0.18) 1.6px, transparent 1.6px),
            repeating-linear-gradient(-45deg, rgba(255,255,255,0.30) 0 10px,
                                      transparent 10px 20px);
        background-size: 24px 24px, auto;
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp label,
    .stApp [data-testid="stMarkdownContainer"], [data-testid="stSidebar"] * {
        color: #0D3B66;
    }
    [data-testid="stHeader"] { background: transparent; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------
# 1) Cargar y preparar los datos (se guarda en memoria para ir rápido)
# ------------------------------------------------------------------
@st.cache_data
def cargar_datos():
    carpeta = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.join(carpeta, NOMBRE_CSV)
    try:
        d = pd.read_csv(ruta, sep=";", encoding="utf-8-sig")
    except UnicodeDecodeError:
        d = pd.read_csv(ruta, sep=";", encoding="cp1252")

    # Fechas (formato día/mes/año)
    d[COL_GEN] = pd.to_datetime(d[COL_GEN], dayfirst=True, errors="coerce")
    d[COL_CIERRE] = pd.to_datetime(d[COL_CIERRE], dayfirst=True, errors="coerce")

    # Limpieza: "cerrado" y "Cerrado" pasan a ser lo mismo; vacíos con nombre claro
    d[COL_ESTADO] = d[COL_ESTADO].str.strip().str.capitalize()
    d[COL_MOTIVO] = d[COL_MOTIVO].fillna("Sin motivo")

    # NUEVA COLUMNA: días entre generación y cierre
    # (solo si el reclamo tiene Estado y tiene fecha de cierre)
    dias = (d[COL_CIERRE] - d[COL_GEN]).dt.days
    d[COL_DIAS] = dias.where(d[COL_ESTADO].notna() & d[COL_CIERRE].notna())

    # NUEVA COLUMNA: clasificación según los días
    #   0 a 5 = Rápido | 6 a 10 = Medio | 11 a 20 = Lento | 21 o más = Tardío
    #   negativos = la fecha de cierre es anterior a la de generación (revisar)
    d[COL_TIEMPO] = pd.cut(
        d[COL_DIAS],
        bins=[-float("inf"), -1, 5, 10, 20, float("inf")],
        labels=["Revisar fecha", "Rápido", "Medio", "Lento", "Tardío"],
    ).astype(object)
    return d


df = cargar_datos()

# Colores y texturas fijos por motivo (el rojo es para el Exceso de Consumo)
motivos = sorted(df[COL_MOTIVO].unique())
color_motivo, textura_motivo = {}, {}
otros = [c for c in PALETA if c not in ("#C2185B",)]
i = 0
for m in motivos:
    if m == MOTIVO_ROJO:
        color_motivo[m] = "#D32F2F"
        textura_motivo[m] = "/"
    else:
        color_motivo[m] = otros[i % len(otros)]
        textura_motivo[m] = TEXTURAS[(i + 1) % len(TEXTURAS)]
        i += 1


def mostrar(fig):
    """Muestra un gráfico de Plotly ocupando todo el ancho."""
    fig.update_layout(
        paper_bgcolor="rgba(255,255,255,0.80)",
        plot_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#0D3B66"),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:  # versiones viejas de Streamlit
        st.plotly_chart(fig, use_container_width=True)


def tarjeta(titulo, valor, color):
    """Tarjeta grande de color para un KPI."""
    return f"""
    <div style="background:{color}; border-radius:14px; padding:18px 10px; min-height:118px;
                text-align:center; margin-bottom:10px;
                box-shadow:0 2px 6px rgba(0,0,0,0.18);">
        <div style="font-size:15px; color:white; opacity:0.92;">{titulo}</div>
        <div style="font-size:38px; font-weight:700; color:white;">{valor}</div>
    </div>"""


def miles(n):
    return f"{n:,.0f}".replace(",", ".")


def pct(parte, base):
    """Porcentaje con coma decimal, por ejemplo 85,7%."""
    return f"{parte / base * 100:.1f}".replace(".", ",") + "%"


def dec(x):
    """Número con 1 decimal y coma, por ejemplo 4,7."""
    return f"{x:.1f}".replace(".", ",")


def caja(html):
    """Caja blanca semitransparente para textos."""
    st.markdown(
        f'''<div style="background:rgba(255,255,255,0.80); border-radius:12px;
        padding:14px 20px; margin:6px 0 14px 0; color:#0D3B66; line-height:1.55;
        box-shadow:0 1px 4px rgba(0,0,0,0.10);">{html}</div>''',
        unsafe_allow_html=True,
    )


MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


# ------------------------------------------------------------------
# 2) Barra lateral: filtros
# ------------------------------------------------------------------
st.sidebar.title("🔎 Filtros")

gen_min, gen_max = df[COL_GEN].min().date(), df[COL_GEN].max().date()
rango_gen = st.sidebar.date_input(
    "Fecha de Generación del Reclamo", value=(gen_min, gen_max),
    min_value=gen_min, max_value=gen_max, format="DD/MM/YYYY",
)

cie_min, cie_max = df[COL_CIERRE].min().date(), df[COL_CIERRE].max().date()
rango_cie = st.sidebar.date_input(
    "Fecha de Cierre del Reclamo", value=(cie_min, cie_max),
    min_value=cie_min, max_value=cie_max, format="DD/MM/YYYY",
)
incluir_sin_cierre = st.sidebar.checkbox(
    "Incluir reclamos sin fecha de cierre (pendientes)", value=True
)

st.sidebar.markdown("**Categorías** (vacío = todas)")
sel_motivo = st.sidebar.multiselect(COL_MOTIVO, motivos, placeholder="Todos")
sel_sucursal = st.sidebar.multiselect(
    COL_SUCURSAL, sorted(df[COL_SUCURSAL].dropna().unique()), placeholder="Todas"
)
sel_agente = st.sidebar.multiselect(
    COL_AGENTE, sorted(df[COL_AGENTE].dropna().unique()), placeholder="Todos"
)
top_n = st.sidebar.slider("Sucursales a mostrar en el heatmap", 5, 40, 15)

# Si el usuario eligió solo una fecha del calendario, esperar a que elija la otra
if len(rango_gen) != 2 or len(rango_cie) != 2:
    st.info("Elegí la fecha de inicio **y** la fecha de fin en los calendarios.")
    st.stop()

# ------------------------------------------------------------------
# 3) Aplicar los filtros
# ------------------------------------------------------------------
f = df[df[COL_GEN].between(pd.Timestamp(rango_gen[0]), pd.Timestamp(rango_gen[1]))]

en_rango_cierre = f[COL_CIERRE].between(
    pd.Timestamp(rango_cie[0]), pd.Timestamp(rango_cie[1])
)
if incluir_sin_cierre:
    f = f[en_rango_cierre | f[COL_CIERRE].isna()]
else:
    f = f[en_rango_cierre]

if sel_motivo:
    f = f[f[COL_MOTIVO].isin(sel_motivo)]
if sel_sucursal:
    f = f[f[COL_SUCURSAL].isin(sel_sucursal)]
if sel_agente:
    f = f[f[COL_AGENTE].isin(sel_agente)]

# ------------------------------------------------------------------
# 4) Título, filas y columnas
# ------------------------------------------------------------------
st.title("📊 Datos RO")
caja(
    "<b>¿Qué busca este proyecto?</b><br>"
    "Esta base de datos reúne los reclamos comerciales surgidos en la empresa EPEC "
    "(donde trabajé) durante este período (del "
    f"{df[COL_GEN].min().strftime('%d/%m/%Y')} al {df[COL_GEN].max().strftime('%d/%m/%Y')}). "
    "El análisis busca entender <b>cuántos</b> reclamos se generan, <b>por qué motivo</b>, "
    "<b>en qué sucursales</b>, a cargo de <b>qué agentes</b> y <b>cuánto tardan en cerrarse</b>, "
    "para identificar debilidades y problemas del proceso, como reclamos lentos, "
    "tardíos o pendientes.<br>"
    "Por política de protección de datos, se modificaron los nombres de los "
    "participantes (excepto el mío) y los números de suministro.<br>"
    "Esta información se usará luego para <b>optimizar y modernizar el flujo de "
    "gestión de reclamos</b> a través del portal web de la empresa."
    "<div style='margin-top:22px; color:#000000; font-size:0.85em;'>"
    "Usá los filtros de la barra lateral: todos los gráficos, indicadores "
    "e insights se actualizan solos.</div>"
)
st.write(
    f"El archivo tiene **{miles(df.shape[0])}** filas y **{df.shape[1]}** columnas "
    f"(incluye 2 calculadas). Con los filtros actuales se muestran "
    f"**{miles(len(f))}** reclamos."
)

if f.empty:
    st.warning("No hay reclamos con esos filtros. Probá ampliar la selección.")
    st.stop()

# ------------------------------------------------------------------
# 5) KPIs
# ------------------------------------------------------------------
total = len(f)
cerrados = int((f[COL_ESTADO] == "Cerrado").sum())
pendientes = int((f[COL_ESTADO] == "Pendiente").sum())
dias_ok = f[COL_DIAS][f[COL_DIAS] >= 0]
clasificados = f[COL_TIEMPO].isin(["Rápido", "Medio", "Lento", "Tardío"])
pct_rapidos = (f[COL_TIEMPO] == "Rápido").sum() / clasificados.sum() * 100 if clasificados.any() else 0
pct_cerrados = cerrados / total * 100

k = st.columns(6)
k[0].markdown(tarjeta("Total de reclamos", miles(total), "#1565C0"), unsafe_allow_html=True)
k[1].markdown(tarjeta("Cerrados", f"{pct_cerrados:.1f}%".replace(".", ","), "#2E7D32"), unsafe_allow_html=True)
k[2].markdown(tarjeta("Pendientes", miles(pendientes), "#EF6C00"), unsafe_allow_html=True)
k[3].markdown(tarjeta("Días promedio", f"{dias_ok.mean():.1f}".replace(".", ",") if len(dias_ok) else "-", "#6A1B9A"), unsafe_allow_html=True)
k[4].markdown(tarjeta("Mediana de días", f"{dias_ok.median():.0f}" if len(dias_ok) else "-", "#00897B"), unsafe_allow_html=True)
k[5].markdown(tarjeta("Cierres rápidos", f"{pct_rapidos:.1f}%".replace(".", ","), "#C2185B"), unsafe_allow_html=True)

# ------------------------------------------------------------------
# 6) Gráficos
# ------------------------------------------------------------------
# --- Barras por Motivo (el de Exceso de Consumo en rojo, con texturas) ---
g_motivo = f.groupby(COL_MOTIVO).size().reset_index(name="Reclamos")
fig = px.bar(
    g_motivo, x="Reclamos", y=COL_MOTIVO, orientation="h", text="Reclamos",
    color=COL_MOTIVO, color_discrete_map=color_motivo,
    pattern_shape=COL_MOTIVO, pattern_shape_map=textura_motivo,
    title="Reclamos por Motivo del Reclamo",
)
fig.update_traces(textposition="outside", cliponaxis=False)
fig.update_layout(showlegend=False, yaxis=dict(categoryorder="total ascending", title=""))
mostrar(fig)

col1, col2 = st.columns(2)

# --- Evolución por fecha de generación ---
with col1:
    diario = f.groupby(f[COL_GEN].dt.normalize()).size()
    diario = diario.reindex(
        pd.date_range(diario.index.min(), diario.index.max()), fill_value=0
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=diario.index, y=diario.values, name="Reclamos por día",
        mode="lines", line=dict(color="#42A5F5", width=1.5),
        fill="tozeroy", fillpattern=dict(shape="/", fgcolor="#42A5F5", bgcolor="rgba(66,165,245,0.15)"),
    ))
    fig.add_trace(go.Scatter(
        x=diario.index, y=diario.rolling(7, min_periods=1).mean(),
        name="Promedio de 7 días", mode="lines", line=dict(color="#E65100", width=3),
    ))
    fig.update_layout(
        title="Evolución de reclamos por Fecha de Generación",
        legend=dict(orientation="h", y=-0.15),
    )
    mostrar(fig)

# --- Tiempo de cierre ---
with col2:
    g_t = (f[COL_TIEMPO].value_counts().reindex(ORDEN_TIEMPO).dropna()
           .reset_index())
    g_t.columns = [COL_TIEMPO, "Reclamos"]
    fig = px.bar(
        g_t, x=COL_TIEMPO, y="Reclamos", text="Reclamos",
        color=COL_TIEMPO, color_discrete_map=COLOR_TIEMPO,
        pattern_shape=COL_TIEMPO,
        pattern_shape_map={"Rápido": "/", "Medio": "x", "Lento": "-",
                           "Tardío": "+", "Revisar fecha": "."},
        title="Reclamos según Tiempo de cierre",
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(showlegend=False, xaxis_title="")
    mostrar(fig)

col3, col4 = st.columns(2)

# --- Reclamos por agente ---
with col3:
    g_ag = f.groupby(COL_AGENTE).size().reset_index(name="Reclamos")
    fig = px.bar(
        g_ag, x="Reclamos", y=COL_AGENTE, orientation="h", text="Reclamos",
        color=COL_AGENTE, color_discrete_sequence=PALETA,
        pattern_shape=COL_AGENTE, pattern_shape_sequence=TEXTURAS,
        title="Reclamos por Agente Asignado",
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(showlegend=False, yaxis=dict(categoryorder="total ascending", title=""))
    mostrar(fig)

# --- Estado ---
with col4:
    g_e = f[COL_ESTADO].fillna("Sin estado").value_counts().reset_index()
    g_e.columns = [COL_ESTADO, "Reclamos"]
    g_e["Leyenda"] = g_e[COL_ESTADO] + " (" + g_e["Reclamos"].map(miles) + ")"
    colores_estado = {"Cerrado": "#2E7D32", "Pendiente": "#EF6C00", "Sin estado": "#90A4AE"}
    fig = px.pie(
        g_e, names="Leyenda", values="Reclamos", hole=0.45,
        color="Leyenda",
        color_discrete_map={
            r["Leyenda"]: colores_estado.get(r[COL_ESTADO], "#1565C0")
            for _, r in g_e.iterrows()
        },
        title="Reclamos por Estado",
    )
    fig.update_traces(textinfo="none")
    mostrar(fig)

# --- Heatmap: Sucursal de origen x Motivo ---
top_suc = f[COL_SUCURSAL].value_counts().head(top_n).index
cruce = pd.crosstab(
    f[f[COL_SUCURSAL].isin(top_suc)][COL_SUCURSAL],
    f[f[COL_SUCURSAL].isin(top_suc)][COL_MOTIVO],
)
cruce = cruce.loc[cruce.sum(axis=1).sort_values(ascending=False).index]
cruce = cruce[cruce.sum().sort_values(ascending=False).index]

# Escala de color logarítmica: así se distinguen también las sucursales chicas
# (si no, Córdoba pinta todo lo demás de amarillo clarito). Los números que se
# ven escritos en cada celda son los reclamos reales.
marcas = [0, 1, 10, 100, 1000, 10000]
fig = go.Figure(go.Heatmap(
    z=np.log1p(cruce.values), x=cruce.columns, y=cruce.index,
    text=cruce.values, texttemplate="%{text}",
    customdata=cruce.values,
    hovertemplate="Sucursal: %{y}<br>Motivo: %{x}<br>Reclamos: %{customdata}<extra></extra>",
    colorscale="YlOrRd",
    colorbar=dict(title="Reclamos", tickvals=np.log1p(marcas),
                  ticktext=[str(m) for m in marcas]),
))
fig.update_layout(
    title=f"Heatmap: reclamos por Sucursal de origen y Motivo "
          f"(top {len(cruce)} sucursales, escala logarítmica)",
    height=max(380, 28 * len(cruce) + 220),
    yaxis=dict(autorange="reversed", title="Sucursal de origen"),
    xaxis=dict(tickangle=-30, title="Motivo del Reclamo"),
)
mostrar(fig)

# ------------------------------------------------------------------
# 7) Tabla (con los filtros aplicados)
# ------------------------------------------------------------------
st.subheader("Tabla de reclamos")
vista = f.copy()
vista[COL_GEN] = vista[COL_GEN].dt.strftime("%d/%m/%Y")
vista[COL_CIERRE] = vista[COL_CIERRE].dt.strftime("%d/%m/%Y")
st.dataframe(vista)

# ------------------------------------------------------------------
# 8) Insights (se calculan con los datos filtrados)
# ------------------------------------------------------------------
st.subheader("💡 Insights")
st.caption("Se recalculan con los filtros que tengas aplicados.")

ins = []

# Motivo principal (solo tiene sentido si quedan varios motivos)
vm = f[COL_MOTIVO].value_counts()
if len(vm) > 1:
    ins.append(
        f"<b>Motivo principal:</b> «{vm.index[0]}» concentra el {pct(vm.iloc[0], total)} "
        f"de los reclamos ({miles(vm.iloc[0])} de {miles(total)})."
    )

# Concentración por sucursal
vs = f[COL_SUCURSAL].value_counts()
if len(vs) > 1:
    txt = f"<b>Concentración por sucursal:</b> {vs.index[0]} origina el {pct(vs.iloc[0], total)} de los reclamos"
    if len(vs) >= 3:
        txt += f"; las 3 principales ({', '.join(vs.head(3).index)}) suman el {pct(vs.head(3).sum(), total)}"
    ins.append(txt + ".")

# Carga de trabajo por agente
va = f[COL_AGENTE].value_counts()
if len(va) > 1:
    ins.append(
        f"<b>Carga de trabajo:</b> {va.index[0]} tiene asignado el {pct(va.iloc[0], total)} "
        f"de los reclamos; entre {va.index[0]} y {va.index[1]} reúnen el {pct(va.iloc[:2].sum(), total)}."
    )

# Velocidad de cierre
if len(dias_ok) and clasificados.any():
    n_cl = int(clasificados.sum())
    n_rap = int((f[COL_TIEMPO] == "Rápido").sum())
    n_lentos = int(f[COL_TIEMPO].isin(["Lento", "Tardío"]).sum())
    txt = (
        f"<b>Velocidad de cierre:</b> la mitad de los reclamos se cierra en "
        f"{dias_ok.median():.0f} día(s) o menos y el promedio es de {dec(dias_ok.mean())} días. "
        f"El {pct(n_rap, n_cl)} se resuelve rápido (hasta 5 días) "
        f"y el {pct(n_lentos, n_cl)} tarda más de 10 días."
    )
    if dias_ok.mean() > 1.5 * dias_ok.median():
        txt += " El promedio supera a la mediana porque unos pocos casos muy largos lo empujan hacia arriba."
    ins.append(txt)

    # Motivo y sucursal más lentos (solo categorías con suficientes casos)
    for col, minimo, nombre in [(COL_MOTIVO, 20, "Motivo más lento"),
                                (COL_SUCURSAL, 30, "Sucursal más lenta")]:
        g = f[f[COL_DIAS] >= 0].groupby(col)[COL_DIAS].agg(["mean", "count"])
        g = g[g["count"] >= minimo]
        if len(g) > 1:
            top = g["mean"].idxmax()
            ins.append(
                f"<b>{nombre}:</b> «{top}» tarda en promedio {dec(g.loc[top, 'mean'])} días "
                f"en cerrarse (el total es {dec(dias_ok.mean())}). Se consideran solo "
                f"categorías con al menos {minimo} reclamos cerrados."
            )

# Momentos de mayor demanda
dia_pico = diario.idxmax()
meses = f[COL_GEN].dt.to_period("M").value_counts()
mes_pico = meses.idxmax()
ins.append(
    f"<b>Momentos de mayor demanda:</b> el día con más reclamos fue el "
    f"{dia_pico.strftime('%d/%m/%Y')} ({miles(diario.max())}) y el mes más cargado "
    f"fue {MESES[mes_pico.month - 1]} de {mes_pico.year} "
    f"({miles(meses.max())}, {pct(meses.max(), total)} del total)."
)

# Pendientes
if pendientes > 0:
    ins.append(
        f"<b>Pendientes:</b> {miles(pendientes)} reclamos ({pct(pendientes, total)}) "
        f"todavía no tienen fecha de cierre."
    )

# Calidad de datos
n_rev = int((f[COL_TIEMPO] == "Revisar fecha").sum())
n_sin_motivo = int((f[COL_MOTIVO] == "Sin motivo").sum())
n_sin_estado = int(f[COL_ESTADO].isna().sum())
alertas = []
if n_rev:
    alertas.append(f"{miles(n_rev)} con fecha de cierre anterior a la de generación")
if n_sin_motivo:
    alertas.append(f"{miles(n_sin_motivo)} sin motivo")
if n_sin_estado:
    alertas.append(f"{miles(n_sin_estado)} sin estado")
if alertas:
    ins.append("<b>Calidad de datos a revisar:</b> " + "; ".join(alertas) + ".")

caja("<ul style='margin:0; padding-left:20px;'>"
     + "".join(f"<li style='margin-bottom:8px;'>{x}</li>" for x in ins)
     + "</ul>")
