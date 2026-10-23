"""
Lógica pura del explorador de árboles (sin Streamlit), para poder probarla
y reutilizarla tanto en la app gráfica como en la versión de consola.

Convención del JSON
-------------------
Cada nodo es un diccionario:

    {
      "valor":    "Texto de la opción con la que se LLEGA a este nodo",
      "pregunta": "Pregunta que se formula EN este nodo (opcional)",
      "hijos":    [ ...opciones de respuesta... ],

      # Solo en hojas del árbol de rosas:
      "diagnostico": "Nombre del diagnóstico",
      "accion": "Acción recomendada",
      "pregunta_confirmacion": "Pregunta interna de la hoja (opcional)"
    }

El nodo raíz puede traer "dominio" para elegir el perfil de la IA.
"""
import json
import os

# ---------------------------------------------------------------------------
# Perfiles de IA por dominio
# ---------------------------------------------------------------------------
PERFILES = {
    "diagnostico_rosas": {
        "sistema": (
            "Eres un ingeniero agrónomo experto en rosales y fitopatología. "
            "Respondes siempre en español, de forma clara, práctica y breve. "
            "Te ciñes estrictamente a las preguntas y opciones del árbol de decisión "
            "que se te entrega: no inventas opciones nuevas ni cambias el texto de las preguntas."
        ),
        "tema": "diagnóstico de problemas en rosales",
    },
    "estructuras_datos": {
        "sistema": (
            "Eres un profesor universitario experto en Estructuras de Datos y Algoritmos. "
            "Responde con explicaciones claras, ordenadas y didácticas en español."
        ),
        "tema": "estructuras de datos no lineales",
    },
}
PERFIL_POR_DEFECTO = "estructuras_datos"


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
    """Lista de todas las preguntas textuales del árbol (incluye las de confirmación)."""
    out = []
    for nodo, _ in recorrer(arbol):
        if nodo.get("pregunta"):
            out.append(nodo["pregunta"])
        if nodo.get("pregunta_confirmacion"):
            out.append(nodo["pregunta_confirmacion"])
    return out


# ---------------------------------------------------------------------------
# Texto de la pregunta que se muestra en pantalla
# ---------------------------------------------------------------------------
def pregunta_de(nodo, nivel):
    """Pregunta exacta del JSON; si no existe, una genérica (compatibilidad con árbol antiguo)."""
    if nodo.get("pregunta"):
        return nodo["pregunta"]
    if nivel == 1:
        return f"¿Qué categoría principal de **{nodo['valor']}** deseas explorar?"
    return f"Dentro de **{nodo['valor']}**, ¿qué sub-rama o concepto quieres consultar?"


def trayecto_qa(historial):
    """
    Pares (pregunta, respuesta) ya contestados por el usuario.
    La respuesta a la pregunta del nodo i es el 'valor' del nodo i+1.
    """
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
# Prompts para la IA
# ---------------------------------------------------------------------------
def prompt_pregunta(historial):
    """
    La IA responde EXACTAMENTE la pregunta del nodo actual: explica qué
    significa y cómo reconocer cada una de las opciones que ofrece el árbol.
    """
    nodo = historial[-1]
    opciones = [h["valor"] for h in nodo.get("hijos", [])]
    pregunta = nodo.get("pregunta") or pregunta_de(nodo, len(historial)).replace("**", "")
    lista = "\n".join(f"  {i}. {o}" for i, o in enumerate(opciones, 1))
    return (
        f"Estás ayudando en un sistema de {perfil_de(historial[0])['tema']} basado en un árbol de decisión.\n\n"
        f"Respuestas ya dadas por el usuario:\n{_formatear_trayecto(historial)}\n\n"
        f"PREGUNTA ACTUAL DEL ÁRBOL (texto exacto): «{pregunta}»\n"
        f"OPCIONES DE RESPUESTA DISPONIBLES:\n{lista}\n\n"
        "Responde exactamente a esa pregunta: explica qué se está preguntando y cómo reconocer "
        "o distinguir cada una de las opciones listadas (qué observar, señales claras). "
        "Usa únicamente las opciones listadas, no agregues otras ni emitas aún un diagnóstico final. "
        "Máximo 120 palabras, con una viñeta corta por opción."
    )


