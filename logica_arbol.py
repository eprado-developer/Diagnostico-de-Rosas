"""
Lógica pura del explorador de rosas (sin Streamlit): carga y validación del
árbol, prompts para la IA y respuestas de respaldo sin Ollama.

Convención del JSON
-------------------
    {
      "valor":    "Texto de la opción con la que se LLEGA a este nodo",
      "pregunta": "Pregunta que se formula EN este nodo (opcional)",
      "hijos":    [ ...opciones de respuesta... ],

      # Solo en hojas:
      "diagnostico": "Nombre del diagnóstico",
      "accion": "Acción recomendada",
      "pregunta_confirmacion": "Pregunta interna de la hoja (opcional)"
    }

El conocimiento (fichas, pistas, fuentes, prompt) vive en conocimiento_rosas.py.
"""
import json
import os

from conocimiento_rosas import (
    CATEGORIAS, FICHAS, FUENTES, PISTAS, PROMPT_SISTEMA,
)

# ---------------------------------------------------------------------------
# Perfil de IA (la app envía este system prompt; el Modelfile usa el mismo)
# ---------------------------------------------------------------------------
PERFILES = {
    "diagnostico_rosas": {
        "sistema": PROMPT_SISTEMA,
        "tema": "diagnóstico de problemas en rosales",
    },
}
PERFIL_POR_DEFECTO = "diagnostico_rosas"


def perfil_de(arbol):
    return PERFILES.get(arbol.get("dominio", PERFIL_POR_DEFECTO), PERFILES[PERFIL_POR_DEFECTO])


# ---------------------------------------------------------------------------
# Carga y validación
# ---------------------------------------------------------------------------
def cargar_arbol(ruta_archivo):
    """Devuelve (arbol, error). Si todo va bien error es None."""
    if not os.path.exists(ruta_archivo):
        return None, f"No se encontró el archivo '{ruta_archivo}'."
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except json.JSONDecodeError as e:
        return None, f"Error al decodificar JSON: {e}"
    except Exception as e:  # noqa: BLE001
        return None, f"Error al leer archivo: {e}"
    if not isinstance(datos, dict) or "valor" not in datos:
        return None, "El formato del JSON debe contener al menos un nodo raíz con la clave 'valor'."
    return datos, None


def es_hoja(nodo):
    return not nodo.get("hijos")


def es_diagnostico(nodo):
    return "diagnostico" in nodo


def recorrer(nodo, camino=()):
    """Genera (nodo, camino_de_valores) para todo el árbol, en preorden."""
    camino = camino + (nodo["valor"],)
    yield nodo, camino
    for h in nodo.get("hijos", []):
        yield from recorrer(h, camino)


def preguntas_del_arbol(arbol):
    out = []
    for nodo, _ in recorrer(arbol):
        if nodo.get("pregunta"):
            out.append(nodo["pregunta"])
        if nodo.get("pregunta_confirmacion"):
            out.append(nodo["pregunta_confirmacion"])
    return out


def validar_arbol(arbol):
    """Avisos útiles al editar el JSON: diagnósticos sin ficha, hojas sin diagnóstico, etc."""
    avisos = []
    for nodo, camino in recorrer(arbol):
        ruta = " > ".join(camino)
        if es_hoja(nodo) and not es_diagnostico(nodo):
            avisos.append(f"Hoja sin diagnóstico: {ruta}")
        if es_diagnostico(nodo) and nodo["diagnostico"] not in FICHAS:
            avisos.append(f"Sin ficha técnica para «{nodo['diagnostico']}» (añádela en conocimiento_rosas.py)")
    return avisos


def profundidad_restante(nodo):
    """Número de preguntas que faltan (incluida la del nodo actual) por la rama más larga."""
    if es_hoja(nodo):
        return 0
    return 1 + max(profundidad_restante(h) for h in nodo["hijos"])


# ---------------------------------------------------------------------------
# Conocimiento
# ---------------------------------------------------------------------------
def ficha_de(diagnostico):
    return FICHAS.get(diagnostico)


def categoria_de(diagnostico):
    f = ficha_de(diagnostico)
    return CATEGORIAS.get(f["categoria"], "") if f else ""


def pista_de(valor):
    return PISTAS.get(valor, "")


def fuentes_de(diagnostico):
    f = ficha_de(diagnostico)
    if not f:
        return []
    return [FUENTES[k] for k in f.get("fuentes", []) if k in FUENTES] + [FUENTES["ica"]]


def ficha_como_texto(diagnostico):
    """Ficha compacta para inyectar en el prompt (el modelo pequeño se apoya en ella)."""
    f = ficha_de(diagnostico)
    if not f:
        return "(sin ficha técnica disponible)"
    return (
        f"Nombre científico / agente: {f['cientifico']}\n"
        f"Cómo reconocerlo: {' '.join(f['reconocer'])}\n"
        f"Causa: {f['causa']}\n"
        f"Se confunde con: {f['confusion']}\n"
        f"Qué hacer: {' '.join(f['que_hacer'])}\n"
        f"Prevención: {' '.join(f['prevencion'])}"
    )


