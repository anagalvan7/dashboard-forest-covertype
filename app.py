"""Dashboard: clasificación de la cobertura forestal del Bosque Nacional Roosevelt.

Ejecutar en local:   python app.py            (http://127.0.0.1:8050)
Despliegue (Render): gunicorn app:server
"""
import json

import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, ctx, dcc, html
from dash_iconify import DashIconify

import datos_dashboard as D
from datos_dashboard import (CLASES, COLOR, CONFIG, CORTO, EMOJI, ETIQ, LARGO, LIBRO,
                             fmt, miles, vacio)

app = Dash(
    __name__,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap",
    ],
    title="Cobertura Forestal · Roosevelt National Forest",
    suppress_callback_exceptions=True,
)
server = app.server


# =============================================================== componentes comunes
def icono(nombre, ancho=22):
    return DashIconify(icon=nombre, width=ancho, className="me-2")


def tarjeta(titulo, icon, cabecera, cuerpo, clase=""):
    return dbc.Card(
        [dbc.CardHeader([icono(icon), titulo], className=f"{cabecera} d-flex align-items-center"),
         dbc.CardBody(cuerpo)],
        className=f"tarjeta {clase}",
    )


def nota(texto, pagina=None, seccion=None):
    hijos = [html.B("💡 Interpretación: "), texto]
    if pagina:
        hijos += [" ", html.A(f"Profundiza en la sección {seccion} del Jupyter Book →",
                              href=LIBRO + pagina, target="_blank")]
    return html.Div(hijos, className="nota")


def kpi(etiqueta, valor, detalle, n):
    return html.Div([html.Div(etiqueta, className="etiqueta"), html.Div(valor, className="valor"),
                     html.Div(detalle, className="detalle")], className=f"kpi kpi-{n}")


def grafica(id_=None, figura=None):
    props = {"config": CONFIG}
    if id_:
        props["id"] = id_
    if figura is not None:
        props["figure"] = figura
    return dcc.Graph(**props)


def control(etiqueta, componente, clase=""):
    return html.Div([html.Div(etiqueta, className=f"etiqueta-control {clase}"), componente])


def radio(id_, opciones, valor):
    return dbc.RadioItems(id=id_, inline=True, value=valor,
                          options=[{"label": f" {l}", "value": v} for v, l in opciones])


def intro(*hijos):
    return html.Div(list(hijos), className="intro-seccion")


# =============================================================== Pestaña 1: contexto
GRADIENTE = {  # p5, p25, mediana, p75, p95 de la elevación por cobertura (m)
    4: (2051, 2143, 2232, 2304, 2375), 3: (2052, 2261, 2403, 2547, 2694), 6: (2066, 2319, 2428, 2545, 2715),
    5: (2588, 2732, 2796, 2858, 2929), 2: (2595, 2794, 2936, 3042, 3227), 1: (2838, 3034, 3146, 3236, 3362),
    7: (3218, 3300, 3363, 3409, 3520),
}


def fig_gradiente():
    fig = go.Figure()
    for c, (p5, p25, p50, p75, p95) in GRADIENTE.items():
        h = (f"<b>{LARGO[c]}</b><br>Mediana: {miles(p50)} m<br>50 % central: {miles(p25)}–{miles(p75)} m"
             f"<br>90 % central: {miles(p5)}–{miles(p95)} m<extra></extra>")
        y = [ETIQ[c]] * 2
        fig.add_scatter(x=[p5, p95], y=y, mode="lines", line=dict(color=COLOR[c], width=3), hovertemplate=h, showlegend=False)
        fig.add_scatter(x=[p25, p75], y=y, mode="lines", line=dict(color=COLOR[c], width=16), hovertemplate=h, showlegend=False)
        fig.add_scatter(x=[p50], y=[ETIQ[c]], mode="markers", hovertemplate=h, showlegend=False,
                        marker=dict(color="white", size=11, line=dict(color=COLOR[c], width=3)))
    for x0, x1, col, txt in [(1850, 2450, "rgba(224,165,38,0.18)", "Montano inferior"),
                             (2450, 2750, "rgba(76,154,42,0.16)", "Montano superior"),
                             (2750, 3250, "rgba(27,111,92,0.16)", "Subalpino"),
                             (3250, 3900, "rgba(142,94,162,0.18)", "Límite arbóreo")]:
        fig.add_vrect(x0=x0, x1=x1, fillcolor=col, line_width=0, layer="below")
        fig.add_annotation(x=(x0 + x1) / 2, y=1, yref="y domain", text=f"<b>{txt}</b>", showarrow=False,
                           yanchor="top", font=dict(color="#4f6159"))
    fig.update_layout(height=400, margin=dict(t=40), xaxis=dict(title="Elevación (m s. n. m.)", range=[1850, 3900]),
                      yaxis=dict(showgrid=False))
    return fig


COMPOSICION = {  # % de celdas de cada área por cobertura
    1: [0, 34.546, 62.224, 40.536], 2: [8.185, 49.373, 30.066, 56.058], 3: [58.034, 5.644, 0, 0],
    4: [7.431, 0, 0, 0], 5: [0, 2.254, 0, 1.450], 6: [26.350, 3.010, 0, 0], 7: [0, 5.172, 7.710, 1.956],
}


def fig_composicion():
    ys = ["Cache la Poudre", "Comanche Peak", "Neota", "Rawah"]
    fig = go.Figure()
    for c in CLASES:
        fig.add_bar(x=COMPOSICION[c], y=ys, orientation="h", name=ETIQ[c],
                    marker=dict(color=COLOR[c], line=dict(color="white", width=1.5)),
                    hovertemplate=f"<b>%{{y}}</b><br>{LARGO[c]}: %{{x:.1f}} %<extra></extra>")
    fig.update_layout(barmode="stack", height=330, margin=dict(t=20), xaxis=dict(title="% de las celdas del área", range=[0, 100]),
                      legend=dict(orientation="h", y=-0.28, x=0))
    return fig


AREAS_INFO = [
    ("🏞️ Rawah", "Exposición media", "Montes Medicine Bow: valles glaciares y más de 25 lagos. Matriz subalpina de pícea/abeto y lodgepole.",
     "260.796 celdas", "2.473–3.686 m", "Elevación mediana 3.002 m · carretera a 3.155 m", "#1e88e5"),
    ("🏔️ Neota", "Exposición baja", "Meseta subalpina junto al paso Cameron, casi toda sobre 2.950 m. La más alta y con más krummholz.",
     "29.884 celdas", "2.945–3.647 m", "Elevación mediana 3.240 m · carretera a 914 m", "#8e5ea2"),
    ("⛰️ Comanche Peak", "Exposición media", "Cordillera Mummy, contigua al Parque Nacional: del piso montano a la tundra alpina.",
     "253.364 celdas", "2.270–3.858 m", "Elevación mediana 2.997 m · carretera a 1.831 m", "#0f9d58"),
    ("💧 Cache la Poudre", "Exposición alta", "Cañón bajo del río: ponderosa, Douglas y la única ribera de álamo/sauce.",
     "36.968 celdas", "1.859–2.654 m", "Elevación mediana 2.313 m · carretera a 696 m", "#d9643a"),
]
ESPECIES = [
    (1, "Picea engelmannii · Abies lasiocarpa", "Subalpino", "Bosque de clímax fresco y húmedo, con nieve prolongada; especies tolerantes a la sombra."),
    (2, "Pinus contorta var. latifolia", "Montano superior y subalpino", "Pionera con conos serótinos que se abren con el fuego; forma rodales tras incendios."),
    (3, "Pinus ponderosa var. scopulorum", "Montano inferior", "Laderas secas y cálidas orientadas al sur; corteza gruesa resistente al fuego."),
    (4, "Populus angustifolia · Salix spp.", "Fondos de valle", "Bosque de galería ribereño ligado a un nivel freático somero."),
    (5, "Populus tremuloides", "Montano y subalpino", "Especie clonal que rebrota de raíz tras perturbaciones."),
    (6, "Pseudotsuga menziesii var. glauca", "Montano inferior y medio", "Prefiere laderas frescas orientadas al norte."),
    (7, "Picea, Abies y Pinus flexilis achaparrados", "Límite arbóreo", "Árboles deformados por el viento y el hielo en el borde superior del bosque."),
]


def pestana_contexto():
    areas = dbc.Row([
        dbc.Col(html.Div([
            html.H5(n), dbc.Badge(exp, color="light", text_color="dark", className="mb-2"),
            html.Div(desc, className="mb-2"), html.Div([html.B(celdas), f" · {rango}"]), html.Div(extra),
        ], className="area", style={"background": f"linear-gradient(135deg, {col}, {col}bb)"}), md=6, className="mb-3")
        for n, exp, desc, celdas, rango, extra, col in AREAS_INFO
    ])
    especies = dbc.Row([
        dbc.Col(html.Div([
            html.H6(f"{EMOJI[c]} {LARGO[c]}"), html.Div(cient, className="cientifico mb-1"),
            dbc.Badge(piso, className="mb-2", style={"backgroundColor": COLOR[c]}), html.Div(desc),
        ], className="especie", style={"borderTopColor": COLOR[c]}), xl=3, lg=4, md=6, className="mb-3")
        for c, cient, piso, desc in ESPECIES
    ])
    return html.Div([
        dbc.Row([
            dbc.Col(tarjeta("¿Qué problema resolvemos?", "mdi:target", "cab-lago", [
                html.P(["Predecir la ", html.B("cobertura forestal dominante"), " de cada celda del terreno a partir solo de su ",
                        html.B("cartografía"), ": elevación, orientación, pendiente, distancias al agua, a carreteras y a puntos "
                        "de incendio, área silvestre y tipo de suelo."]),
                html.P(["Los inventarios de campo son costosos en zonas remotas; un modelo cartográfico apoya la ",
                        html.B("planificación forestal, la evaluación del riesgo de incendios y la conservación"), "."]),
                html.P(["Primero se construyó un ", html.B("modelo base"), " (regresión logística) y luego se compararon ",
                        html.B("7 algoritmos × 4 estrategias de balanceo × 4 métodos de optimización"),
                        " para elegir el mejor modelo de forma estadísticamente defendible."]),
                html.Div([dbc.Badge("🎯 Clasificación multiclase", color="success", className="me-1 mb-1"),
                          dbc.Badge("⚖️ Desbalance 103 : 1", color="warning", className="me-1 mb-1"),
                          dbc.Badge("🤖 7 algoritmos · 108 combinaciones", color="info", className="me-1 mb-1"),
                          dbc.Badge("🏆 XGBoost: F1 macro 0,927", color="danger", className="me-1 mb-1")]),
            ]), lg=4, className="mb-3"),
            dbc.Col(tarjeta("Gradiente altitudinal: cada especie en su piso", "mdi:image-filter-hdr", "cab-verde", [
                grafica(figura=fig_gradiente()),
                nota("La temperatura baja ≈ 6 °C por cada 1.000 m de ascenso y cada cobertura ocupa la franja que tolera. "
                     "Las barras gruesas de clases vecinas se solapan: esas transiciones serán las zonas de duda de los modelos.",
                     "02_eda.html", "2.3"),
            ]), lg=8, className="mb-3"),
        ]),
        dbc.Row([
            dbc.Col(tarjeta("Composición de cada área silvestre", "mdi:map-marker-radius", "cab-azul", [
                grafica(figura=fig_composicion()),
                nota("Cada área ocupa un tramo distinto del gradiente. Cache la Poudre es otro mundo: sin pícea/abeto ni "
                     "krummholz, y es la única con bosque ribereño de álamo/sauce.", "02b_fuga_estructura.html", "2.7"),
            ]), lg=5, className="mb-3"),
            dbc.Col([html.H4("🏞️ Las cuatro áreas silvestres", className="seccion-titulo"), areas], lg=7),
        ]),
        html.H4("🌲 Las siete coberturas forestales", className="seccion-titulo mt-2"),
        especies,
        html.Div(dbc.Button([icono("mdi:book-open-page-variant"), "Leer el informe completo en Jupyter Book"],
                            href=LIBRO, target="_blank", className="boton-libro mt-2"), className="text-center"),
    ], className="contenido-tab")


# =============================================================== Pestaña 2: EDA
ETA2 = {"Aspect": 0.00453, "Hillshade_3pm": 0.01057, "Vertical_Distance_To_Hydrology": 0.01246,
        "Horizontal_Distance_To_Hydrology": 0.02366, "Hillshade_Noon": 0.02945, "Hillshade_9am": 0.03271,
        "Horizontal_Distance_To_Fire_Points": 0.06971, "Slope": 0.07457, "Horizontal_Distance_To_Roadways": 0.09604,
        "Elevation": 0.61645}