def prompt_hoja(historial):
    """Explicación completa de la hoja (diagnóstico de rosas o concepto de estructuras de datos)."""
    nodo = historial[-1]
    camino = [n["valor"] for n in historial]
    if es_diagnostico(nodo):
        extra = ""
        if nodo.get("pregunta_confirmacion"):
            extra = (
                f"Pregunta de confirmación del árbol (texto exacto): «{nodo['pregunta_confirmacion']}». "
                "Respóndela primero, indicando qué señales confirman el diagnóstico.\n"
            )
        return (
            "Sistema de diagnóstico de rosales. El usuario recorrió el árbol de decisión así:\n"
            f"{_formatear_trayecto(historial)}\n\n"
            f"DIAGNÓSTICO FINAL DEL ÁRBOL: {nodo['diagnostico']}\n"
            f"ACCIÓN RECOMENDADA POR EL ÁRBOL: {nodo['accion']}\n\n"
            f"{extra}"
            "Explica en español y de forma práctica: 1) Qué es este problema y por qué aparece, "
            "2) Cómo aplicar paso a paso la acción recomendada, 3) Cómo prevenirlo. "
            "Respeta el diagnóstico y la acción del árbol; no los cambies. Máximo 200 palabras."
        )
    return (
        f"Explícame qué es '{nodo['valor']}' en el contexto de {camino[0]}. "
        f"La ruta completa en la jerarquía es: {' > '.join(camino)}. "
        "Estructura tu respuesta con: 1) Definición concisa, 2) Características principales o cómo funciona, "
        "y 3) Un ejemplo breve o caso de uso. Sé claro y pedagógico."
    )


# ---------------------------------------------------------------------------
# Respuestas de respaldo (modo offline, sin Ollama): salen del propio árbol
# ---------------------------------------------------------------------------
def respuesta_offline_pregunta(historial):
    nodo = historial[-1]
    pregunta = nodo.get("pregunta") or pregunta_de(nodo, len(historial)).replace("**", "")
    opciones = "\n".join(f"* {h['valor']}" for h in nodo.get("hijos", []))
    return (
        f"### 📘 {pregunta}\n\n"
        "Modo offline: la IA no está disponible, pero estas son las respuestas posibles "
        f"en el árbol:\n\n{opciones}\n\n"
        "_Inicia Ollama (`ollama serve`) para obtener la explicación de la IA._"
    )


def respuesta_offline_hoja(historial):
    nodo = historial[-1]
    camino = [n["valor"] for n in historial]
    if es_diagnostico(nodo):
        texto = (
            f"### 📘 {nodo['diagnostico']}\n\n"
            f"* **Acción recomendada**: {nodo['accion']}\n"
            f"* **Recorrido**: `{' > '.join(camino)}`\n"
        )
        if nodo.get("pregunta_confirmacion"):
            texto += f"* **Pregunta de confirmación**: {nodo['pregunta_confirmacion']}\n"
        return texto + "\n_Esta es una respuesta de prueba sin IA. Inicia Ollama para la explicación completa._"
    padre = camino[-2] if len(camino) > 1 else "Estructura"
    return (
        f"### 📘 Explicación demostrativa: {nodo['valor']}\n\n"
        f"* **Jerarquía**: `{' > '.join(camino)}`\n"
        f"* **Definición**: En ciencias de la computación, `{nodo['valor']}` es un componente esencial "
        "dentro de las estructuras de datos.\n"
        f"* **Funcionamiento**: Permite organizar, gestionar y optimizar el acceso a la información según "
        f"las reglas de su categoría padre (`{padre}`).\n"
        "* **Nota**: Esta es una respuesta de prueba local. Para obtener la explicación generada por la IA "
        "en tiempo real, inicia Ollama en tu computadora (`ollama serve`)."
    )
