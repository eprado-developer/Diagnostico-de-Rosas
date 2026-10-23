# 🌳🌹 Explorador Dinámico de Árboles con IA (Ollama + Streamlit)

Aplicación interactiva desarrollada en Python para la materia **Estructuras de Datos No Lineales** (Colegio Mayor del Cauca). Permite navegar jerárquicamente por un árbol paso a paso. Incluye dos árboles: **Estructuras de Datos No Lineales** y el nuevo **Diagnóstico de Rosas** (basado en `docs/Diagrama_de_arbol.jpeg`). En **cada pregunta** del árbol, un modelo de lenguaje local (**Ollama**) responde exactamente esa pregunta; en la hoja final explica el diagnóstico o concepto en tiempo real.

---

## 🚀 Puesta en Marcha Rápida

### 1. Requisitos Previos
* **Python 3.10+** (si no tienes el entorno `.venv-1`, crea uno e instala `pip install -r requirements.txt`).
* **Ollama**: Descargado e instalado desde [ollama.com](https://ollama.com/).
* Modelo local de Ollama descargado (por defecto: `llama3.2:1b`):
  ```bash
  ollama run llama3.2:1b
  ```

---

### 2. Ejecutar la Aplicación

Abre una terminal (PowerShell o CMD) en la carpeta del proyecto y ejecuta:

```powershell
.\.venv-1\Scripts\streamlit.exe run app.py
```

> **Nota:** Si tienes el entorno virtual activado, también puedes ejecutar simplemente:
> ```bash
> streamlit run app.py
> ```

---

### 3. Acceder al Entorno Gráfico

Una vez ejecutado el comando anterior, la consola mostrará la URL local. Abre tu navegador web favorito (Chrome, Edge, Firefox, etc.) e ingresa a:

👉 **[http://localhost:8501/](http://localhost:8501/)**

---

## 🌹 Árbol de Diagnóstico de Rosas

Archivo: **`DiagnosticoRosas.json`** (transcripción fiel del diagrama `docs/Diagrama_de_arbol.jpeg`).

* **Raíz**: `¿Qué tipo de rosa tienes?` → Rosales de Té / Corte, Arbustivos / Paisajísticos, Trepadores, Miniatura / Maceta.
* **Preguntas del árbol** (texto exacto del diagrama): `Parte afectada?`, `¿Suelo encharcado y marcha?`, `¿Presenta moho velloso/gris?`, `¿Tiene plaga o manchas?`, `¿Pequeños verdes/negros en brotes?`, `¿Deformación por plaga?`, `¿Síntomas visuales?`, `¿Manchas en superficie?`, `¿Alteración de color / insectos?`, `¿Compactación o exceso de riego?`.
* **14 diagnósticos** (Pudrición Radicular, Botritis en flor, Trips, Oídio, Chancro / Botritis, Pulgón, Orugas / Gusanos, Roya, Mancha Negra, Deficiencia de Potasio, Deficiencia de Nitrógeno, Araña Roja, Clorosis Férrica, Asfixia Radicular / Estrés Hídrico), cada uno con su **acción** recomendada.
* Los nodos compartidos del diagrama (*Pulgón* y *¿Alteración de color / insectos?*) están repetidos en cada rama donde aparecen.

### ¿Cómo responde la IA?

1. **En cada pregunta**: la IA recibe el texto exacto de la pregunta, las opciones del árbol y las respuestas ya dadas; explica qué se pregunta y cómo distinguir cada opción (sin inventar opciones ni diagnosticar antes de tiempo). Se puede desactivar el modo automático en la barra lateral para usar un botón **`🤖 Preguntarle a la IA`**.
2. **En la hoja (diagnóstico)**: se muestra el diagnóstico y la acción **tal como están en el árbol** y la IA explica qué es, cómo aplicar la acción y cómo prevenirlo.
3. **Modo offline**: si Ollama no está activo, el botón de prueba muestra la información tomada directamente del árbol.

---

## 🧠 ¿Cómo Funciona la Aplicación?

1. **Navegación Paso a Paso**:
   * No satura la pantalla con todo el diagrama. En su lugar, muestra **una pregunta por pantalla** correspondiente al nivel actual.
   * Cada opción muestra un icono de carpeta (`📁`) si tiene más subcategorías o de documento (`📄`) si es un concepto final.

2. **Ruta Actual (Miga de pan / Breadcrumb)**:
   * En la parte superior siempre visualizas el camino recorrido (ejemplo: `Estructuras de Datos No Lineales ➔ Arboles ➔ Recorridos ➔ InOrden`).

3. **Explicación con IA en el Último Nivel**:
   * Al seleccionar un nodo hoja (sin más hijos), la app genera automáticamente un prompt contextual y consulta a Ollama con efecto de escritura en vivo (*streaming*).

4. **Controles de Navegación**:
   * **`⬅️ Paso anterior`**: Retrocede un nivel en la jerarquía.
   * **`🔄 Desde el inicio`**: Regresa a la raíz del árbol.
   * **`🔄 Regenerar respuesta`**: Solicita una nueva explicación a la IA.

---

## ⚡ Modificar el Árbol Dinámicamente (`EstructurasDeDatos.json`)

El programa **no tiene rutas fijas en el código Python**; lee y construye las preguntas directamente del archivo `EstructurasDeDatos.json`.

### Estructura de un Nodo:
```json
{
  "valor": "Nombre de la categoría o concepto",
  "pregunta": "¿Pregunta que se formula en este nodo?",
  "hijos": [
    {
      "valor": "Subtema 1"
    },
    {
      "valor": "Subtema 2",
      "hijos": [ ... ]
    }
  ]
}
```

* `valor`: la **opción** con la que se llega al nodo (lo que el usuario pulsó).
* `pregunta`: la **pregunta** que se hace en el nodo; sus `hijos` son las opciones de respuesta.
* Hojas de diagnóstico: `diagnostico`, `accion` y, opcionalmente, `pregunta_confirmacion`.
* Raíz: `dominio` (`diagnostico_rosas` o `estructuras_datos`) elige el perfil de la IA en `logica_arbol.py`.

### ¿Cómo agregar nuevas ramas?
1. Abre `DiagnosticoRosas.json` o `EstructurasDeDatos.json` y agrega o modifica cualquier categoría (por ejemplo, añadir *Árboles AVL*, *Árboles B*, *Colas de Prioridad*, etc.).
2. Guarda el archivo `.json`.
3. En la barra lateral de la aplicación web, haz clic en **`🔄 Recargar JSON`**.
4. ¡Listo! La nueva opción y sus preguntas aparecerán de inmediato en el menú sin reiniciar el servidor.

---

## ⚠️ Consideraciones Importantes

* **Servicio de Ollama Activo**: Para que la IA responda, el servicio de Ollama debe estar en ejecución en tu equipo. Si la aplicación muestra un error de conexión:
  1. Abre una terminal y ejecuta `ollama serve` (o asegúrate de que la app de Ollama esté abierta en la barra de tareas de Windows).
  2. Haz clic en el botón **`🔄 Reintentar conexión con Ollama`** en la página web.
* **Modo Demostrativo Offline**: Si vas a exponer el proyecto en un equipo donde no esté instalado Ollama o no haya recursos suficientes, la aplicación incluye un botón:  
  **`💡 Ver explicación de prueba (Modo Offline)`**, el cual genera una respuesta didáctica simulada para que la presentación nunca falle.
* **Cambio de Modelo**: En la barra lateral puedes cambiar el modelo de Ollama en cualquier momento (ej: `llama3`, `mistral`, `gemma:2b`, etc.) y regular la creatividad con el deslizador de *Temperatura*.

---

## 📁 Estructura de Archivos del Proyecto

| Archivo | Descripción |
| :--- | :--- |
| **`app.py`** | Interfaz gráfica interactiva y dinámica desarrollada en Streamlit. |
| **`logica_arbol.py`** | Lógica sin interfaz: carga del JSON, prompts de la IA y respuestas offline. |
| **`DiagnosticoRosas.json`** | 🌹 Árbol de diagnóstico de rosas (según el diagrama). |
| **`EstructurasDeDatos.json`** | Árbol original de Estructuras de Datos No Lineales. |
| **`docs/Diagrama_de_arbol.jpeg`** | Diagrama de origen del árbol de rosas. |
| **`requirements.txt`** | Dependencias (`streamlit`, `ollama`). |
| **`ApiLocal.py`** | Versión de consola: elige árbol y la IA responde cada pregunta. |
| **`ApiLLM.py`** | Script base de prueba para la librería de Ollama. |
| **`.venv-1/`** | *(No incluido en este zip por su tamaño.)* Usa tu entorno existente o crea uno nuevo con `pip install -r requirements.txt`. |
| **`README.md`** | Guía de uso, consideraciones y documentación técnica del proyecto. |