ETA_ETIQ = {"Aspect": "Orientación", "Hillshade_3pm": "Sombreado 3 p. m.", "Vertical_Distance_To_Hydrology": "Dist. vertical a agua",
            "Horizontal_Distance_To_Hydrology": "Dist. horizontal a agua", "Hillshade_Noon": "Sombreado mediodía",
            "Hillshade_9am": "Sombreado 9 a. m.", "Horizontal_Distance_To_Fire_Points": "Dist. a puntos de incendio",
            "Slope": "Pendiente", "Horizontal_Distance_To_Roadways": "Dist. a carreteras", "Elevation": "Elevación"}
NOTAS_DIST = {
    "Elevation": "La elevación separa las coberturas en tres bloques: montano inferior (ponderosa, Douglas, álamo/sauce), montano superior (lodgepole, álamo temblón) y subalpino (pícea/abeto, krummholz). Es el predictor dominante del conjunto.",
    "Aspect": "La orientación por sí sola apenas discrimina, pero separa al abeto Douglas, más frecuente en laderas frescas orientadas al norte, del pino ponderosa, propio de laderas cálidas.",
    "Slope": "Las coberturas del cañón del Poudre (ponderosa, Douglas, álamo/sauce) ocupan laderas más inclinadas, con suelos someros; las subalpinas se asientan sobre mesetas glaciares más suaves.",
    "Horizontal_Distance_To_Hydrology": "El álamo y el sauce son la única cobertura pegada al agua (mediana de 30 m): su nicho ribereño depende de un nivel freático somero.",
    "Vertical_Distance_To_Hydrology": "El bosque de galería se concentra en celdas casi al nivel del cauce (mediana de 6 m de desnivel). Fuera de esa franja, la variable apenas distingue coberturas.",
    "Horizontal_Distance_To_Roadways": "Las vías siguen los fondos de valle: las coberturas del piso bajo quedan más cerca de carreteras. Es un indicador regional de accesibilidad y presión antrópica.",
    "Hillshade_9am": "El abeto Douglas tiene la menor iluminación matinal: prefiere laderas en sombra, más frescas y húmedas.",
    "Hillshade_Noon": "El sombreado del mediodía depende sobre todo de la pendiente: las laderas abruptas reciben menos luz cenital.",
    "Hillshade_3pm": "El índice de la tarde refleja la orientación al oeste y es casi el espejo del de las 9 a. m. (r = −0,78): un bloque de iluminación redundante.",
    "Horizontal_Distance_To_Fire_Points": "Las coberturas montanas bajas están más cerca de puntos históricos de ignición, en coherencia con un régimen de incendios más frecuente en el piso bajo.",
}
CORR_ETIQ = ["Elevación", "Orientación", "Pendiente", "D. horiz. agua", "D. vert. agua", "D. carreteras",
             "Sombra 9 h", "Sombra 12 h", "Sombra 15 h", "D. incendios"]
CORR_INF = [
    [], [0.016], [-0.243, 0.078], [0.306, 0.017, -0.011], [0.093, 0.070, 0.274, 0.606],
    [0.366, 0.025, -0.216, 0.072, -0.046], [0.112, -0.579, -0.326, -0.027, -0.165, 0.035],
    [0.205, 0.336, -0.527, 0.047, -0.111, 0.190, 0.010], [0.059, 0.647, -0.177, 0.052, 0.034, 0.106, -0.780, 0.594],
    [0.147, -0.109, -0.186, 0.052, -0.071, 0.331, 0.133, 0.058, -0.048],
]
VIF = {"D. incendios": 1.164, "D. carreteras": 1.302, "Elevación": 1.337, "D. horiz. agua": 1.810, "D. vert. agua": 1.828,
       "Orientación": 1.862, "Pendiente": 6.844, "Sombra 12 h": 38.145, "Sombra 9 h": 104.824, "Sombra 15 h": 144.339}


def fig_eta2():
    orden = sorted(ETA2, key=ETA2.get)
    fig = go.Figure(go.Bar(
        x=[ETA2[v] for v in orden], y=[ETA_ETIQ[v] for v in orden], orientation="h",
        text=[fmt(ETA2[v]) for v in orden], textposition="outside",
        marker=dict(color=["#0f9d58" if v == "Elevation" else "#9fd8b8" for v in orden], line=dict(color="white", width=2)),
        hovertemplate="<b>%{y}</b><br>η² = %{x:.3f}<br>(%{x:.1%} de su varianza explicada por la cobertura)<extra></extra>"))
    fig.update_layout(height=420, title="🏔️ La elevación explica 6 veces más que la segunda variable",
                      xaxis=dict(range=[0, 0.72], title="η² (proporción de varianza explicada por la cobertura)"),
                      yaxis=dict(showgrid=False))
    return fig


def pestana_eda():
    return html.Div([
        dbc.Row([
            dbc.Col(tarjeta("Desbalance de clases", "mdi:scale-unbalanced", "cab-ocre", [
                radio("escala-desbalance", [("log", "Escala logarítmica"), ("lineal", "Escala lineal")], "log"),
                grafica("fig-desbalance"),
                nota("El lodgepole y la pícea/abeto forman la matriz subalpina (85 % de las celdas); el álamo/sauce es un "
                     "corredor ribereño estrecho. Los modelos tienden a favorecer las clases frecuentes, por eso se usa F1 macro, "
                     "validación estratificada y se probaron tres estrategias de balanceo (SMOTE, ADASYN y pesos de clase).",
                     "02_eda.html", "2.1"),
            ]), lg=6, className="mb-3"),
            dbc.Col(tarjeta("Poder discriminante de cada variable", "mdi:podium-gold", "cab-verde", [
                grafica(figura=fig_eta2()),
                nota("η² mide qué parte de la variabilidad de una variable se explica por la cobertura. La elevación (0,62) "
                     "domina; orientación, sombreado e hidrología solo separan pares concretos de especies.", "02_eda.html", "2.3"),
            ]), lg=6, className="mb-3"),
        ]),
        dbc.Row([
            dbc.Col(tarjeta("Distribución de las variables por cobertura", "mdi:chart-bell-curve", "cab-lavanda", [
                dbc.Row([
                    dbc.Col(control("🔎 Variable cartográfica", dcc.Dropdown(
                        id="variable-distribucion", clearable=False, value="Elevation",
                        options=[{"label": l, "value": v} for v, l in D.VARIABLES.items()])), md=5),
                    dbc.Col(control("🏞️ Áreas silvestres", dbc.Checklist(
                        id="areas-distribucion", inline=True, value=D.AREAS,
                        options=[{"label": f" {a}", "value": a} for a in D.AREAS])), md=7),
                ], className="mb-2"),
                grafica("fig-distribucion"),
                html.Div(id="nota-distribucion", className="nota"),
            ]), lg=6, className="mb-3"),
            dbc.Col(tarjeta("Correlación y multicolinealidad", "mdi:grid", "cab-azul", [
                radio("vista-correlacion", [("matriz", "Matriz de correlación"), ("vif", "VIF")], "matriz"),
                grafica("fig-correlacion"),
                nota("Los tres índices de sombreado se calculan con la orientación y la pendiente: son redundantes (VIF de 38 a "
                     "144). La elevación aporta información casi independiente (VIF 1,3).", "02_eda.html", "2.3"),
            ]), lg=6, className="mb-3"),
        ]),
        dbc.Row([
            dbc.Col(tarjeta("¿Generaliza el modelo a un área que nunca vio?", "mdi:map-search", "cab-terracota", [
                radio("metrica-areas-eda", [("accuracy", "Accuracy"), ("f1_macro_clases_presentes", "F1 macro (clases presentes)")], "accuracy"),
                grafica("fig-areas-eda"),
                nota("Se entrena con tres áreas y se evalúa en la cuarta. El desempeño cae de 0,72 (partición aleatoria) a "
                     "0,41–0,59 de accuracy: las celdas vecinas se parecen mucho entre sí (autocorrelación espacial) y la "
                     "partición aleatoria es optimista. Ni siquiera el finalista XGBoost escapa a este límite.",
                     "02b_fuga_estructura.html", "2.7"),
            ]), lg=12, className="mb-3"),
        ]),
    ], className="contenido-tab")


# =============================================================== Pestaña 3: modelos
FIN_F1 = D.FIN_MET.loc["XGBoost (finalista)", "F1 macro"]
FIN_ACC = D.FIN_MET.loc["XGBoost (finalista)", "Accuracy"]
LR_F1 = D.BASE["test"]["F1 macro"]
LR_ACC = D.BASE["test"]["Accuracy"]
N_COMB = int(D.TABLA["aplicable"].sum())


def sub_modelo_base():
    t = D.BASE["test"]
    mejor_dummy = max(v["F1 macro"] for v in D.BASE["dummies"].values())
    brecha = abs(D.BASE["train"]["F1 macro"] - t["F1 macro"])
    return html.Div([
        intro(html.B("Paso 1 · Modelo base. "), "Una regresión logística multinomial con ingeniería de variables, "
              "ajustada con validación cruzada estratificada. Sirve de referencia: cualquier modelo más complejo tiene que superarla."),
        dbc.Row([
            dbc.Col(kpi("🎯 Accuracy en prueba", fmt(t["Accuracy"]), f"vs. {fmt(D.BASE['dummies']['Dummy (más frecuente)']['Accuracy'])} del clasificador mayoritario", 1), lg=3, md=6, className="mb-3"),
            dbc.Col(kpi("⚖️ F1 macro en prueba", fmt(t["F1 macro"]), f"vs. {fmt(mejor_dummy)} del mejor dummy", 2), lg=3, md=6, className="mb-3"),
            dbc.Col(kpi("🚀 Ganancia en F1 macro", f"+{(t['F1 macro'] / mejor_dummy - 1) * 100:.0f} %", "sobre la inferencia ingenua", 3), lg=3, md=6, className="mb-3"),
            dbc.Col(kpi("🩺 Brecha entrenamiento–prueba", fmt(brecha, 4), "F1 macro: sin sobreajuste", 4), lg=3, md=6, className="mb-3"),
        ]),
        dbc.Row([
            dbc.Col(tarjeta("Desempeño frente a la línea base", "mdi:trophy", "cab-verde", [
                radio("vista-metricas", [("base", "🎯 Modelo vs. dummies"), ("ajuste", "🩺 Diagnóstico de ajuste")], "base"),
                grafica("fig-metricas"),
                nota("Predecir siempre lodgepole acierta el 49 % por puro desbalance, pero su F1 macro es 0,09. El modelo "
                     "multiplica el F1 macro, y entrenamiento y prueba casi coinciden: su límite es el sesgo de un modelo lineal, "
                     "no la falta de datos.", "03_modelo_base.html", "3.5"),
            ]), lg=6, className="mb-3"),
            dbc.Col(tarjeta("¿Qué pesa en cada cobertura? Coeficientes", "mdi:tune-variant", "cab-lavanda", [
                dbc.Row([
                    dbc.Col(control("🌲 Cobertura", dcc.Dropdown(id="clase-coef", clearable=False, value=7,
                                                                options=[{"label": f"{EMOJI[c]} {LARGO[c]}", "value": c} for c in CLASES])), md=6),
                    dbc.Col(control("🧩 Tipo de variable", dcc.Dropdown(id="grupo-coef", clearable=False, value="todas", options=[
                        {"label": "Todas", "value": "todas"}, {"label": "Continuas", "value": "Continua"},
                        {"label": "Áreas silvestres", "value": "Área silvestre"}, {"label": "Tipos de suelo", "value": "Tipo de suelo"}])), md=6),
                ]),
                control("🔢 Número de variables", dcc.Slider(id="n-coef", min=5, max=20, step=1, value=10,
                                                             marks={i: str(i) for i in (5, 10, 15, 20)}), "mt-2"),
                grafica("fig-coef"),
                html.Div(id="nota-coef", className="nota"),
            ]), lg=6, className="mb-3"),
        ]),
        dbc.Row([
            dbc.Col(tarjeta("Matriz de confusión", "mdi:grid-large", "cab-terracota", [
                radio("modo-confusion", [("real", "% de la clase real (recall)"), ("pred", "% de la predicción (precisión)"), ("conteo", "Conteos")], "real"),
                grafica("fig-confusion"),
                nota("Los errores no se dispersan: se concentran entre coberturas vecinas del gradiente. El álamo temblón casi "
                     "desaparece (más del 90 % → lodgepole) y el abeto Douglas se confunde con el ponderosa.", "03_modelo_base.html", "3.5"),
            ]), lg=6, className="mb-3"),
            dbc.Col(tarjeta("Los errores siguen el nicho compartido", "mdi:vector-intersection", "cab-lago", [
                grafica("fig-solapamiento", fig_solapamiento()),
                nota("Cada punto es un par de coberturas: cuanto más comparten su franja de elevación, más las confunde el "
                     "modelo. El tamaño indica cuántas celdas se confundieron.", "03_modelo_base.html", "3.7"),
            ]), lg=6, className="mb-3"),
        ]),
        tarjeta("Explorador de confusiones: la ecología detrás de cada error", "mdi:magnify", "cab-ocre",
                html.Div(id="explicacion-confusion", className="panel-explicacion"), "mb-3"),
    ])


