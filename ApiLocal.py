"""Versión de consola: recorre un árbol JSON y la IA (Ollama) responde cada pregunta."""
import sys
import ollama

from logica_arbol import (
    cargar_arbol, es_hoja, es_diagnostico, perfil_de, pregunta_de,
    prompt_pregunta, prompt_hoja, respuesta_offline_pregunta, respuesta_offline_hoja,
)

MODELO = "rosas-experto"
ARBOL = "DiagnosticoRosas.json"


def preguntar_ia(sistema, prompt, offline):
    try:
        r = ollama.chat(model=MODELO, options={"temperature": 0.3}, messages=[
            {"role": "system", "content": sistema}, {"role": "user", "content": prompt}])
        return r["message"]["content"]
    except Exception as e:  # noqa: BLE001
        return f"[Ollama no disponible: {e}]\n\n{offline}"


def explorar():
    arbol, error = cargar_arbol(ARBOL)
    if error:
        print("Error:", error)
        return
    sistema = perfil_de(arbol)["sistema"]
    historial = [arbol]

    while True:
        nodo = historial[-1]
        print("\n" + "=" * 40)
        print(" UBICACIÓN:", " > ".join(n["valor"] for n in historial))
        print("=" * 40)

        if es_hoja(nodo):
            if es_diagnostico(nodo):
                print(f"\n🩺 DIAGNÓSTICO: {nodo['diagnostico']}\n✅ ACCIÓN: {nodo['accion']}")
                if nodo.get("pregunta_confirmacion"):
                    print(f"❓ {nodo['pregunta_confirmacion']}")
            print("\n[Ollama] Generando explicación local...")
            print("\nEXPLICACIÓN:\n" + preguntar_ia(sistema, prompt_hoja(historial), respuesta_offline_hoja(historial)))
            break

        pregunta = pregunta_de(nodo, len(historial)).replace("**", "")
        print(f"\n❓ {pregunta}")
        print("\n[Ollama] Respondiendo la pregunta...")
        print(preguntar_ia(sistema, prompt_pregunta(historial), respuesta_offline_pregunta(historial)))

        hijos = nodo["hijos"]
        print("\nSelecciona una opción:")
        for i, h in enumerate(hijos, 1):
            print(f"{i}. {h['valor']}")
        while True:
            idx = input("\nNúmero > ")
            if idx.isdigit() and 1 <= int(idx) <= len(hijos):
                historial.append(hijos[int(idx) - 1])
                break
            print("Opción inválida.")


if __name__ == "__main__":
    explorar()
