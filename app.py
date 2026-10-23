import os
import re
import html
import zlib
import streamlit as st

from logica_arbol import (
    cargar_arbol, es_diagnostico, perfil_de, pregunta_de, trayecto_qa,
    prompt_pregunta, prompt_hoja, respuesta_offline_pregunta, respuesta_offline_hoja,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Árboles disponibles (nombre en pantalla -> archivo JSON)
ARBOLES = {
    "Diagnóstico de Rosas": "DiagnosticoRosas.json",
    "Estructuras de Datos No Lineales": "EstructurasDeDatos.json",
}
ICONO_ARBOL = {"diagnostico_rosas": "🌹"}

st.set_page_config(
    page_title="Explorador de Árboles con IA",
    page_icon="🌳",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-title {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 2.1rem; font-weight: 700;
        background: linear-gradient(90deg, #2563EB, #7C3AED);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title { color: #64748B; font-size: 1rem; margin-bottom: 1.5rem; }
    .breadcrumb-box {
        background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 0.75rem 1.2rem; margin-bottom: 1.5rem; display: flex; flex-wrap: wrap;
        align-items: center; gap: 0.5rem; font-size: 0.95rem;
    }
    @media (prefers-color-scheme: dark) {
        .breadcrumb-box { background-color: #1E293B; border-color: #334155; color: #F1F5F9; }
    }
    .breadcrumb-item { color: #2563EB; font-weight: 600; }
    .breadcrumb-sep { color: #94A3B8; font-weight: 400; }
    .question-card {
        background: #FFFFFF; border-radius: 14px; border: 1px solid #E2E8F0;
        padding: 1.5rem; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); margin-bottom: 1.5rem;
    }
    @media (prefers-color-scheme: dark) {
        .question-card { background: #0F172A; border-color: #1E293B; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3); }
    }
    .level-badge {
        display: inline-block; padding: 0.25rem 0.75rem; background-color: #EFF6FF; color: #1D4ED8;
        border-radius: 9999px; font-size: 0.8rem; font-weight: 600; margin-bottom: 0.6rem;
    }
    @media (prefers-color-scheme: dark) {
        .level-badge { background-color: #1E3A8A; color: #93C5FD; }
    }
    .dx-line { margin: 0.2rem 0; font-size: 1rem; }
</style>
""", unsafe_allow_html=True)


def a_html(texto):
    """Escapa HTML y convierte **negritas** simples."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(texto))


# -------------------------------------------------------------
# Estado de la sesión
# -------------------------------------------------------------
def reiniciar_navegacion():
    st.session_state.historial = [st.session_state.arbol] if st.session_state.arbol else []


def cargar_seleccion(nombre):
    arbol, error = cargar_arbol(os.path.join(BASE_DIR, ARBOLES[nombre]))
    st.session_state.arbol = arbol
    st.session_state.error_arbol = error
    st.session_state.arbol_cargado = nombre
    st.session_state.cache_ia = {}  # respuestas de la IA ya generadas
    reiniciar_navegacion()


# -------------------------------------------------------------
# Barra lateral
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🌲 Árbol")
    seleccion = st.selectbox("Árbol a explorar:", list(ARBOLES.keys()), key="seleccion_arbol")

if st.session_state.get("arbol_cargado") != seleccion:
    cargar_seleccion(seleccion)

with st.sidebar:
    st.markdown("### ⚙️ Configuración de la IA")
    modelo_ollama = st.text_input(
        "Modelo de Ollama:", value="llama3.2:1b",
        help="Nombre del modelo descargado localmente (ej: llama3.2:1b, llama3, mistral, gemma:2b)",
    )
    temperatura = st.slider("Creatividad (Temperatura):", 0.0, 1.0, 0.3, 0.1)
    ia_automatica = st.checkbox(
        "La IA responde cada pregunta automáticamente", value=True,
        help="Si la desactivas, aparecerá un botón para preguntarle a la IA cuando lo necesites.",
    )

    st.markdown("---")
    st.markdown("### 📂 Gestión del Árbol")
    if st.button("🔄 Recargar JSON", use_container_width=True, help="Vuelve a leer el archivo JSON"):
        cargar_seleccion(seleccion)
        st.toast("Árbol recargado correctamente", icon="✅")
        st.rerun()
    if st.button("⏪ Reiniciar Recorrido", use_container_width=True):
        reiniciar_navegacion()
        st.rerun()
    with st.expander("👀 Ver estructura del JSON activo"):
        if st.session_state.arbol:
            st.json(st.session_state.arbol)
        else:
            st.warning("No hay árbol cargado.")

# -------------------------------------------------------------
# Cabecera
# -------------------------------------------------------------
arbol = st.session_state.arbol
if st.session_state.error_arbol:
    st.error(st.session_state.error_arbol)
    st.stop()

perfil = perfil_de(arbol)
icono_titulo = ICONO_ARBOL.get(arbol.get("dominio"), "🌳")
st.markdown(f'<div class="main-title">{icono_titulo} {html.escape(arbol["valor"])}</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Navegación paso a paso y respuestas de la IA local con Ollama</div>',
            unsafe_allow_html=True)

historial = st.session_state.historial
if not historial:
    reiniciar_navegacion()
    historial = st.session_state.historial

nodo_actual = historial[-1]
nivel_actual = len(historial)
hijos = nodo_actual.get("hijos", [])
camino_titulos = [n["valor"] for n in historial]
clave_nodo = "|".join([seleccion] + camino_titulos)

# Breadcrumb
bc = '<div class="breadcrumb-box"><span>📍 <b>Ruta actual:</b></span> '
for idx, tit in enumerate(camino_titulos):
    if idx > 0:
        bc += '<span class="breadcrumb-sep">➔</span> '
    bc += f'<span class="breadcrumb-item">{html.escape(tit)}</span> '
bc += '</div>'
st.markdown(bc, unsafe_allow_html=True)

# Preguntas ya respondidas
pares = trayecto_qa(historial)
if pares:
    with st.expander(f"📝 Preguntas y respuestas hasta ahora ({len(pares)})"):
        for p, r in pares:
            st.markdown(f"**{p}**  \n➡️ {r}")


# -------------------------------------------------------------
# Componente: respuesta de la IA (con streaming, caché y modo offline)
# -------------------------------------------------------------
def mostrar_respuesta_ia(clave, prompt, offline_fn):
    cache = st.session_state.cache_ia
    clave = f"{clave}|{modelo_ollama}|{temperatura}"
    kb = f"regen_{zlib.crc32(clave.encode())}"

    if clave in cache:
        st.markdown(cache[clave])
        if st.button("🔄 Regenerar respuesta", key=kb):
            del cache[clave]
            st.rerun()
        return

    try:
        from importlib import import_module
        ollama = import_module("ollama")
        with st.spinner(f"Consultando a {modelo_ollama} vía Ollama..."):
            stream = ollama.chat(
                model=modelo_ollama,
                messages=[
                    {"role": "system", "content": perfil["sistema"]},
                    {"role": "user", "content": prompt},
                ],
                options={"temperature": temperatura},
                stream=True,
            )

            def generar_stream():
                for chunk in stream:
                    yield chunk["message"]["content"]

            cache[clave] = st.write_stream(generar_stream)
    except Exception as e:  # noqa: BLE001
        st.error("⚠️ No se pudo comunicar con el servidor local de Ollama.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 Reintentar conexión con Ollama", use_container_width=True, key=f"retry_{kb}"):
                st.rerun()
        with c2:
            if st.button("💡 Ver respuesta de prueba (Modo Offline)", use_container_width=True, key=f"off_{kb}"):
                cache[clave] = offline_fn(historial)
                st.rerun()
        with st.expander("🛠️ ¿Cómo solucionarlo?"):
            st.markdown(f"""
1. **Verifica que Ollama esté iniciado**: abre una terminal y ejecuta `ollama serve`
   (o abre la aplicación de escritorio de **Ollama**).
2. **Verifica tener el modelo `{modelo_ollama}`**: ejecuta `ollama pull {modelo_ollama}`.

**Detalle del error técnico:** `{e}`
""")


# -------------------------------------------------------------
# Pantalla de PREGUNTA (nodo con hijos)
# -------------------------------------------------------------
if hijos:
    pregunta_texto = pregunta_de(nodo_actual, nivel_actual)

    st.markdown(f"""
    <div class="question-card">
        <span class="level-badge">Paso {nivel_actual}</span>
        <h3 style="margin-top:0.3rem; margin-bottom:0.5rem; font-weight:600;">{a_html(pregunta_texto)}</h3>
        <p style="color:#64748B; font-size:0.9rem; margin-bottom:0;">Selecciona una opción para continuar el recorrido:</p>
    </div>
    """, unsafe_allow_html=True)

    # Opciones de respuesta
    ncols = 2 if any(len(h.get("valor", "")) > 28 for h in hijos) else min(len(hijos), 3)
    cols = st.columns(max(1, min(ncols, len(hijos))))
    for i, hijo in enumerate(hijos):
        etiqueta = hijo.get("valor", f"Opción {i+1}")
        if es_diagnostico(hijo):
            icono = "🩺"
        else:
            icono = "📁" if hijo.get("hijos") else "📄"
        if cols[i % len(cols)].button(f"{icono} {etiqueta}", key=f"btn_{zlib.crc32(clave_nodo.encode())}_{i}", use_container_width=True):
            st.session_state.historial.append(hijo)
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    n1, n2, _ = st.columns([1, 1, 2])
    with n1:
        if nivel_actual > 1 and st.button("⬅️ Paso anterior", use_container_width=True):
            st.session_state.historial.pop()
            st.rerun()
    with n2:
        if nivel_actual > 1 and st.button("🔄 Desde el inicio", use_container_width=True):
            reiniciar_navegacion()
            st.rerun()

    # La IA responde exactamente la pregunta del árbol
    st.markdown("---")
    st.subheader("🤖 Respuesta de la IA a esta pregunta")
    st.caption(f"Pregunta del árbol: {pregunta_texto.replace('**', '')}")
    clave_ia = f"{clave_nodo}|pregunta"
    ya_generada = any(k.startswith(clave_ia + "|") for k in st.session_state.cache_ia)
    flag_pedir = f"pedir_{clave_nodo}"
    if ia_automatica or ya_generada or st.session_state.get(flag_pedir):
        mostrar_respuesta_ia(clave_ia, prompt_pregunta(historial), respuesta_offline_pregunta)
    elif st.button("🤖 Preguntarle a la IA", key=f"ask_{zlib.crc32(clave_nodo.encode())}"):
        st.session_state[flag_pedir] = True
        st.rerun()

# -------------------------------------------------------------
# Pantalla FINAL (hoja)
# -------------------------------------------------------------
else:
    if es_diagnostico(nodo_actual):
        confirm = ""
        if nodo_actual.get("pregunta_confirmacion"):
            confirm = (f'<p class="dx-line">❓ <b>Pregunta de confirmación:</b> '
                       f'{html.escape(nodo_actual["pregunta_confirmacion"])}</p>')
        st.markdown(f"""
        <div class="question-card" style="border-left: 5px solid #10B981;">
            <span class="level-badge" style="background-color: #D1FAE5; color: #047857;">Diagnóstico</span>
            <h3 style="margin-top: 0.3rem; margin-bottom: 0.6rem;">🩺 {html.escape(nodo_actual['diagnostico'])}</h3>
            {confirm}
            <p class="dx-line">✅ <b>Acción:</b> <i>{html.escape(nodo_actual['accion'])}</i></p>
        </div>
        """, unsafe_allow_html=True)
        titulo_ia = ".." \
        "Explicación de la IA sobre el diagnóstico"
    else:
        st.markdown(f"""
        <div class="question-card" style="border-left: 5px solid #10B981;">
            <span class="level-badge" style="background-color: #D1FAE5; color: #047857;">Nivel Final Alcanzado</span>
            <h3 style="margin-top: 0.3rem; margin-bottom: 0.5rem;">Concepto: <b>{html.escape(nodo_actual['valor'])}</b></h3>
            <p style="color: #64748B; font-size: 0.9rem; margin-bottom: 0;">
                Has llegado al final de este ramal. A continuación se genera la explicación con el modelo local de IA.
            </p>
        </div>
        """, unsafe_allow_html=True)
        titulo_ia = f"🤖 Explicación del modelo local ({modelo_ollama})"

    b1, b2, _ = st.columns([1, 1, 2])
    with b1:
        if st.button("⬅️ Elegir otra opción", use_container_width=True):
            st.session_state.historial.pop()
            st.rerun()
    with b2:
        if st.button("🔄 Reiniciar exploración", use_container_width=True):
            reiniciar_navegacion()
            st.rerun()

    st.markdown("---")
    st.subheader(titulo_ia)
    mostrar_respuesta_ia(f"{clave_nodo}|hoja", prompt_hoja(historial), respuesta_offline_hoja)