def sub_benchmark():
    return html.Div([
        intro(html.B("Paso 2 · Benchmark. "), f"Se entrenaron 7 algoritmos con 4 estrategias de balanceo y 4 métodos de "
              f"optimización ({N_COMB} combinaciones aplicables) con validación cruzada anidada: 3 pliegues externos para "
              "medir el desempeño y 3 internos para elegir hiperparámetros. Así el F1 reportado nunca se usó para ajustar el modelo."),
        dbc.Row([
            dbc.Col(tarjeta("Mapa del benchmark: algoritmo × balanceo", "mdi:view-grid-plus", "cab-verde", [
                dbc.Row([
                    dbc.Col(control("🎛️ Método de optimización", dcc.Dropdown(id="opt-heatmap", clearable=False, value="mejor", options=[
                        {"label": "El mejor de los cuatro", "value": "mejor"}] + [{"label": l, "value": v} for v, l in D.OPTIMIZADORES.items()])), md=6),
                    dbc.Col(control("📏 Qué mostrar", dcc.Dropdown(id="metrica-heatmap", clearable=False, value="f1_macro_media", options=[
                        {"label": "F1 macro (media de 3 pliegues)", "value": "f1_macro_media"},
                        {"label": "Accuracy (media)", "value": "accuracy_media"},
                        {"label": "Tiempo total (minutos)", "value": "tiempo_min"}])), md=6),
                ], className="mb-2"),
                grafica("fig-heatmap"),
                nota("Haz clic en una celda para ver su detalle. XGBoost y Random Forest dominan; Naive Bayes queda último "
                     "porque supone variables independientes y gaussianas, algo que estos datos violan. KNN no admite pesos de clase (N/A).",
                     "06_benchmark_modelos.html", "5.4"),
            ]), lg=7, className="mb-3"),
            dbc.Col(tarjeta("Detalle de la combinación", "mdi:clipboard-text-search", "cab-lago", [
                html.Div(id="detalle-combinacion"),
            ]), lg=5, className="mb-3"),
        ]),
        dbc.Row([
            dbc.Col(tarjeta("¿Vale la pena el costo? Tiempo frente a desempeño", "mdi:timer-sand", "cab-azul", [
                dbc.Checklist(id="modelos-dispersion", inline=True, value=list(D.MODELOS),
                              options=[{"label": f" {n}", "value": k} for k, n in D.MODELOS.items()]),
                grafica("fig-dispersion"),
                nota("Cada punto es una combinación. Arriba a la izquierda está lo ideal (alto F1, poco tiempo). El tiempo crece "
                     "con el balanceo sintético (SMOTE/ADASYN multiplican las filas) y no siempre trae más F1.",
                     "06_benchmark_modelos.html", "5.4"),
            ]), lg=7, className="mb-3"),
            dbc.Col(tarjeta("¿Ayuda balancear las clases?", "mdi:scale-balance", "cab-ocre", [
                grafica("fig-balanceo"),
                nota("Diferencia de F1 macro de cada estrategia frente a no balancear, por algoritmo. En casi todos los casos el "
                     "balanceo no mejora el F1 macro: con 40.000 celdas, las clases minoritarias ya tienen suficientes ejemplos.",
                     "06_benchmark_modelos.html", "5.4"),
            ]), lg=5, className="mb-3"),
        ]),
    ])


def sub_optimizacion():
    ahorro = D.MULTI_RES["ahorro_relativo"] * 100
    return html.Div([
        intro(html.B("Paso 3 · Optimización de hiperparámetros. "), "Grid Search prueba todas las combinaciones; Random Search "
              "sortea; la optimización bayesiana (TPE) aprende de los intentos previos; el algoritmo genético cruza y muta las "
              "mejores configuraciones. ¿Cuál encuentra antes una buena solución?"),
        dbc.Row([
            dbc.Col(tarjeta("Experimento controlado: la carrera de los optimizadores", "mdi:run-fast", "cab-verde", [
                dbc.Row([
                    dbc.Col(control("🏁 Métodos", dbc.Checklist(id="metodos-anytime", inline=True,
                                                               value=list(D.COLOR_OPT_NOMBRE), options=[{"label": f" {m}", "value": m} for m in D.COLOR_OPT_NOMBRE])), md=8),
                    dbc.Col(control("⏱️ Eje horizontal", dbc.RadioItems(id="eje-anytime", inline=True, value="evaluacion", options=[
                        {"label": " Evaluaciones", "value": "evaluacion"}, {"label": " Segundos", "value": "tiempo_acumulado_s"}])), md=4),
                ], className="mb-2"),
                grafica("fig-anytime"),
                nota("Árbol de decisión, espacio de 5 hiperparámetros, 30 evaluaciones y 5 semillas. La línea es el mejor F1 "
                     "encontrado hasta ese momento (media de las semillas) y la banda, su rango. TPE llega más alto y antes; en el "
                     "benchmark, con rejillas pequeñas, Grid Search ya era casi exhaustivo y las diferencias desaparecían.",
                     "07_optimizacion.html", "6.4"),
            ]), lg=7, className="mb-3"),
            dbc.Col(tarjeta("Los cuatro métodos en el benchmark", "mdi:tune", "cab-azul", [
                radio("metrica-opt", [("f1_macro_media", "F1 macro"), ("tiempo_total_s", "Tiempo"), ("evaluaciones_totales", "Evaluaciones")], "f1_macro_media"),
                grafica("fig-optimizadores"),
                nota("Sobre las 108 combinaciones los cuatro métodos alcanzan F1 muy parecidos; lo que cambia es el costo. La "
                     "elección del algoritmo pesa mucho más que la del optimizador.", "07_optimizacion.html", "6.2"),
            ]), lg=5, className="mb-3"),
        ]),
        tarjeta("Successive Halving: descartar pronto a los candidatos malos", "mdi:filter-variant", "cab-lavanda", [
            dbc.Row([
                dbc.Col(grafica(figura=fig_halving()), lg=8),
                dbc.Col([
                    html.Div([html.Div("1", className="numero"), html.Div("Se evalúan 8 configuraciones de un bosque con poco presupuesto (20 árboles).")], className="paso"),
                    html.Div([html.Div("2", className="numero"), html.Div("Solo la mitad mejor pasa a la siguiente ronda, con el doble de árboles (η = 2).")], className="paso"),
                    html.Div([html.Div("3", className="numero"), html.Div("Se repite hasta quedar un ganador entrenado con 160 árboles.")], className="paso"),
                    html.Div(kpi("💰 Ahorro de cómputo", f"{ahorro:.0f} %", "frente a evaluar todo con el presupuesto completo", 5), className="mt-3"),
                ], lg=4),
            ]),
            nota("El ganador (profundidad 20, hoja mínima 1) es el mismo que habría encontrado la búsqueda completa, a una "
                 "fracción del costo.", "07_optimizacion.html", "6.6"),
        ], "mb-3"),
    ])


def sub_finalista():
    ic = D.FIN_IC.set_index(["modelo", "métrica"])
    f1_inf, f1_sup = ic.loc[("XGBoost (finalista)", "F1 macro"), ["IC95 inf", "IC95 sup"]]
    hp = D.RESUMEN["hiperparametros"]
    return html.Div([
        intro(html.B("Paso 4 · El finalista. "), f"La mejor combinación del benchmark, XGBoost sin balanceo "
              f"({hp['n_estimators']} árboles, profundidad {hp['max_depth']}, tasa de aprendizaje {fmt(hp['learning_rate'], 1)}), "
              "se reentrenó con las 464.809 celdas de entrenamiento y se evaluó una sola vez en la prueba reservada."),
        dbc.Row([
            dbc.Col(kpi("🏆 F1 macro del finalista", fmt(FIN_F1), f"IC 95 %: {fmt(f1_inf)}–{fmt(f1_sup)}", 1), lg=3, md=6, className="mb-3"),
            dbc.Col(kpi("📈 Frente a la regresión logística", f"+{fmt(FIN_F1 - LR_F1)}", f"F1 macro: {fmt(LR_F1)} → {fmt(FIN_F1)}", 2), lg=3, md=6, className="mb-3"),
            dbc.Col(kpi("🎯 Accuracy en prueba", fmt(FIN_ACC), f"vs. {fmt(LR_ACC)} de la referencia", 3), lg=3, md=6, className="mb-3"),
            dbc.Col(kpi("🧪 Calibración (Brier)", fmt(D.CALIB["brier_multiclase_finalista"]), f"vs. {fmt(D.CALIB['brier_multiclase_referencia'])}: probabilidades más fiables", 4), lg=3, md=6, className="mb-3"),
        ]),
        dbc.Row([
            dbc.Col(tarjeta("Finalista frente a referencia, clase por clase", "mdi:podium", "cab-verde", [
                radio("metrica-clase", [("F1", "F1"), ("Recall", "Recall"), ("Precisión", "Precisión")], "F1"),
                grafica("fig-por-clase"),
                nota("La mejora no está en las clases grandes sino en las difíciles: el álamo temblón pasa de un recall casi nulo "
                     "a más de 0,8, y el abeto Douglas y el krummholz dejan de confundirse con sus vecinos.", "06_benchmark_modelos.html", "5.6"),
            ]), lg=6, className="mb-3"),
            dbc.Col(tarjeta("Matriz de confusión comparada", "mdi:grid-large", "cab-terracota", [
                dbc.Row([
                    dbc.Col(radio("modelo-confusion", [("xgb", "XGBoost"), ("lr", "Regresión logística")], "xgb"), md=6),
                    dbc.Col(radio("modo-confusion-fin", [("real", "Recall"), ("conteo", "Conteos")], "real"), md=6),
                ]),
                grafica("fig-confusion-fin"),
                nota("Alterna entre los dos modelos: la diagonal del finalista es casi completa, mientras que la regresión "
                     "logística deja grandes bloques fuera de ella.", "06_benchmark_modelos.html", "5.6"),
            ]), lg=6, className="mb-3"),
        ]),
        dbc.Row([
            dbc.Col(tarjeta("¿Y en un área que el modelo nunca vio?", "mdi:map-search", "cab-ocre", [
                radio("metrica-areas", [("accuracy", "Accuracy"), ("f1_macro_clases_presentes", "F1 macro (clases presentes)")], "accuracy"),
                grafica("fig-areas"),
                nota("El hallazgo más importante de la revisión crítica: fuera de las áreas de entrenamiento el finalista no "
                     "supera a la regresión logística (accuracy media 0,52 frente a 0,56). Su ventaja depende de haber visto "
                     "celdas vecinas del mismo lugar; no es un modelo que se pueda trasladar a otro bosque sin reentrenarlo.",
                     "10_conclusiones_finales.html", "9.4"),
            ]), lg=6, className="mb-3"),
            dbc.Col(tarjeta("¿Es real la diferencia? Comparación estadística", "mdi:sigma", "cab-lavanda", [
                radio("vista-estadistica", [("cd", "Diagrama de diferencia crítica"), ("nemenyi", "Valores p de Nemenyi"), ("delong", "DeLong por clase")], "cd"),
                grafica("fig-estadistica"),
                html.Div(id="nota-estadistica", className="nota"),
            ]), lg=6, className="mb-3"),
        ]),
    ])


