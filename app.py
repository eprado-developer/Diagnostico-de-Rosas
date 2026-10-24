import html
import os
import re
import zlib

import streamlit as st

from logica_arbol import (
    cargar_arbol, categoria_de, es_diagnostico, ficha_de, fuentes_de, pista_de,
    perfil_de, pregunta_de, profundidad_restante, prompt_hoja, prompt_pregunta,
    respuesta_offline_hoja, respuesta_offline_pregunta, trayecto_qa, validar_arbol,
)
from conocimiento_rosas import FICHAS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_ARBOL = os.path.join(BASE_DIR, "DiagnosticoRosas.json")
MODELO_POR_DEFECTO = "rosas-experto"

st.set_page_config(page_title="Rosal · diagnóstico de rosas", page_icon="🌹",
                   layout="centered", initial_sidebar_state="collapsed")

# -------------------------------------------------------------
# Estilos
# -------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,500;1,9..144,300&family=Inter:wght@400;500&display=swap');

:root {
  --paper:#FBF7F2; --card:#FFFFFF; --ink:#2B2024; --muted:#8A7B7F; --line:#E9DFD5;
  --rose:#8E2F45; --rose-soft:#F6E7EA; --sage:#6F8F72; --gold:#B8893A;
}
html, body, .stApp, [data-testid="stAppViewContainer"] { background: var(--paper); color: var(--ink); }
.stApp, .stApp p, .stApp li, .stApp button, .stApp label { font-family: 'Inter', system-ui, sans-serif; }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
.block-container { max-width: 680px; padding-top: 2.2rem; padding-bottom: 5rem; }

/* Marca */
.brand { display:flex; align-items:center; gap:.7rem; margin-bottom:2.2rem; }
.brand svg { width:44px; height:44px; flex:none; }
.brand-name { font-family:'Fraunces', serif; font-weight:500; font-size:1.25rem; letter-spacing:.01em; }
.brand-sub { color:var(--muted); font-size:.78rem; letter-spacing:.14em; text-transform:uppercase; }

/* Progreso */
.dots { display:flex; gap:.45rem; margin-bottom:1.1rem; }
.dot { width:26px; height:3px; border-radius:2px; background:var(--line); }
.dot.on { background:var(--rose); }

