# 🌹 Rosal · Diagnóstico de rosas con IA local

**Edwin Prado & Dana Huaca** · Estructuras de Datos No Lineales · Colegio Mayor del Cauca

App en Streamlit que recorre un árbol de decisión (`DiagnosticoRosas.json`, basado en `docs/Diagrama_de_arbol.jpeg`) y apoya cada paso con una IA local (Ollama) **limitada exclusivamente al mundo de las rosas**.

## Puesta en marcha

```bash
pip install -r requirements.txt

# 1) Crear el modelo especializado (una vez, y cada vez que edites el conocimiento)
python generar_modelfile.py
ollama create rosas-experto -f Modelfile

# 2) Ejecutar
streamlit run app.py
```

Sin Ollama la app funciona igual: muestra la ficha técnica y las pistas de cada opción; la IA solo añade una explicación personalizada.

## Estructura

| Archivo | Para qué sirve |
| :-- | :-- |
| `app.py` | Interfaz minimalista (una pregunta por pantalla, progreso, ficha del diagnóstico). |
| `conocimiento_rosas.py` | **Fuente única de conocimiento**: fichas de los 14 diagnósticos, pistas de cada opción, fuentes y *system prompt*. |
| `logica_arbol.py` | Carga/validación del árbol, prompts (inyectan la ficha técnica) y respuestas sin IA. |
| `generar_modelfile.py` | Genera el `Modelfile` desde `conocimiento_rosas.py` para que app y modelo no se desincronicen. |
| `Modelfile` | Generado: parámetros, system prompt con base de conocimiento y ejemplos (incluye rechazo de temas ajenos). |
| `DiagnosticoRosas.json` | El árbol. |
| `ApiLocal.py` | Versión de consola. |
| `.streamlit/config.toml` | Tema de colores. |

## Cómo se mantiene la IA enfocada en rosas

1. **System prompt con ámbito obligatorio**: ante cualquier tema ajeno responde una frase fija y vuelve al diagnóstico.
2. **Ejemplos (few-shot) en el Modelfile**: un caso correcto y dos intentos fuera de tema.
3. **Ficha técnica inyectada en cada prompt**: el modelo de 1B se apoya en datos curados, no solo en su memoria.
4. **El árbol manda**: la IA no cambia el diagnóstico ni la acción, no inventa dosis y distingue síntoma de diagnóstico confirmado.
5. **Parámetros estables**: temperatura 0.2, `repeat_penalty` 1.15, contexto 4096.

> Con un modelo de 1B el enfoque es robusto pero no infalible. Para más precisión, cambia `BASE` en `generar_modelfile.py` a un modelo mayor (p. ej. `llama3.2:3b`).

## Ampliar el conocimiento

1. Edita `FICHAS`, `PISTAS` o `FUENTES` en `conocimiento_rosas.py`.
2. `python generar_modelfile.py && ollama create rosas-experto -f Modelfile`
3. En la app: **Ajustes → Recargar JSON**. El panel avisa si un diagnóstico del árbol no tiene ficha.

## Fuentes

- UC IPM (Univ. de California) · *Roses: Diseases and Abiotic Disorders*, Pest Notes 7463: https://ipm.ucanr.edu/home-and-landscape/roses-diseases-and-abiotic-disorders/
- UC IPM · Black spot: https://ipm.ucanr.edu/PMG/GARDEN/PLANTS/DISEASES/blackspot.html
- UC IPM · Rosa spp., Floriculture and Ornamental Nurseries: https://ipm.ucanr.edu/agriculture/floriculture-and-ornamental-nurseries/rose
- APS · Diseases of Roses: https://www.apsnet.org/edcenter/apsnetfeatures/Pages/Roses.aspx
- UC Master Gardeners (Ventura): https://ucanr.edu/node/131269
- ICA Colombia (registro de plaguicidas): https://www.ica.gov.co

Las fichas son una síntesis orientativa; no sustituyen a un ingeniero agrónomo.