def sub_interpretabilidad():
    return html.Div([
        intro(html.B("Paso 5 · ¿Por qué decide así? "), "SHAP reparte cada predicción entre las variables: cuánto empujó cada "
              "una hacia (o en contra de) cada cobertura. Se calculó con TreeExplainer sobre 3.000 celdas de prueba."),
        dbc.Row([
            dbc.Col(tarjeta("Importancia global de las variables", "mdi:chart-bar-stacked", "cab-verde", [
                dbc.Row([
                    dbc.Col(control("🌲 Cobertura", dcc.Dropdown(id="clase-shap", clearable=False, value="todas", options=[
                        {"label": "Todas (apiladas)", "value": "todas"}] + [{"label": f"{EMOJI[c]} {LARGO[c]}", "value": c} for c in CLASES])), md=7),
                    dbc.Col(control("🔢 Variables", dcc.Slider(id="n-shap", min=5, max=20, step=5, value=12,
                                                              marks={i: str(i) for i in (5, 10, 15, 20)})), md=5),
                ], className="mb-2"),
                grafica("fig-shap-global"),
                nota("La elevación y la elevación relativa al agua dominan todas las clases. Las áreas silvestres (Rawah, Cache "
                     "la Poudre) actúan como atajos geográficos, y la distancia a carreteras resume la posición en el valle.",
                     "09_interpretabilidad.html", "8.1"),
            ]), lg=6, className="mb-3"),
            dbc.Col(tarjeta("Cómo responde el modelo a una variable", "mdi:chart-scatter-plot", "cab-azul", [
                dbc.Row([
                    dbc.Col(control("🔎 Variable", dcc.Dropdown(id="var-dependencia", clearable=False, value="Elevation", options=[
                        {"label": D.VARIABLES[v], "value": v} for v in D.VARIABLES if v != "Aspect"])), md=6),
                    dbc.Col(control("🌲 Cobertura", dcc.Dropdown(id="clase-dependencia", clearable=False, value=7, options=[
                        {"label": f"{EMOJI[c]} {LARGO[c]}", "value": c} for c in CLASES])), md=6),
                ], className="mb-2"),
                grafica("fig-dependencia"),
                html.Div(id="nota-dependencia", className="nota"),
            ]), lg=6, className="mb-3"),
        ]),
        dbc.Row([
            dbc.Col(tarjeta("Explica una celda", "mdi:map-marker-question", "cab-terracota", [
                dbc.Row([
                    dbc.Col(control("✅ Tipo de caso", dbc.RadioItems(id="tipo-celda", inline=True, value="error", options=[
                        {"label": " Errores", "value": "error"}, {"label": " Aciertos", "value": "acierto"}, {"label": " Todos", "value": "todos"}])), md=6),
                    dbc.Col(control("🌲 Cobertura real", dcc.Dropdown(id="clase-celda", clearable=False, value="todas", options=[
                        {"label": "Cualquiera", "value": "todas"}] + [{"label": ETIQ[c], "value": c} for c in CLASES])), md=6),
                ]),
                control("🎲 Elige una celda", dcc.Slider(id="indice-celda", min=0, max=10, step=1, value=0, marks=None,
                                                        tooltip={"placement": "bottom", "always_visible": False}), "mt-2"),
                html.Div(id="resumen-celda", className="mt-2"),
                grafica("fig-waterfall"),
                nota("Cada barra muestra cuánto empujó una variable la puntuación de la cobertura predicha (en log-odds). En los "
                     "errores, el modelo suele estar en una zona de transición: la elevación favorece a dos coberturas vecinas.",
                     "09_interpretabilidad.html", "8.2"),
            ]), lg=7, className="mb-3"),
            dbc.Col(tarjeta("SHAP frente a LIME", "mdi:compare-horizontal", "cab-lavanda", [
                html.Div(id="tabla-lime"),
                nota("LIME aproxima el modelo con una recta local y, en estos datos, se deja llevar por los tipos de suelo raros: "
                     "su ajuste local es pobre (R² ≈ 0,1). SHAP es exacto para árboles y más estable, por eso es la explicación de referencia.",
                     "09_interpretabilidad.html", "8.3"),
            ]), lg=5, className="mb-3"),
        ]),
    ])


def sub_eficiencia():
    p = D.PERFIL.set_index("versión")
    return html.Div([
        intro(html.B("Paso 6 · Costo computacional. "), "Un buen modelo también tiene que ser entrenable y usable. Aquí se "
              "compara cómo crece el tiempo con el tamaño de los datos y qué ganan las implementaciones optimizadas."),
        dbc.Row([
            dbc.Col(tarjeta("¿Cómo crece el tiempo con los datos?", "mdi:chart-timeline-variant", "cab-verde", [
                dbc.Checklist(id="modelos-escala", inline=True, value=list(D.ESC["modelo"].unique()),
                              options=[{"label": f" {m}", "value": m} for m in D.ESC["modelo"].unique()]),
                grafica("fig-escala"),
                nota("En escala log-log una recta de pendiente b significa tiempo ∝ nᵇ. La SVM con núcleo RBF crece casi "
                     "cuadráticamente (b ≈ 1,9): por eso se entrenó con una submuestra de 9.000 celdas. XGBoost hist escala mejor que lineal.",
                     "10_conclusiones_finales.html", "9.1"),
            ]), lg=7, className="mb-3"),
            dbc.Col(tarjeta("Implementación estándar frente a optimizada", "mdi:rocket-launch", "cab-azul", [
                control("🧩 Algoritmo", dcc.Dropdown(id="algoritmo-comp", clearable=False, value="XGBoost (200 árboles)",
                                                    options=[{"label": m, "value": m} for m in D.COMP["modelo"].unique()])),
                grafica("fig-comp"),
                html.Div(id="nota-comp", className="nota"),
            ]), lg=5, className="mb-3"),
        ]),
        tarjeta("El costo de afinar el finalista", "mdi:cash-clock", "cab-ocre", dbc.Row([
            dbc.Col(kpi("⏱️ Entrenamiento", f"{p.loc['optimizado (finalista)', 'tiempo_entrenamiento_s'] / 60:.0f} min",
                        f"vs. {p.loc['estándar (sin ajustar)', 'tiempo_entrenamiento_s'] / 60:.0f} min sin ajustar", 2), md=3, className="mb-2"),
            dbc.Col(kpi("📈 F1 macro", fmt(p.loc["optimizado (finalista)", "F1_macro_prueba"]),
                        f"vs. {fmt(p.loc['estándar (sin ajustar)', 'F1_macro_prueba'])} sin ajustar", 1), md=3, className="mb-2"),
            dbc.Col(kpi("💾 Memoria pico", f"{p.loc['optimizado (finalista)', 'memoria_pico_entrenamiento_MB']:.0f} MB",
                        "igual en ambas versiones", 5), md=3, className="mb-2"),
            dbc.Col(kpi("🎲 Estabilidad", f"± {fmt(D.SEMILLAS['F1_macro'].std(), 4)}",
                        "DE del F1 macro entre 5 semillas", 3), md=3, className="mb-2"),
        ]), "mb-3"),
    ])


def pestana_modelos():
    return html.Div([
        dbc.Row([
            dbc.Col(kpi("🏆 Modelo finalista", "XGBoost", "sin balanceo · Grid y Random Search", 1), lg=3, md=6, className="mb-3"),
            dbc.Col(kpi("⚖️ F1 macro en prueba", fmt(FIN_F1), f"vs. {fmt(LR_F1)} de la regresión logística", 2), lg=3, md=6, className="mb-3"),
            dbc.Col(kpi("🧪 Combinaciones evaluadas", str(N_COMB), "7 algoritmos × 4 balanceos × 4 optimizadores", 3), lg=3, md=6, className="mb-3"),
            dbc.Col(kpi("🗺️ En áreas no vistas", fmt(D.AREAS_NV[D.AREAS_NV['modelo'].str.startswith('XGB')]['accuracy'].mean(), 2),
                        "accuracy media: el gran límite pendiente", 4), lg=3, md=6, className="mb-3"),
        ]),
        dbc.Tabs([
            dbc.Tab(sub_modelo_base(), label="📏 1 · Modelo base", tab_id="base"),
            dbc.Tab(sub_benchmark(), label="🏁 2 · Benchmark de 7 modelos", tab_id="benchmark"),
            dbc.Tab(sub_optimizacion(), label="🎛️ 3 · Optimización", tab_id="optimizacion"),
            dbc.Tab(sub_finalista(), label="🏆 4 · Finalista y estadística", tab_id="finalista"),
            dbc.Tab(sub_interpretabilidad(), label="🔍 5 · Interpretabilidad", tab_id="interpretabilidad"),
            dbc.Tab(sub_eficiencia(), label="⚡ 6 · Eficiencia", tab_id="eficiencia"),
        ], id="subpestanas", active_tab="base", className="subpestanas nav-pills"),
    ], className="contenido-tab")


# =============================================================== figuras fijas auxiliares
ESPECIALES = {(1, 2), (1, 7), (2, 5), (2, 6), (3, 4), (3, 6)}


def _tasas(cm):
    return cm / cm.sum(axis=1, keepdims=True)


def fig_solapamiento():
    r = _tasas(D.CM_LR)
    xs, ys, cd, col, txt, tam, pos = [], [], [], [], [], [], []
    maxc = max(D.CM_LR[a - 1, b - 1] + D.CM_LR[b - 1, a - 1] for a, b in D.SOLAPE)
    for (a, b), s in D.SOLAPE.items():
        y = r[a - 1, b - 1] + r[b - 1, a - 1]
        n = int(D.CM_LR[a - 1, b - 1] + D.CM_LR[b - 1, a - 1])
        par = f"{CORTO[a]} ↔ {CORTO[b]}"
        xs.append(s), ys.append(y), cd.append([a, b, n, par])
        destacado = y > 0.2
        col.append("#d9643a" if destacado else "#26a6e8")
        txt.append(par if destacado else "")
        tam.append(10 + 30 * np.sqrt(n / maxc))
        pos.append("top center" if (a, b) == (1, 2) else "middle left" if (a, b) == (1, 7) else "middle right")
    rcorr = np.corrcoef(xs, ys)[0, 1]
    fig = go.Figure(go.Scatter(
        x=xs, y=ys, mode="markers+text", text=txt, textposition=pos, textfont=dict(size=10), customdata=cd,
        marker=dict(size=tam, color=col, opacity=0.85, line=dict(color="white", width=2)),
        hovertemplate="<b>%{customdata[3]}</b><br>Solapamiento altitudinal: %{x:.2f}<br>Confusión bidireccional: %{y:.2f}"
                      "<br>Celdas confundidas: %{customdata[2]:,}<extra></extra>"))
    fig.update_layout(height=470, title=f"r = {fmt(rcorr, 2)} entre nicho compartido y confusión · clic en un punto 👆",
                      xaxis=dict(title="Solapamiento de elevación (0 = nada, 1 = idéntico)", range=[-0.32, 1.42],
                                 tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1]),
                      yaxis=dict(title="Confusión bidireccional (a→b + b→a)"))
    return fig


def fig_halving():
    fig = go.Figure()
    m = D.MULTI.copy()
    for cand, g in m.groupby("candidato"):
        conf = g["config"].iloc[0].replace("'", "").replace("max_depth", "prof.").replace("min_samples_leaf", "hoja")
        ganador = len(g) == m.groupby("candidato").size().max()
        fig.add_scatter(x=g["n_estimators"], y=g["f1_macro"], mode="lines+markers", name=conf.strip("{}"),
                        line=dict(width=4 if ganador else 1.5, color="#0f9d58" if ganador else "#b0bec5"),
                        marker=dict(size=10 if ganador else 7),
                        hovertemplate=f"<b>{conf}</b><br>%{{x}} árboles<br>F1 macro: %{{y:.3f}}<extra></extra>")
    fig.update_layout(height=380, title="Cada ronda conserva la mitad mejor y duplica el presupuesto",
                      xaxis=dict(title="Presupuesto (número de árboles, escala log)", type="log", tickvals=[20, 40, 80, 160]),
                      yaxis=dict(title="F1 macro (validación)"), legend=dict(font=dict(size=10)))
    return fig


# =============================================================== layout general
app.layout = html.Div([
    html.Div(dbc.Container(dbc.Row([
        dbc.Col([
            html.H1("🌲 Clasificación de Cobertura Forestal - Roosevelt National Forest"),
            html.Div("Montañas Rocosas del norte de Colorado · Curso Machine Learning · Tercer entregable", className="subtitulo"),
            html.Div([dbc.Badge("👩‍🔬 Ana Galván", color="light", text_color="success"),
                      dbc.Badge("👩‍🔬 Valeria Oñate", color="light", text_color="primary"),
                      dbc.Badge("👩‍🔬 María José Ruiz", color="light", text_color="danger")], className="mt-2"),
        ], lg=9),
        dbc.Col(dbc.Button([icono("mdi:book-open-variant", 20), "Jupyter Book"], href=LIBRO, target="_blank",
                           className="boton-libro"), lg=3, className="d-flex align-items-center justify-content-lg-end mt-3 mt-lg-0"),
    ]), fluid="xl"), className="hero mb-4"),
    dbc.Container([
        dcc.Location(id="url"),
        dbc.Row([
            dbc.Col(kpi("🗺️ Celdas de 30 × 30 m", "581.012", "sin valores faltantes", 1), xs=6, md=True, className="mb-3"),
            dbc.Col(kpi("📐 Predictoras", "54", "10 continuas + 44 indicadoras", 2), xs=6, md=True, className="mb-3"),
            dbc.Col(kpi("🌲 Coberturas", "7", "clases a predecir", 3), xs=6, md=True, className="mb-3"),
            dbc.Col(kpi("🏞️ Áreas silvestres", "4", "Roosevelt National Forest", 5), xs=6, md=True, className="mb-3"),
            dbc.Col(kpi("🏔️ Gradiente altitudinal", "≈ 2.000 m", "de 1.859 a 3.858 m s. n. m.", 4), xs=12, md=True, className="mb-3"),
        ], className="g-3"),
        html.Img(src="/assets/banner_montana.svg", className="banner mb-4", alt="Pisos altitudinales de las Montañas Rocosas"),
        dbc.Tabs([
            dbc.Tab(pestana_contexto(), label="🌲 Contexto y Territorio", tab_id="contexto"),
            dbc.Tab(pestana_eda(), label="📊 Análisis Exploratorio", tab_id="eda"),
            dbc.Tab(pestana_modelos(), label="🤖 Modelos de Machine Learning", tab_id="modelo"),
        ], id="pestanas", active_tab="contexto"),
        html.Div(["Datos: Covertype, UCI Machine Learning Repository (Blackard y Dean, 1998; CC BY 4.0) · ",
                  html.A("Informe técnico en Jupyter Book", href=LIBRO, target="_blank")], className="pie"),
    ], fluid="xl"),
])