/* Ruta */
.trail { color:var(--muted); font-size:.82rem; margin-bottom:.4rem; line-height:1.7; }
.trail b { color:var(--ink); font-weight:500; }
.trail i { font-style:normal; margin:0 .35rem; color:#CDBFB6; }

/* Pregunta */
.eyebrow { color:var(--rose); font-size:.74rem; letter-spacing:.16em; text-transform:uppercase; font-weight:500; margin-bottom:.5rem; }
.q-title { font-family:'Fraunces', serif; font-weight:300; font-size:2.35rem; line-height:1.15; margin:.1rem 0 1.8rem; letter-spacing:-.01em; }

/* Opciones */
div.stButton > button {
  width:100%; min-height:58px; justify-content:flex-start; text-align:left;
  background:var(--card); color:var(--ink); border:1px solid var(--line); border-radius:14px;
  padding:.85rem 1.15rem; font-weight:500; font-size:1rem;
  transition:all .18s ease; box-shadow:none;
}
div.stButton > button > div, div.stButton > button p { width:100%; text-align:left !important; justify-content:flex-start !important; }
div.stButton > button:hover { border-color:var(--rose); color:var(--rose); transform:translateY(-1px);
  box-shadow:0 6px 18px rgba(142,47,69,.08); }
div.stButton > button:focus:not(:active) { border-color:var(--rose); color:var(--rose); }
.hint { color:var(--muted); font-size:.82rem; margin:-.55rem .3rem .9rem 1.15rem; }

/* Navegación discreta */
[class*="st-key-nav_"] button { min-height:auto; width:auto !important; background:transparent; border:none; color:var(--muted);
  padding:.3rem .2rem; font-weight:400; font-size:.88rem; box-shadow:none; }
[class*="st-key-nav_"] button:hover { color:var(--rose); background:transparent; transform:none; box-shadow:none; }

/* Diagnóstico */
.dx-wrap { background:var(--card); border:1px solid var(--line); border-radius:22px; padding:2rem 2rem 1.6rem; margin-bottom:1.4rem; }
.chip-cat { display:inline-flex; align-items:center; gap:.45rem; font-size:.74rem; letter-spacing:.14em; text-transform:uppercase; color:var(--muted); }
.chip-cat span.pt { width:8px; height:8px; border-radius:50%; display:inline-block; }
.dx-name { font-family:'Fraunces', serif; font-weight:500; font-size:2.3rem; line-height:1.1; margin:.6rem 0 .2rem; }
.dx-sci { font-family:'Fraunces', serif; font-style:italic; font-weight:300; color:var(--muted); margin-bottom:1.3rem; }
.act-label { font-size:.74rem; letter-spacing:.14em; text-transform:uppercase; color:var(--muted); margin-bottom:.55rem; }
.act { display:inline-block; background:var(--rose-soft); color:var(--rose); border-radius:999px; padding:.38rem .95rem; font-size:.92rem; font-weight:500; margin:0 .15rem .35rem 0; }
.act-sep { color:var(--muted); font-size:.85rem; margin:0 .3rem; }
.confirm { margin-top:1rem; padding-top:1rem; border-top:1px dashed var(--line); color:var(--muted); font-size:.92rem; }
.fine { color:var(--muted); font-size:.78rem; margin-top:1.6rem; line-height:1.6; }
.ficha li { margin-bottom:.35rem; line-height:1.55; }
.ia-title { font-family:'Fraunces', serif; font-weight:500; font-size:1.2rem; margin:2rem 0 .6rem; }

/* Tabs y expanders */
button[data-baseweb="tab"] { font-size:.92rem; }
[data-testid="stExpander"] { border:1px solid var(--line); border-radius:14px; background:var(--card); }
section[data-testid="stSidebar"] { background:#F3ECE3; }
</style>
""", unsafe_allow_html=True)

LOGO = """<svg viewBox="0 0 48 48" fill="none" stroke="#8E2F45" stroke-width="1.6" stroke-linecap="round">
<circle cx="24" cy="24" r="4"/><path d="M24 20c-5-1-8 3-6 7"/><path d="M28 24c1-5-3-8-7-6"/>
<path d="M24 28c5 1 8-3 6-7"/><path d="M20 24c-1 5 3 8 7 6"/>
<path d="M24 11c-9 0-15 6-15 13s6 14 15 14 15-7 15-14-6-13-15-13z" opacity=".55"/>
<path d="M24 38v8M24 43c-4-1-6-3-7-6M24 44c4-1 6-3 7-6" opacity=".6" stroke="#6F8F72"/></svg>"""

COLOR_CAT = {"Hongo": "#8E2F45", "Plaga": "#B8893A", "Nutrición": "#6F8F72", "Suelo y riego": "#5B7A99"}


def a_html(texto):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(texto))


# -------------------------------------------------------------
# Estado
# -------------------------------------------------------------
def reiniciar_navegacion():
    st.session_state.historial = [st.session_state.arbol] if st.session_state.arbol else []


def cargar():
    arbol, error = cargar_arbol(ARCHIVO_ARBOL)
    st.session_state.arbol = arbol
    st.session_state.error_arbol = error
    st.session_state.cache_ia = {}
    st.session_state.cargado = True
    reiniciar_navegacion()


if not st.session_state.get("cargado"):
    cargar()

# -------------------------------------------------------------
# Barra lateral (ajustes, escondida por defecto)
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("#### Ajustes")
    modelo_ollama = st.text_input("Modelo de Ollama", value=MODELO_POR_DEFECTO,
                                  help="Créalo con: python generar_modelfile.py  y  ollama create rosas-experto -f Modelfile")
    temperatura = st.slider("Creatividad", 0.0, 1.0, 0.2, 0.1)
    ia_automatica = st.toggle("La IA ayuda en cada pregunta", value=False,
                              help="Apagado: aparece un botón ‘Ayuda de la IA’ solo cuando la necesites.")
    st.divider()
    if st.button("Recargar JSON", use_container_width=True):
        cargar()
        st.rerun()
    if st.button("Reiniciar recorrido", use_container_width=True):
        reiniciar_navegacion()
        st.rerun()
    if st.session_state.arbol:
        avisos = validar_arbol(st.session_state.arbol)
        if avisos:
            with st.expander(f"⚠️ {len(avisos)} aviso(s) del árbol"):
                for a in avisos:
                    st.write("•", a)
        with st.expander("Ver JSON activo"):
            st.json(st.session_state.arbol)

arbol = st.session_state.arbol
if st.session_state.error_arbol:
    st.error(st.session_state.error_arbol)
    st.stop()

perfil = perfil_de(arbol)
historial = st.session_state.historial or [arbol]
nodo = historial[-1]
nivel = len(historial)
hijos = nodo.get("hijos", [])
clave_nodo = "|".join(n["valor"] for n in historial)

# -------------------------------------------------------------
# Marca
# -------------------------------------------------------------
st.markdown(f"""<div class="brand">{LOGO}<div>
<div class="brand-name">Rosal</div><div class="brand-sub">Diagnóstico de rosas</div></div></div>""",
            unsafe_allow_html=True)


# -------------------------------------------------------------
# IA (streaming + caché + modo sin IA)
# -------------------------------------------------------------
def mostrar_respuesta_ia(clave, prompt, offline_fn):
    cache = st.session_state.cache_ia
    clave = f"{clave}|{modelo_ollama}|{temperatura}"
    kb = f"{zlib.crc32(clave.encode())}"

    if clave in cache:
        st.markdown(cache[clave])
        if st.button("Regenerar", key=f"regen_{kb}"):
            del cache[clave]
            st.rerun()
        return
    try:
        import ollama
        with st.spinner("Pensando…"):
            stream = ollama.chat(
                model=modelo_ollama,
                messages=[{"role": "system", "content": perfil["sistema"]},
                          {"role": "user", "content": prompt}],
                options={"temperature": temperatura}, stream=True,
            )
            cache[clave] = st.write_stream(c["message"]["content"] for c in stream)
    except Exception as e:  # noqa: BLE001
        st.caption("✦ La IA local no está disponible; mientras tanto usa la ficha y las pistas de arriba.")
        with st.expander("¿Cómo activar la IA?"):
            st.markdown(
                "1. Abre Ollama (`ollama serve`).\n"
                "2. `python generar_modelfile.py`\n"
                f"3. `ollama create {MODELO_POR_DEFECTO} -f Modelfile`\n\n"
                f"Detalle técnico: `{e}`"
            )
        if st.button("Reintentar", key=f"retry_{kb}"):
            st.rerun()


def progreso(actual, total):
    puntos = "".join(f'<div class="dot {"on" if i < actual else ""}"></div>' for i in range(total))
    st.markdown(f'<div class="dots">{puntos}</div>', unsafe_allow_html=True)


def migas():
    if len(historial) > 1:
        partes = "<i>›</i>".join(f"<b>{html.escape(n['valor'])}</b>" if k == len(historial) - 1
                                 else html.escape(n["valor"]) for k, n in enumerate(historial[1:]))
        st.markdown(f'<div class="trail">{partes}</div>', unsafe_allow_html=True)


# -------------------------------------------------------------
# PREGUNTA
# -------------------------------------------------------------
if hijos:
    total = (nivel - 1) + profundidad_restante(nodo)
    progreso(nivel, total)
    migas()
    pregunta = pregunta_de(nodo, nivel)
    st.markdown(f'<div class="eyebrow">Pregunta {nivel} de {total}</div>'
                f'<div class="q-title">{a_html(pregunta)}</div>', unsafe_allow_html=True)

    for i, hijo in enumerate(hijos):
        if st.button(hijo["valor"], key=f"opt_{zlib.crc32(clave_nodo.encode())}_{i}", use_container_width=True):
            st.session_state.historial.append(hijo)
            st.rerun()
        pista = pista_de(hijo["valor"])
        if pista:
            st.markdown(f'<div class="hint">{html.escape(pista)}</div>', unsafe_allow_html=True)

    c1, c2, _ = st.columns([1, 1, 3])
    if nivel > 1:
        with c1:
            if st.button("← Atrás", key="nav_back"):
                st.session_state.historial.pop()
                st.rerun()
        with c2:
            if st.button("Reiniciar", key="nav_restart"):
                reiniciar_navegacion()
                st.rerun()

    # Ayuda de la IA para esta pregunta
    clave_ia = f"{clave_nodo}|pregunta"
    ya = any(k.startswith(clave_ia + "|") for k in st.session_state.cache_ia)
    flag = f"pedir_{clave_nodo}"
    st.markdown("<br>", unsafe_allow_html=True)
    if ia_automatica or ya or st.session_state.get(flag):
        st.markdown('<div class="ia-title">Ayuda de la IA</div>', unsafe_allow_html=True)
        mostrar_respuesta_ia(clave_ia, prompt_pregunta(historial), respuesta_offline_pregunta)
    elif st.button("✦ Ayuda de la IA para responder", key=f"nav_ask_{zlib.crc32(clave_nodo.encode())}"):
        st.session_state[flag] = True
        st.rerun()

# -------------------------------------------------------------
# DIAGNÓSTICO (hoja)
# -------------------------------------------------------------
else:
    total = (nivel - 1)
    progreso(total, total)
    migas()
    dx = nodo["diagnostico"]
    ficha = ficha_de(dx)
    cat = categoria_de(dx)
    color = COLOR_CAT.get(cat, "#8E2F45")

    # Acción en chips: «+» = combinar, «/» = alternativas
    partes = re.split(r"( \+ | / )", nodo["accion"])
    chips = ""
    for p in partes:
        if p == " + ":
            chips += '<span class="act-sep">＋</span>'
        elif p == " / ":
            chips += '<span class="act-sep">o</span>'
        else:
            chips += f'<span class="act">{html.escape(p)}</span>'

    confirm = nodo.get("pregunta_confirmacion") or (ficha or {}).get("confirmar")
    confirm_html = f'<div class="confirm">Para confirmar: {html.escape(confirm)}</div>' if confirm else ""
    cat_html = (f'<div class="chip-cat"><span class="pt" style="background:{color}"></span>{html.escape(cat)}</div>'
                if cat else "")
    sci_html = f'<div class="dx-sci">{html.escape(ficha["cientifico"])}</div>' if ficha else ""

    aviso = ("Es una orientación a partir de lo que describiste, no un diagnóstico definitivo. "
             "Cualquier producto químico debe tener registro vigente (en Colombia, ICA); sigue siempre la etiqueta.")
    tarjeta = (
        '<div class="dx-wrap">' + cat_html +
        f'<div class="dx-name">{html.escape(dx)}</div>' + sci_html +
        '<div class="act-label">Acción recomendada</div>' +
        f'<div>{chips}</div>' + confirm_html +
        f'<div class="fine">{html.escape(aviso)}</div></div>'
    )
    st.markdown(tarjeta, unsafe_allow_html=True)

    if ficha:
        t1, t2, t3 = st.tabs(["Reconocerlo", "Qué hacer", "Prevenir"])
        with t1:
            st.markdown("<ul class='ficha'>" + "".join(f"<li>{html.escape(x)}</li>" for x in ficha["reconocer"]) + "</ul>",
                        unsafe_allow_html=True)
            st.markdown(f"**Por qué aparece.** {ficha['causa']}")
            st.markdown(f"**Se confunde con.** {ficha['confusion']}")
        with t2:
            st.markdown("<ol class='ficha'>" + "".join(f"<li>{html.escape(x)}</li>" for x in ficha["que_hacer"]) + "</ol>",
                        unsafe_allow_html=True)
        with t3:
            st.markdown("<ul class='ficha'>" + "".join(f"<li>{html.escape(x)}</li>" for x in ficha["prevencion"]) + "</ul>",
                        unsafe_allow_html=True)

    st.markdown('<div class="ia-title">Explicación personalizada</div>', unsafe_allow_html=True)
    mostrar_respuesta_ia(f"{clave_nodo}|hoja", prompt_hoja(historial), respuesta_offline_hoja)

    fuentes = fuentes_de(dx)
    if fuentes:
        with st.expander("Fuentes"):
            for titulo, url in fuentes:
                st.markdown(f"- [{titulo}]({url})")

    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2, _ = st.columns([1.2, 1.6, 2])
    with b1:
        if st.button("← Otra opción", key="nav_other"):
            st.session_state.historial.pop()
            st.rerun()
    with b2:
        if st.button("Nuevo diagnóstico", key="nav_new"):
            reiniciar_navegacion()
            st.rerun()