# ---------------------------------------------------------------------------
# Texto de la pregunta
# ---------------------------------------------------------------------------
def pregunta_de(nodo, nivel):
    if nodo.get("pregunta"):
        return nodo["pregunta"]
    return f"Dentro de **{nodo['valor']}**, ¿qué opción coincide con lo que ves?"


def trayecto_qa(historial):
    """Pares (pregunta, respuesta) ya contestados; la respuesta a la pregunta i es el valor del nodo i+1."""
    pares = []
    for i in range(len(historial) - 1):
        preg = historial[i].get("pregunta")
        if preg:
            pares.append((preg, historial[i + 1]["valor"]))
    return pares


def _formatear_trayecto(historial):
    pares = trayecto_qa(historial)
    if not pares:
        return "(todavía no se ha respondido ninguna pregunta)"
    return "\n".join(f"- {p}  →  {r}" for p, r in pares)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
def prompt_pregunta(historial):
    nodo = historial[-1]
    pregunta = nodo.get("pregunta") or pregunta_de(nodo, len(historial)).replace("**", "")
    lineas = []
    for i, h in enumerate(nodo.get("hijos", []), 1):
        pista = pista_de(h["valor"])
        lineas.append(f"  {i}. {h['valor']}" + (f"  (pista: {pista})" if pista else ""))
    return (
        f"Contexto: sistema de {perfil_de(historial[0])['tema']} basado en un árbol de decisión.\n\n"
        f"Respuestas ya dadas por el usuario:\n{_formatear_trayecto(historial)}\n\n"
        f"PREGUNTA ACTUAL DEL ÁRBOL (texto exacto): «{pregunta}»\n"
        f"OPCIONES DISPONIBLES:\n" + "\n".join(lineas) + "\n\n"
        "Tarea: explica qué se está preguntando y cómo reconocer cada opción listada "
        "(qué observar, señales claras). Usa SOLO esas opciones; no añadas otras ni des "
        "todavía un diagnóstico final. Una viñeta corta por opción, máximo 120 palabras."
    )


def prompt_hoja(historial):
    nodo = historial[-1]
    extra = ""
    if nodo.get("pregunta_confirmacion"):
        extra = (
            f"Pregunta de confirmación del árbol (texto exacto): «{nodo['pregunta_confirmacion']}». "
            "Respóndela primero, indicando qué señales la confirman.\n"
        )
    return (
        "El usuario recorrió el árbol de decisión así:\n"
        f"{_formatear_trayecto(historial)}\n\n"
        f"DIAGNÓSTICO DEL ÁRBOL: {nodo['diagnostico']}\n"
        f"ACCIÓN DEL ÁRBOL: {nodo['accion']}\n\n"
        f"FICHA TÉCNICA (úsala como base, no la contradigas):\n{ficha_como_texto(nodo['diagnostico'])}\n\n"
        f"{extra}"
        "Tarea: explica en español y de forma práctica: 1) qué es y por qué aparece, "
        "2) cómo aplicar paso a paso la acción, 3) cómo prevenirlo, y 4) una señal para "
        "confirmar que el diagnóstico es correcto (esto es una orientación, no un diagnóstico "
        "definitivo). No cambies el diagnóstico ni inventes dosis. Máximo 200 palabras."
    )


# ---------------------------------------------------------------------------
# Respuestas de respaldo (sin Ollama): salen del propio árbol y de las fichas
# ---------------------------------------------------------------------------
def respuesta_offline_pregunta(historial):
    nodo = historial[-1]
    pregunta = nodo.get("pregunta") or pregunta_de(nodo, len(historial)).replace("**", "")
    filas = []
    for h in nodo.get("hijos", []):
        pista = pista_de(h["valor"])
        filas.append(f"* **{h['valor']}**" + (f" — {pista}" if pista else ""))
    return (
        f"**{pregunta}**\n\n" + "\n".join(filas) +
        "\n\n_Modo sin IA: estas pistas salen del propio árbol. "
        "Inicia Ollama (`ollama serve`) para una explicación personalizada._"
    )


def respuesta_offline_hoja(historial):
    nodo = historial[-1]
    f = ficha_de(nodo["diagnostico"])
    texto = f"**{nodo['diagnostico']}**\n\n* **Acción recomendada:** {nodo['accion']}\n"
    if f:
        texto += (
            f"* **Cómo reconocerlo:** {' '.join(f['reconocer'])}\n"
            f"* **Por qué aparece:** {f['causa']}\n"
            f"* **Prevención:** {' '.join(f['prevencion'])}\n"
        )
    if nodo.get("pregunta_confirmacion"):
        texto += f"* **Para confirmar:** {nodo['pregunta_confirmacion']}\n"
    return texto + "\n_Modo sin IA: ficha técnica de la base de conocimiento._"