# =============================================================== callbacks: navegación
@app.callback(Output("pestanas", "active_tab"), Input("url", "search"))
def pestana_desde_url(busqueda):
    if busqueda and "tab=" in busqueda:
        valor = busqueda.split("tab=")[1].split("&")[0]
        if valor in ("contexto", "eda", "modelo"):
            return valor
    return "contexto"


# =============================================================== callbacks: EDA
@app.callback(Output("fig-desbalance", "figure"), Input("escala-desbalance", "value"))
def cb_desbalance(escala):
    conteo = pd.Series(D.CONTEO_TRAIN).sort_values()
    total = conteo.sum()
    fig = go.Figure(go.Bar(
        x=conteo.values, y=[ETIQ[c] for c in conteo.index], orientation="h",
        customdata=[[100 * v / total] for v in conteo.values],
        text=[f"{miles(v)} ({fmt(100 * v / total, 2)} %)" for v in conteo.values], textposition="outside",
        marker=dict(color=[COLOR[c] for c in conteo.index], line=dict(color="white", width=2)),
        hovertemplate="<b>%{y}</b><br>%{x:,} celdas<br>%{customdata[0]:.2f} % del entrenamiento<extra></extra>"))
    razon = conteo.max() / conteo.min()
    eje = dict(title="Celdas de entrenamiento", type="log", range=[3, 6.6]) if escala == "log" else \
        dict(title="Celdas de entrenamiento", type="linear", range=[0, conteo.max() * 1.35])
    fig.update_layout(height=380, title=f"Razón de desbalance {razon:.0f} : 1", xaxis=eje, yaxis=dict(showgrid=False))
    return fig


@app.callback(Output("fig-correlacion", "figure"), Input("vista-correlacion", "value"))
def cb_correlacion(vista):
    if vista == "vif":
        orden = sorted(VIF, key=VIF.get)
        col = ["#0f9d58" if VIF[v] < 5 else "#f2b134" if VIF[v] < 10 else "#d9643a" for v in orden]
        fig = go.Figure(go.Bar(x=[VIF[v] for v in orden], y=orden, orientation="h", text=[fmt(VIF[v], 1) for v in orden],
                               textposition="outside", marker=dict(color=col, line=dict(color="white", width=2)),
                               hovertemplate="<b>%{y}</b><br>VIF = %{x:.1f}<extra></extra>"))
        fig.add_vline(x=5, line_dash="dash", line_color="#f2b134", annotation_text="VIF 5", annotation_position="top right")
        fig.add_vline(x=10, line_dash="dash", line_color="#d9643a", annotation_text="VIF 10", annotation_position="top right")
        fig.update_layout(height=430, title="🟢 independiente · 🟡 moderado · 🔴 redundante",
                          xaxis=dict(type="log", title="Factor de inflación de la varianza (escala log)"), yaxis=dict(showgrid=False))
        return fig
    n = len(CORR_ETIQ)
    z = [[1.0 if j == i else CORR_INF[i][j] if j < i else None for j in range(n)] for i in range(n)]
    texto = [[f"{z[i][j]:.2f}" if j <= i else "" for j in range(n)] for i in range(n)]
    fig = go.Figure(go.Heatmap(
        z=z, x=CORR_ETIQ, y=CORR_ETIQ, zmin=-1, zmax=1, text=texto, texttemplate="%{text}", textfont=dict(size=10),
        xgap=2, ygap=2, colorbar=dict(title="r"),
        colorscale=[[0, "#b5432a"], [0.25, "#f08a5d"], [0.5, "#fbf7ef"], [0.75, "#42a5f5"], [1, "#0d47a1"]],
        hovertemplate="<b>%{y}</b> vs <b>%{x}</b><br>r = %{z:.2f}<extra></extra>"))
    fig.update_layout(height=470, title="Correlación de Pearson (triángulo inferior)",
                      yaxis=dict(autorange="reversed", showgrid=False), xaxis=dict(tickangle=35, showgrid=False))
    return fig


@app.callback(Output("fig-distribucion", "figure"), Output("nota-distribucion", "children"),
              Input("variable-distribucion", "value"), Input("areas-distribucion", "value"))
def cb_distribucion(variable, areas):
    datos = D.EDA[D.EDA["Area"].isin(areas or [])]
    etiqueta = D.VARIABLES[variable]
    if datos.empty:
        return vacio("Selecciona al menos un área silvestre", 440), ""
    orden = datos.groupby("Clase")[variable].median().sort_values().index
    fig = go.Figure()
    for c in orden:
        v = datos.loc[datos["Clase"] == c, variable]
        fig.add_violin(y=v, name=ETIQ[c], fillcolor=COLOR[c], line=dict(color=COLOR[c], width=1.5), opacity=0.78,
                       box=dict(visible=True, width=0.22, fillcolor="white", line=dict(color="#333", width=1)),
                       meanline=dict(visible=False), points=False, showlegend=False, spanmode="hard",
                       scalemode="width", width=0.6, hoveron="violins+kde")
    rango = [D.EDA[variable].min(), D.EDA[variable].max()]
    pad = (rango[1] - rango[0]) * 0.1
    fig.update_layout(height=440, violingap=0.25, title=f"{etiqueta} por cobertura · {miles(len(datos))} celdas de la muestra estratificada",
                      xaxis=dict(showgrid=False), yaxis=dict(title=etiqueta, range=[rango[0] - pad / 2, rango[1] + pad]))
    texto = [html.B("💡 Interpretación: "), NOTAS_DIST[variable], f" (η² = {fmt(ETA2[variable])}). ",
             html.A("Profundiza en la sección 2.2 del Jupyter Book →", href=LIBRO + "02_eda.html", target="_blank")]
    return fig, texto


def fig_areas_no_vistas(metrica, solo_lr=False):
    df = D.AREAS_NV.copy()
    fig = go.Figure()
    for modelo, color, nombre in [("Regresión logística", "#d9643a", "Regresión logística"),
                                  ("XGBoost (finalista)", "#0f9d58", "XGBoost (finalista)")]:
        if solo_lr and modelo != "Regresión logística":
            continue
        g = df[df["modelo"] == modelo]
        fig.add_bar(x=g["área_no_vista"], y=g[metrica], name=nombre, marker_color=color,
                    text=[fmt(v) for v in g[metrica]], textposition="outside",
                    customdata=g[["celdas"]].to_numpy(),
                    hovertemplate=f"<b>{nombre}</b><br>Área no vista: %{{x}}<br>%{{y:.3f}}<br>%{{customdata[0]:,}} celdas de prueba<extra></extra>")
    referencia = LR_ACC if metrica == "accuracy" else LR_F1
    fig.add_hline(y=referencia, line_dash="dash", line_color="#4f6159",
                  annotation_text=f"Regresión logística con partición aleatoria ({fmt(referencia)})", annotation_position="top left")
    fig.update_layout(barmode="group", height=400, yaxis=dict(range=[0, 1], title="Accuracy" if metrica == "accuracy" else "F1 macro"),
                      xaxis=dict(title="Área silvestre dejada fuera del entrenamiento", showgrid=False),
                      legend=dict(orientation="h", y=-0.22, x=0), title="Entrenar con 3 áreas, evaluar en la cuarta")
    return fig


@app.callback(Output("fig-areas-eda", "figure"), Input("metrica-areas-eda", "value"))
def cb_areas_eda(metrica):
    return fig_areas_no_vistas(metrica, solo_lr=False)


# =============================================================== callbacks: modelo base
@app.callback(Output("fig-metricas", "figure"), Input("vista-metricas", "value"))
def cb_metricas(vista):
    met = ["Accuracy", "Precisión macro", "Recall macro", "F1 macro"]
    fig = go.Figure()
    if vista == "base":
        for (nombre, valores), color in zip(D.BASE["dummies"].items(), ["#ffcc80", "#ffab91", "#ce93d8"]):
            fig.add_bar(x=met, y=[valores[m] for m in met], name=nombre, marker_color=color,
                        hovertemplate=f"<b>{nombre}</b><br>%{{x}}: %{{y:.3f}}<extra></extra>")
        t, ic = D.BASE["test"], D.BASE["ic95"]
        fig.add_bar(x=met, y=[t[m] for m in met], name="Regresión logística", marker_color="#0f9d58",
                    text=[fmt(t[m]) for m in met], textposition="outside",
                    error_y=dict(type="data", array=[ic[m][1] - t[m] for m in met], arrayminus=[t[m] - ic[m][0] for m in met],
                                 color="#0b4f34", thickness=2, width=6),
                    hovertemplate="<b>Regresión logística</b><br>%{x}: %{y:.3f}<extra></extra>")
        titulo = f"🎯 Regresión logística frente a la inferencia ingenua (prueba, {miles(D.BASE['n_test'])} celdas)"
    else:
        for parte, nombre, color in [("train", "Entrenamiento", "#26a6e8"), ("test", "Prueba", "#0f9d58")]:
            v = D.BASE[parte]
            fig.add_bar(x=met, y=[v[m] for m in met], name=nombre, marker_color=color, text=[fmt(v[m]) for m in met],
                        textposition="outside", hovertemplate=f"<b>{nombre}</b><br>%{{x}}: %{{y:.4f}}<extra></extra>")
        titulo = "Entrenamiento vs. prueba: brecha < 0,01 en todas las métricas"
    fig.update_layout(barmode="group", bargap=0.25, height=420, title=titulo, yaxis=dict(range=[0, 0.88], title="Valor de la métrica"),
                      xaxis=dict(showgrid=False), legend=dict(orientation="h", y=-0.15, x=0))
    return fig


NOTAS_COEF = {
    1: "Cada 100 m de ascenso multiplican sus odds por ≈ {or_}. Rawah y los suelos subalpinos la favorecen; Cache la Poudre y los suelos rocosos del cañón la excluyen.",
    2: "Efecto altitudinal moderado (≈ ×{or_} por cada 100 m): ocupa el centro del gradiente. Sus coeficientes más fuertes son edáficos.",
    3: "La altitud la penaliza (≈ ×{or_} por cada 100 m). Los suelos 1 a 4, complejos de afloramiento rocoso del cañón, son su firma edáfica; Rawah la excluye.",
    4: "Cache la Poudre ({cp}) actúa como atajo geográfico: es la única área con bosque ribereño. Cada 100 m de ascenso reducen sus odds a ≈ {or_}, y la cercanía al agua la favorece.",
    5: "Sin variables de perturbación (incendios, edad del rodal), ninguna predictora le da suficiente evidencia: su recall es apenas {rec}.",
    6: "Los índices de sombreado tienen signos opuestos por colinealidad: solo su efecto conjunto tiene lectura física, a favor de laderas poco expuestas.",
    7: "El efecto altitudinal más fuerte del modelo: +100 m multiplican sus odds por ≈ {or_}. Los suelos pedregosos de alta montaña completan su firma.",
}


@app.callback(Output("fig-coef", "figure"), Output("nota-coef", "children"),
              Input("clase-coef", "value"), Input("grupo-coef", "value"), Input("n-coef", "value"))
def cb_coef(clase, grupo, n):
    coef = pd.Series(D.BASE["coeficientes"][str(clase)])
    df = pd.DataFrame({"var": coef.index, "coef": coef.values})
    df["grupo"] = df["var"].map(D.grupo_variable)
    df["nombre"] = df["var"].map(D.NOMBRE_ING)
    if grupo != "todas":
        df = df[df["grupo"] == grupo]
    df = df.reindex(df["coef"].abs().sort_values(ascending=False).index).head(n).sort_values("coef")
    fig = go.Figure(go.Bar(
        x=df["coef"], y=df["nombre"], orientation="h", customdata=np.c_[np.exp(df["coef"]), df["grupo"]],
        marker=dict(color=["#0f9d58" if v > 0 else "#d9643a" for v in df["coef"]]),
        hovertemplate="<b>%{y}</b> (%{customdata[1]})<br>Coeficiente: %{x:+.2f}<br>Razón de odds: ×%{customdata[0]:.2f}<extra></extra>"))
    fig.update_layout(height=max(360, 26 * len(df) + 120), title=f"{EMOJI[clase]} {LARGO[clase]}: 🟢 aumenta · 🟠 reduce la probabilidad",
                      xaxis=dict(title="Coeficiente (log-odds; continuas por desviación estándar)"), yaxis=dict(showgrid=False))
    or_ = D.BASE["or_100m"][str(clase)]
    texto = NOTAS_COEF[clase].format(or_=fmt(or_, 2), cp=f"{coef['Wilderness_Area_4']:+.2f}".replace(".", ","),
                                     rec=fmt(D.PC_LR.loc[5, "Recall"], 2))
    hijos = [html.B("💡 Interpretación: "), texto, " Razón de odds por +100 m de elevación (efecto conjunto de la elevación y "
             "la elevación relativa al agua): ", html.B(f"×{fmt(or_, 2)}"), ". ",
             html.A("Profundiza en la sección 3.10 del Jupyter Book →", href=LIBRO + "03_modelo_base.html", target="_blank")]
    return fig, hijos


def fig_confusion(cm, modo, titulo_extra=""):
    etiquetas = [CORTO[c] for c in CLASES]
    if modo == "conteo":
        z = np.log10(cm + 1)
        texto = [[miles(v) for v in fila] for fila in cm]
        custom, hover, escala, titulo = cm, "%{customdata:,} celdas", dict(title="celdas"), "Conteos absolutos"
        mostrar = False
    else:
        z = cm / cm.sum(axis=1, keepdims=True) if modo == "real" else cm / np.maximum(cm.sum(axis=0, keepdims=True), 1)
        texto = [[f"{v:.2f}" for v in fila] for fila in z]
        custom, hover, escala, mostrar = z, "%{customdata:.1%}", dict(title="proporción"), True
        titulo = "Normalizada por fila (diagonal = recall)" if modo == "real" else "Normalizada por columna (diagonal = precisión)"
    fig = go.Figure(go.Heatmap(
        z=z, x=etiquetas, y=etiquetas, text=texto, texttemplate="%{text}", textfont=dict(size=12), customdata=custom,
        xgap=3, ygap=3, zmin=0, zmax=1 if modo != "conteo" else None, showscale=mostrar, colorbar=escala,
        colorscale=[[0, "#f1fbf3"], [0.15, "#b9e8c6"], [0.4, "#4fc38a"], [0.7, "#0f9d58"], [1, "#0b4f34"]],
        hovertemplate="Real: <b>%{y}</b><br>Predicha: <b>%{x}</b><br>" + hover + "<extra></extra>"))
    fig.update_layout(height=470, title=titulo + titulo_extra, yaxis=dict(title="Cobertura real", autorange="reversed", showgrid=False),
                      xaxis=dict(title="Cobertura predicha", tickangle=30, showgrid=False))
    return fig


@app.callback(Output("fig-confusion", "figure"), Input("modo-confusion", "value"))
def cb_confusion(modo):
    return fig_confusion(D.CM_LR, modo, " · haz clic en una celda 👆")


EXPLICACIONES = {
    (1, 2): ("🔥 Transición sucesional", "El pino lodgepole coloniza los sitios tras incendios de reemplazo y, con los siglos, la pícea y el abeto lo sustituyen bajo su dosel. Entre 2.800 y 3.300 m el mismo terreno puede sostener cualquiera de las dos: decide el tiempo desde el último incendio, que no está en los datos.{extra}"),
    (1, 7): ("🏔️ Ecotono del límite arbóreo", "El krummholz es la forma achaparrada de las mismas especies del bosque subalpino, moldeada por el viento y el hielo. Lo determinan la exposición y la nieve a escalas menores que la celda de 30 m, y es 10 veces menos frecuente: la duda se resuelve a favor de la pícea/abeto."),
    (2, 5): ("🍂 Cobertura definida por la perturbación", "El álamo temblón es clonal y rebrota tras incendios: su presencia depende de la historia del sitio, no de la topografía. Su nicho altitudinal está contenido en el del lodgepole, 30 veces más frecuente, y el modelo casi nunca lo elige (recall {rec5})."),
    (2, 6): ("📏 Vecinos en el gradiente", "El abeto Douglas ocupa el borde inferior del nicho del lodgepole; en las laderas frescas del montano medio ambos comparten elevación y suelos."),
    (3, 4): ("💧 Nicho ribereño no monótono", "El álamo/sauce se concentra en celdas casi al nivel del cauce, y por encima y por debajo desaparece: un pico que una recta no representa. Además, el corredor ribereño es compartido: incluso junto al agua el pino ponderosa ocupa buena parte de las celdas."),
    (3, 6): ("🧭 Partición por orientación", "Es el par con mayor solapamiento altitudinal. El abeto Douglas ocupa laderas frescas orientadas al norte y el ponderosa, laderas cálidas. El efecto de la orientación depende de la pendiente (interacción no lineal) y está repartido entre índices de sombreado colineales."),
    (4, 6): ("💧 Corredor ribereño compartido", "El álamo/sauce comparte con el abeto Douglas la elevación, el área (Cache la Poudre) y buena parte de los suelos; la capa hidrológica no registra el nivel freático ni las crecidas que delimitan el bosque de galería."),
}


def explicar_par(a, b):
    if a == b:
        pc = D.PC_LR.loc[a]
        return [html.H6(f"{EMOJI[a]} {LARGO[a]}: celda diagonal (aciertos)"),
                html.P(f"Recall = {fmt(pc['Recall'])} · precisión = {fmt(pc['Precisión'])}. En el finalista XGBoost: "
                       f"recall = {fmt(D.PC_XGB.loc[a, 'Recall'])} · precisión = {fmt(D.PC_XGB.loc[a, 'Precisión'])}."),
                html.Small("Haz clic fuera de la diagonal para entender por qué el modelo confunde dos coberturas.", className="text-muted")]
    clave = tuple(sorted((a, b)))
    r = _tasas(D.CM_LR)
    rx = _tasas(D.CM_XGB)
    n = int(D.CM_LR[a - 1, b - 1] + D.CM_LR[b - 1, a - 1])
    if clave in EXPLICACIONES:
        titulo, texto = EXPLICACIONES[clave]
    else:
        titulo, texto = "📏 Vecinos en el gradiente", ("Estas coberturas comparten parte de su franja altitudinal; cuanto mayor es "
                                                     "el solapamiento, más se confunden. Los pares con solapamiento inferior a 0,2 apenas registran errores.")
    med = D.BASE["elev_mediana_error"].get("1-2")
    extra = f" Las celdas de pícea/abeto que el modelo llama lodgepole están a una mediana de {miles(med)} m." if med else ""
    texto = texto.format(extra=extra, rec5=fmt(D.PC_LR.loc[5, "Recall"], 2))
    return [html.H6(f"{titulo}: {CORTO[a]} ↔ {CORTO[b]}"), html.P(texto),
            html.Small(f"Solapamiento altitudinal = {fmt(D.SOLAPE[clave], 2)} · {CORTO[a]} → {CORTO[b]}: {fmt(100 * r[a - 1, b - 1], 1)} % · "
                       f"{CORTO[b]} → {CORTO[a]}: {fmt(100 * r[b - 1, a - 1], 1)} % · {miles(n)} celdas confundidas en total. "
                       f"Con XGBoost: {fmt(100 * rx[a - 1, b - 1], 1)} % y {fmt(100 * rx[b - 1, a - 1], 1)} %.", className="text-muted")]


@app.callback(Output("explicacion-confusion", "children"),
              Input("fig-confusion", "clickData"), Input("fig-solapamiento", "clickData"))
def cb_explicacion(click_conf, click_sol):
    try:
        disparador = ctx.triggered_id
        if disparador == "fig-solapamiento" and click_sol:
            a, b = click_sol["points"][0]["customdata"][:2]
            return explicar_par(int(a), int(b))
        if disparador == "fig-confusion" and click_conf:
            p = click_conf["points"][0]
            a = int(str(p["y"]).split()[0])
            b = int(str(p["x"]).split()[0])
            return explicar_par(a, b)
    except Exception:
        pass
    return explicar_par(1, 2)


# =============================================================== callbacks: benchmark
def _tabla_heatmap(opt, metrica):
    df = D.APLIC.copy()
    df["tiempo_min"] = df["tiempo_total_s"] / 60
    if opt == "mejor":
        df = df.loc[df.groupby(["modelo", "balanceo"])["f1_macro_media"].idxmax()]
    else:
        df = df[df["optimizacion"] == opt]
    return df.pivot(index="modelo", columns="balanceo", values=metrica), df


@app.callback(Output("fig-heatmap", "figure"), Input("opt-heatmap", "value"), Input("metrica-heatmap", "value"))
def cb_heatmap(opt, metrica):
    piv, _ = _tabla_heatmap(opt, metrica)
    filas = [m for m in D.MODELOS if m in piv.index]
    piv = piv.reindex(index=filas, columns=list(D.BALANCEOS))
    z = piv.to_numpy()
    if metrica == "tiempo_min":
        texto = [["N/A" if np.isnan(v) else f"{v:.0f}" for v in fila] for fila in z]
        escala = [[0, "#e3f2fd"], [1, "#0d47a1"]]
        zz = np.log10(z)
        barra = dict(title="min (log)", tickvals=[0, 1, 2], ticktext=["1", "10", "100"])
    else:
        texto = [["N/A" if np.isnan(v) else f"{v:.3f}" for v in fila] for fila in z]
        escala = [[0, "#fff3e0"], [0.4, "#f6c344"], [0.7, "#4fc38a"], [1, "#0b4f34"]]
        zz, barra = z, dict(title="F1" if metrica.startswith("f1") else "Acc.")
    fig = go.Figure(go.Heatmap(
        z=zz, x=[D.BALANCEOS[b] for b in piv.columns], y=[D.MODELOS[m] for m in piv.index], text=texto,
        texttemplate="%{text}", textfont=dict(size=13), xgap=3, ygap=3, colorscale=escala, colorbar=barra,
        customdata=[[[m, b] for b in piv.columns] for m in piv.index],
        hovertemplate="<b>%{y}</b> · %{x}<br>%{text}<extra>clic para ver el detalle</extra>"))
    nombre = "el mejor optimizador" if opt == "mejor" else D.OPTIMIZADORES[opt]
    fig.update_layout(height=430, title=f"Cada celda: una combinación con {nombre} · clic 👆",
                      yaxis=dict(autorange="reversed", showgrid=False), xaxis=dict(side="top", showgrid=False))
    return fig


@app.callback(Output("detalle-combinacion", "children"),
              Input("fig-heatmap", "clickData"), Input("opt-heatmap", "value"))
def cb_detalle(click, opt):
    modelo, balanceo = "XGB", "ninguno"
    try:
        if click and ctx.triggered_id == "fig-heatmap":
            punto = click["points"][0]
            modelo = {v: k for k, v in D.MODELOS.items()}[punto["y"]]
            balanceo = {v: k for k, v in D.BALANCEOS.items()}[punto["x"]]
    except Exception:
        pass
    filas = D.TABLA[(D.TABLA["modelo"] == modelo) & (D.TABLA["balanceo"] == balanceo)]
    if not filas["aplicable"].any():
        return html.P(f"{D.MODELOS[modelo]} no admite {D.BALANCEOS[balanceo].lower()}: la combinación no es aplicable.")
    filas = filas[filas["aplicable"]].copy()
    ranking = D.APLIC["f1_macro_media"].rank(ascending=False, method="min")
    cab = html.Tr([html.Th("Optimizador"), html.Th("F1 macro"), html.Th("Pliegues"), html.Th("Tiempo"), html.Th("Puesto")])
    cuerpo = []
    mejor = filas["f1_macro_media"].max()
    for _, f in filas.sort_values("f1_macro_media", ascending=False).iterrows():
        pl = " · ".join(fmt(v) for v in f["f1_pliegues"])
        cuerpo.append(html.Tr([html.Td(D.OPTIMIZADORES[f["optimizacion"]]), html.Td(fmt(f["f1_macro_media"]), className="num"),
                               html.Td(pl, className="num"), html.Td(f"{f['tiempo_total_s'] / 60:.0f} min", className="num"),
                               html.Td(f"{int(ranking[f.name])} / {len(D.APLIC)}", className="num")],
                              className="resaltada" if f["f1_macro_media"] == mejor else ""))
    top = filas.loc[filas["f1_macro_media"].idxmax()]
    hp = top["hiper"][0] if top["hiper"] else {}
    hp_txt = ", ".join(f"{k} = {('sin límite' if v is None else (fmt(v, 3).rstrip('0').rstrip(',') if isinstance(v, float) else v))}" for k, v in hp.items())
    return [
        html.H5(f"{D.MODELOS[modelo]} · {D.BALANCEOS[balanceo]}", style={"fontWeight": 900, "color": "#1b6f5c"}),
        html.Table([html.Thead(cab), html.Tbody(cuerpo)], className="tabla-bosque mb-3"),
        html.P([html.B("Hiperparámetros elegidos (mejor optimizador, pliegue 1): "), hp_txt or "—"]),
        html.P([html.B("¿Cómo leer los pliegues? "), "Son los F1 del bucle externo de la validación anidada: tres estimaciones "
                "independientes del desempeño. Si varían poco, el resultado es estable."], className="small text-muted mb-0"),
    ]


@app.callback(Output("fig-dispersion", "figure"), Input("modelos-dispersion", "value"))
def cb_dispersion(modelos):
    df = D.APLIC[D.APLIC["modelo"].isin(modelos or [])]
    if df.empty:
        return vacio("Selecciona al menos un algoritmo", 420)
    simbolos = {"ninguno": "circle", "smote": "diamond", "adasyn": "square", "balanced": "triangle-up"}
    fig = go.Figure()
    for m in [k for k in D.MODELOS if k in modelos]:
        g = df[df["modelo"] == m]
        fig.add_scatter(x=g["tiempo_total_s"] / 60, y=g["f1_macro_media"], mode="markers", name=D.MODELOS[m],
                        marker=dict(color=D.COLOR_MODELO[m], size=11, symbol=[simbolos[b] for b in g["balanceo"]],
                                    line=dict(color="white", width=1)),
                        customdata=np.c_[g["balanceo"].map(D.BALANCEOS), g["optimizacion"].map(D.OPTIMIZADORES)],
                        hovertemplate=f"<b>{D.MODELOS[m]}</b><br>%{{customdata[0]}} · %{{customdata[1]}}<br>F1 macro: %{{y:.3f}}"
                                      "<br>Tiempo: %{x:.1f} min<extra></extra>")
    fig.update_layout(height=420, title="● sin balanceo · ◆ SMOTE · ■ ADASYN · ▲ pesos de clase",
                      xaxis=dict(type="log", title="Tiempo total de la validación anidada (min, escala log)"),
                      yaxis=dict(title="F1 macro (media de 3 pliegues)"), legend=dict(orientation="h", y=-0.2, x=0))
    return fig


@app.callback(Output("fig-balanceo", "figure"), Input("opt-heatmap", "value"))
def cb_balanceo(opt):
    piv, _ = _tabla_heatmap(opt, "f1_macro_media")
    piv = piv.reindex(index=[m for m in D.MODELOS if m in piv.index])
    fig = go.Figure()
    for b, color in [("smote", "#1e88e5"), ("adasyn", "#8e5ea2"), ("balanced", "#e0a526")]:
        delta = piv[b] - piv["ninguno"]
        fig.add_bar(y=[D.MODELOS[m] for m in piv.index], x=delta, orientation="h", name=D.BALANCEOS[b], marker_color=color,
                    hovertemplate=f"<b>%{{y}}</b><br>{D.BALANCEOS[b]}: %{{x:+.3f}} de F1 frente a no balancear<extra></extra>")
    fig.add_vline(x=0, line_color="#1f2d27", line_width=1.5)
    fig.update_layout(barmode="group", height=420, title="Δ F1 macro frente a «sin balanceo»",
                      xaxis=dict(title="Diferencia de F1 macro"), yaxis=dict(autorange="reversed", showgrid=False),
                      legend=dict(orientation="h", y=-0.2, x=0))
    return fig


# =============================================================== callbacks: optimización
@app.callback(Output("fig-anytime", "figure"), Input("metodos-anytime", "value"), Input("eje-anytime", "value"))
def cb_anytime(metodos, eje):
    if not metodos:
        return vacio("Selecciona al menos un método", 420)
    fig = go.Figure()
    for metodo in metodos:
        g = D.ANYTIME[D.ANYTIME["metodo"] == metodo]
        piv = g.pivot(index="evaluacion", columns="semilla", values="mejor_hasta_ahora")
        x = piv.index if eje == "evaluacion" else g.groupby("evaluacion")["tiempo_acumulado_s"].mean().reindex(piv.index)
        color = D.COLOR_OPT_NOMBRE[metodo]
        fig.add_scatter(x=list(x) + list(x)[::-1], y=list(piv.max(axis=1)) + list(piv.min(axis=1))[::-1], fill="toself",
                        fillcolor=color, opacity=0.15, line=dict(width=0), hoverinfo="skip", showlegend=False)
        fig.add_scatter(x=x, y=piv.mean(axis=1), mode="lines", name=metodo, line=dict(color=color, width=3),
                        hovertemplate=f"<b>{metodo}</b><br>%{{x:.0f}}<br>Mejor F1 hasta ahora: %{{y:.4f}}<extra></extra>")
    fig.update_layout(height=420, title="Mejor F1 macro encontrado hasta cada momento (media de 5 semillas)",
                      xaxis=dict(title="Evaluaciones realizadas" if eje == "evaluacion" else "Tiempo acumulado (s)"),
                      yaxis=dict(title="Mejor F1 macro hasta ahora"), legend=dict(orientation="h", y=-0.2, x=0))
    return fig


@app.callback(Output("fig-optimizadores", "figure"), Input("metrica-opt", "value"))
def cb_optimizadores(metrica):
    g = D.APLIC.groupby("optimizacion")[metrica].agg(["mean", "median"]).reindex(list(D.OPTIMIZADORES))
    if metrica == "tiempo_total_s":
        g = g / 60
    etiqueta = {"f1_macro_media": "F1 macro medio", "tiempo_total_s": "Tiempo medio por combinación (min)",
                "evaluaciones_totales": "Evaluaciones por combinación"}[metrica]
    d = 3 if metrica == "f1_macro_media" else 0
    fig = go.Figure(go.Bar(x=[D.OPTIMIZADORES[o] for o in g.index], y=g["mean"], text=[fmt(v, d) for v in g["mean"]],
                           textposition="outside", marker_color=[D.COLOR_OPT[o] for o in g.index],
                           hovertemplate="<b>%{x}</b><br>" + etiqueta + ": %{y:.3f}<extra></extra>"))
    fig.update_layout(height=420, title=etiqueta + " (108 combinaciones)", yaxis=dict(title=etiqueta,
                      range=[0, g["mean"].max() * 1.2]), xaxis=dict(showgrid=False))
    return fig


# =============================================================== callbacks: finalista
@app.callback(Output("fig-por-clase", "figure"), Input("metrica-clase", "value"))
def cb_por_clase(metrica):
    x = [ETIQ[c] for c in CLASES]
    fig = go.Figure()
    for pc, nombre, color in [(D.PC_LR, "Regresión logística", "#d9643a"), (D.PC_XGB, "XGBoost (finalista)", "#0f9d58")]:
        fig.add_bar(x=x, y=pc[metrica], name=nombre, marker_color=color, text=[fmt(v, 2) for v in pc[metrica]],
                    textposition="outside", hovertemplate=f"<b>{nombre}</b><br>%{{x}}<br>{metrica}: %{{y:.3f}}<extra></extra>")
    fig.update_layout(barmode="group", height=430, yaxis=dict(range=[0, 1.12], title=metrica), xaxis=dict(tickangle=25, showgrid=False),
                      title=f"{metrica} por cobertura en la prueba reservada", legend=dict(orientation="h", y=-0.3, x=0))
    return fig


@app.callback(Output("fig-confusion-fin", "figure"), Input("modelo-confusion", "value"), Input("modo-confusion-fin", "value"))
def cb_confusion_fin(modelo, modo):
    cm = D.CM_XGB if modelo == "xgb" else D.CM_LR
    nombre = "XGBoost (finalista)" if modelo == "xgb" else "Regresión logística"
    return fig_confusion(cm, modo, f" · {nombre}")


@app.callback(Output("fig-areas", "figure"), Input("metrica-areas", "value"))
def cb_areas(metrica):
    return fig_areas_no_vistas(metrica)


@app.callback(Output("fig-estadistica", "figure"), Output("nota-estadistica", "children"), Input("vista-estadistica", "value"))
def cb_estadistica(vista):
    fam = D.MEJORES
    if vista == "cd":
        orden = fam.sort_values("rango")
        cd = D.CD_FAM
        mejor = orden["rango"].min()
        fig = go.Figure()
        fig.add_vrect(x0=mejor, x1=mejor + cd, fillcolor="rgba(15,157,88,0.12)", line_width=0, layer="below")
        fig.add_annotation(x=mejor + cd / 2, y=1.08, yref="paper", showarrow=False,
                           text=f"<b>Zona de la diferencia crítica (CD = {fmt(cd, 2)})</b>: no se distingue de XGBoost",
                           font=dict(color="#0b7a4b", size=12))
        nombres = [D.MODELOS[m] for m in orden["modelo"]]
        fuera = [r > mejor + cd for r in orden["rango"]]
        fig.add_scatter(x=orden["rango"], y=nombres, mode="markers+text",
                        text=[fmt(r, 1) for r in orden["rango"]], textposition="middle right",
                        marker=dict(size=18, color=[D.COLOR_MODELO[m] for m in orden["modelo"]],
                                    symbol=["x" if f else "circle" for f in fuera], line=dict(color="white", width=2)),
                        customdata=np.c_[orden["f1_macro_media"]], showlegend=False,
                        hovertemplate="<b>%{y}</b><br>Rango promedio: %{x:.1f}<br>F1 macro: %{customdata[0]:.3f}<extra></extra>")
        fig.update_layout(height=430, title="Rango promedio en los 3 pliegues (1 = mejor) · ✖ = significativamente peor que XGBoost",
                          xaxis=dict(range=[0.5, D.K_FAM + 0.8], dtick=1, title="Rango promedio"),
                          yaxis=dict(autorange="reversed", showgrid=False), margin=dict(t=80))
        texto = [html.B("💡 Interpretación: "), f"Friedman sobre las 7 familias (mejor combinación de cada una) es significativo "
                 f"(p = 0,006), pero con solo 3 pliegues la diferencia crítica de Nemenyi es grande ({fmt(D.CD_FAM, 2)} rangos). "
                 "Solo XGBoost frente a Naive Bayes supera la CD. Con 108 combinaciones la CD (110,9) supera incluso el rango máximo posible: "
                 "por eso el análisis se hace por algoritmo. ",
                 html.A("Profundiza en la sección 7.2 del Jupyter Book →", href=LIBRO + "08_comparacion_estadistica.html", target="_blank")]
        return fig, texto
    if vista == "nemenyi":
        nombres = [D.MODELOS[m] for m in D.NEMENYI.index]
        z = D.NEMENYI.to_numpy()
        fig = go.Figure(go.Heatmap(z=z, x=nombres, y=nombres, text=[[f"{v:.3f}" for v in fila] for fila in z], texttemplate="%{text}",
                                   colorscale=[[0, "#b5432a"], [0.05, "#f08a5d"], [0.2, "#fff3e0"], [1, "#f1fbf3"]],
                                   zmin=0, zmax=1, xgap=2, ygap=2, colorbar=dict(title="p"),
                                   hovertemplate="<b>%{y}</b> vs <b>%{x}</b><br>p = %{z:.3f}<extra></extra>"))
        fig.update_layout(height=430, title="Valores p de Nemenyi entre algoritmos (rojo: p < 0,05)",
                          yaxis=dict(autorange="reversed", showgrid=False), xaxis=dict(tickangle=30, showgrid=False))
        texto = [html.B("💡 Interpretación: "), "Solo el par XGBoost–Naive Bayes es significativo (p = 0,012). Que el resto no lo sea no "
                 "significa que sean iguales: con 3 pliegues la prueba tiene poca potencia. La prueba de DeLong sobre la prueba "
                 "reservada sí separa al finalista de la referencia en todas las clases. ",
                 html.A("Profundiza en la sección 7.2 del Jupyter Book →", href=LIBRO + "08_comparacion_estadistica.html", target="_blank")]
        return fig, texto
    dl = D.DELONG
    fig = go.Figure()
    fig.add_bar(x=[ETIQ[c] for c in dl["clase"]], y=dl["auc_referencia"], name="Regresión logística", marker_color="#d9643a",
                hovertemplate="<b>%{x}</b><br>AUC: %{y:.4f}<extra>Regresión logística</extra>")
    fig.add_bar(x=[ETIQ[c] for c in dl["clase"]], y=dl["auc_finalista"], name="XGBoost (finalista)", marker_color="#0f9d58",
                customdata=np.c_[dl["delta_auc"], dl["z"]],
                hovertemplate="<b>%{x}</b><br>AUC: %{y:.4f}<br>Δ AUC = %{customdata[0]:+.4f} · z = %{customdata[1]:.1f}<extra>XGBoost</extra>")
    fig.update_layout(barmode="group", height=430, title="AUC uno contra el resto por clase (prueba reservada)",
                      yaxis=dict(range=[0.8, 1.005], title="AUC"), xaxis=dict(tickangle=25, showgrid=False),
                      legend=dict(orientation="h", y=-0.3, x=0))
    texto = [html.B("💡 Interpretación: "), "La prueba de DeLong compara las curvas ROC de los dos modelos sobre las mismas 116.203 "
             "celdas. Las siete diferencias son significativas tras la corrección de Holm (p < 10⁻³⁰⁰ en todas); la mejora es mayor "
             "en las clases que más se confundían (pícea/abeto y lodgepole). El tamaño del efecto (δ de Cliff = 1) es máximo. ",
             html.A("Profundiza en la sección 7.3 del Jupyter Book →", href=LIBRO + "08_comparacion_estadistica.html", target="_blank")]
    return fig, texto


# =============================================================== callbacks: interpretabilidad
@app.callback(Output("fig-shap-global", "figure"), Input("clase-shap", "value"), Input("n-shap", "value"))
def cb_shap_global(clase, n):
    imp = np.abs(D.SHAP_VAL).mean(axis=0)              # (variables, clases)
    total = imp.sum(axis=1) if clase == "todas" else imp[:, int(clase) - 1]
    idx = np.argsort(total)[::-1][:n][::-1]
    nombres = [D.NOMBRE_ING.get(D.SHAP_NOMBRES[i], D.SHAP_NOMBRES[i]) for i in idx]
    fig = go.Figure()
    if clase == "todas":
        for c in CLASES:
            fig.add_bar(y=nombres, x=imp[idx, c - 1], orientation="h", name=ETIQ[c], marker_color=COLOR[c],
                        hovertemplate=f"<b>%{{y}}</b><br>{LARGO[c]}: %{{x:.3f}}<extra></extra>")
        titulo = "|SHAP| medio por variable, apilado por cobertura"
    else:
        c = int(clase)
        fig.add_bar(y=nombres, x=imp[idx, c - 1], orientation="h", marker_color=COLOR[c], showlegend=False,
                    hovertemplate="<b>%{y}</b><br>|SHAP| medio: %{x:.3f}<extra></extra>")
        titulo = f"|SHAP| medio para {LARGO[c]}"
    fig.update_layout(barmode="stack", height=max(380, 26 * n + 140), title=titulo,
                      xaxis=dict(title="Importancia media (|SHAP|, log-odds)"), yaxis=dict(showgrid=False),
                      legend=dict(orientation="h", y=-0.18, x=0, font=dict(size=11)))
    return fig


@app.callback(Output("fig-dependencia", "figure"), Output("nota-dependencia", "children"),
              Input("var-dependencia", "value"), Input("clase-dependencia", "value"))
def cb_dependencia(variable, clase):
    j = D.SHAP_NOMBRES.index(variable)
    x = D.SHAP_CRUDOS[variable].to_numpy()
    y = D.SHAP_VAL[:, j, int(clase) - 1]
    fig = go.Figure()
    for a in D.AREAS:
        m = D.SHAP_AREA == a
        fig.add_scatter(x=x[m], y=y[m], mode="markers", name=a, marker=dict(color=D.COLOR_AREA[a], size=6, opacity=0.6),
                        hovertemplate=f"<b>{a}</b><br>{D.VARIABLES[variable]}: %{{x:,.0f}}<br>SHAP: %{{y:+.2f}}<extra></extra>")
    fig.add_hline(y=0, line_color="#1f2d27", line_width=1)
    fig.update_layout(height=430, title=f"Efecto de {D.VARIABLES[variable].split(' (')[0].lower()} sobre «{LARGO[int(clase)]}»",
                      xaxis=dict(title=D.VARIABLES[variable]), yaxis=dict(title="Valor SHAP (log-odds)"),
                      legend=dict(orientation="h", y=-0.2, x=0))
    texto = [html.B("💡 Cómo leerlo: "), "cada punto es una celda de prueba. Por encima de cero, ese valor de la variable empuja la "
             "predicción hacia la cobertura elegida; por debajo, en contra. A diferencia de un coeficiente lineal, la curva puede "
             "subir y bajar: XGBoost aprende umbrales y franjas (por ejemplo, la franja altitudinal propia de cada especie). ",
             html.A("Profundiza en la sección 8.1 del Jupyter Book →", href=LIBRO + "09_interpretabilidad.html", target="_blank")]
    return fig, texto


def _filtro_celdas(tipo, clase):
    m = np.ones(len(D.SHAP_REAL), dtype=bool)
    if tipo == "error":
        m &= D.SHAP_PRED != D.SHAP_REAL
    elif tipo == "acierto":
        m &= D.SHAP_PRED == D.SHAP_REAL
    if clase != "todas":
        m &= D.SHAP_REAL == int(clase)
    return np.flatnonzero(m)


@app.callback(Output("indice-celda", "max"), Output("indice-celda", "value"),
              Input("tipo-celda", "value"), Input("clase-celda", "value"))
def cb_rango_celdas(tipo, clase):
    idx = _filtro_celdas(tipo, clase)
    return max(len(idx) - 1, 0), 0


@app.callback(Output("fig-waterfall", "figure"), Output("resumen-celda", "children"),
              Input("indice-celda", "value"), Input("tipo-celda", "value"), Input("clase-celda", "value"))
def cb_waterfall(i, tipo, clase):
    idx = _filtro_celdas(tipo, clase)
    if len(idx) == 0:
        return vacio("No hay celdas con ese filtro en la muestra", 420), ""
    k = idx[min(i or 0, len(idx) - 1)]
    real, pred = int(D.SHAP_REAL[k]), int(D.SHAP_PRED[k])
    contrib = D.SHAP_VAL[k, :, pred - 1]
    orden = np.argsort(np.abs(contrib))[::-1]
    top = orden[:10]
    resto = contrib[orden[10:]].sum()
    nombres = [D.NOMBRE_ING.get(D.SHAP_NOMBRES[t], D.SHAP_NOMBRES[t]) for t in top][::-1]
    valores = list(contrib[top][::-1])
    nombres = [f"Otras {len(orden) - 10} variables"] + nombres
    valores = [resto] + valores
    base = float(D.SHAP_BASE[pred - 1])
    fig = go.Figure(go.Waterfall(
        orientation="h", y=["Valor base"] + nombres + ["Puntuación final"], x=[base] + valores + [0],
        measure=["absolute"] + ["relative"] * len(valores) + ["total"],
        increasing=dict(marker=dict(color="#0f9d58")), decreasing=dict(marker=dict(color="#d9643a")),
        totals=dict(marker=dict(color=COLOR[pred])), connector=dict(line=dict(color="#cfdcd3")),
        hovertemplate="<b>%{y}</b><br>%{x:+.2f}<extra></extra>"))
    fig.update_layout(height=470, title=f"¿Por qué predijo «{LARGO[pred]}»? (log-odds de esa cobertura)",
                      xaxis=dict(title="Contribución SHAP"), yaxis=dict(showgrid=False))
    crudos = D.SHAP_CRUDOS.iloc[k]
    acierto = real == pred
    resumen = html.Div([
        dbc.Badge("✅ Acierto" if acierto else "❌ Error", color="success" if acierto else "danger", className="me-2"),
        html.Span([html.B("Real: "), f"{ETIQ[real]} · ", html.B("Predicha: "), f"{ETIQ[pred]} (p = {fmt(D.SHAP_PROBA[k, pred - 1], 2)}) · ",
                   html.B("Área: "), f"{D.SHAP_AREA[k]} · ", html.B("Elevación: "), f"{miles(crudos['Elevation'])} m · ",
                   f"celda {min(i or 0, len(idx) - 1) + 1} de {len(idx)}"]),
    ], className="small")
    return fig, resumen


@app.callback(Output("tabla-lime", "children"), Input("pestanas", "active_tab"))
def cb_lime(_):
    filas = []
    for clave, titulo in [("correcta", "✅ Celda bien clasificada"), ("error", "❌ Celda mal clasificada")]:
        c = D.LIME[clave]
        filas.append(html.Div([
            html.H6(titulo, style={"fontWeight": 900}),
            html.P(f"Real: {ETIQ[c['clase_real']]} · Predicha: {ETIQ[c['clase_predicha']]} (p = {fmt(c['probabilidad'], 2)})", className="small mb-1"),
            html.Table([
                html.Thead(html.Tr([html.Th("#"), html.Th("Top 5 SHAP"), html.Th("Top 5 LIME")])),
                html.Tbody([html.Tr([html.Td(str(i + 1)),
                                     html.Td(D.NOMBRE_ING.get(s, s)),
                                     html.Td(D.NOMBRE_ING.get(l, l))])
                            for i, (s, l) in enumerate(zip(c["top5_shap"], c["top5_lime"]))]),
            ], className="tabla-bosque mb-1"),
            html.P([html.B("Coincidencias: "), f"{len(c['comunes_top5'])} de 5 · ", html.B("R² local de LIME: "), fmt(c["lime_r2_local"], 2)],
                   className="small mb-3"),
        ]))
    return filas


# =============================================================== callbacks: eficiencia
@app.callback(Output("fig-escala", "figure"), Input("modelos-escala", "value"))
def cb_escala(modelos):
    if not modelos:
        return vacio("Selecciona al menos un algoritmo", 430)
    paleta = ["#0f9d58", "#1e88e5", "#c8a13a", "#1b6f5c", "#8e5ea2", "#d9643a", "#00acc1"]
    colores = dict(zip(D.ESC["modelo"].unique(), paleta))
    exp = D.ESC_EXP.set_index("modelo")["exponente_empirico"]
    fig = go.Figure()
    for m in modelos:
        g = D.ESC[D.ESC["modelo"] == m]
        fig.add_scatter(x=g["n"], y=g["tiempo_s"], mode="lines+markers", name=f"{m} (b = {fmt(exp[m], 2)})",
                        line=dict(color=colores[m], width=3), marker=dict(size=8),
                        hovertemplate=f"<b>{m}</b><br>n = %{{x:,}}<br>%{{y:.3f}} s<extra></extra>")
    fig.update_layout(height=430, title="Tiempo de entrenamiento (o de predicción en KNN) según el tamaño de la muestra",
                      xaxis=dict(type="log", title="Celdas de entrenamiento (escala log)"),
                      yaxis=dict(type="log", title="Segundos (escala log)"), legend=dict(orientation="h", y=-0.25, x=0, font=dict(size=11)))
    return fig


NOTAS_COMP = {
    "KNN (k = 5)": "Los árboles KD y Ball Tree aceleran la búsqueda de vecinos solo en pocas dimensiones. Con 57 variables pierden su ventaja y la fuerza bruta vectorizada es la más rápida (KD-Tree 4,5 veces más lento; Ball Tree 24 veces).",
    "Naive Bayes": "partial_fit procesa los datos por lotes: mismo resultado y mucha menos memoria (≈ 7,6 veces menos). Útil cuando los datos no caben en memoria.",
    "Regresión logística (L2)": "SAGA, un optimizador estocástico, converge unas 4 veces más rápido que L-BFGS con una tolerancia algo más laxa, sin perder F1.",
    "XGBoost (200 árboles)": "El método hist agrupa cada variable en histogramas y evita evaluar todos los cortes posibles: ≈ 12 veces más rápido que el método exact con un F1 prácticamente igual. La parada temprana ahorra árboles innecesarios.",
    "SVM": "LinearSVC y SGD escalan de forma lineal, pero pierden la frontera curva del núcleo RBF: el F1 macro cae de 0,65 a ≈ 0,50. Más rápido no siempre es mejor.",
}


@app.callback(Output("fig-comp", "figure"), Output("nota-comp", "children"), Input("algoritmo-comp", "value"))
def cb_comp(algoritmo):
    g = D.COMP[D.COMP["modelo"] == algoritmo]
    versiones = g["versión"].tolist()
    fig = go.Figure()
    fig.add_bar(x=versiones, y=g["tiempo_entrenamiento_s"], name="Entrenamiento (s)", marker_color="#1e88e5",
                text=[fmt(v, 2) for v in g["tiempo_entrenamiento_s"]], textposition="outside", cliponaxis=False)
    fig.add_bar(x=versiones, y=g["tiempo_inferencia_s"], name="Inferencia (s)", marker_color="#e0a526",
                text=[fmt(v, 2) for v in g["tiempo_inferencia_s"]], textposition="outside", cliponaxis=False)
    fig.add_scatter(x=versiones, y=g["F1_macro"], name="F1 macro", yaxis="y2", mode="markers+text",
                    marker=dict(size=16, color="#0f9d58", symbol="diamond"), text=[fmt(v) for v in g["F1_macro"]],
                    textposition="top center")
    fig.update_layout(barmode="group", height=430, title="Tiempo (barras, escala log) y F1 macro (rombos)", margin=dict(t=70),
                      yaxis=dict(type="log", title="Segundos"), yaxis2=dict(overlaying="y", side="right", range=[0, 1.05],
                                                                             title="F1 macro", showgrid=False),
                      xaxis=dict(showgrid=False), legend=dict(orientation="h", y=-0.25, x=0))
    texto = [html.B("💡 Interpretación: "), NOTAS_COMP.get(algoritmo, ""), " ",
             html.A("Profundiza en la sección 9.2 del Jupyter Book →", href=LIBRO + "10_conclusiones_finales.html", target="_blank")]
    return fig, texto


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)
