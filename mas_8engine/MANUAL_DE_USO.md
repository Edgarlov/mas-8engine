# 📘 MANUAL DE USO SIMPLIFICADO: SISTEMA MULTIAGENTE MAS-8ENGINE

Este manual está diseñado para explicar cómo instalar, encender y consultar el sistema **MAS-8ENGINE** paso a paso, sin requerir conocimientos de programación o matemáticas avanzadas.

---

## 💡 1. ¿Qué es este sistema y para qué sirve?

Imagina que tienes un **comité de 4 expertos virtuales** trabajando en equipo dentro de tu ordenador para resolver problemas complejos de tu empresa o proyecto:

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 ├─ 👴 El Historiador (Memoria): Busca soluciones a problemas pasados.   │
 ├─ 🔬 El Científico (Percepción): Mide probabilidades e incertidumbre.   │
 ├─ ⚖️ El Juez Formal (Verificador): Comprueba que no haya contradicciones│
 └─ 👨‍💼 El Director (Master): Coordina a los 3 y elige la mejor respuesta.  │
 ────────────────────────────────────────────────────────────────────────┘
```

Cuando le haces una pregunta difícil al sistema, los 4 expertos dialogan, descartan caminos falsos o imposibles y te entregan la **mejor solución garantizada**.

---

## 🛠️ 2. Requisitos Básicos

Para usar el sistema en tu ordenador necesitas:
- Un ordenador con **Windows**, **macOS** o **Linux**.
- **Python 3.12** instalado (o Docker si prefieres contenedores).

---

## 🚀 3. ¿Cómo encender el sistema? (Paso a Paso)

### Opción A: Inicio Rápido con Python (Recomendado)

1. **Abre la consola o terminal:**
   - En Windows: Presiona la tecla `Windows`, escribe `PowerShell` y pulsa `Enter`.

2. **Entra en la carpeta del sistema:**
   Escribe el siguiente comando y pulsa `Enter`:
   ```powershell
   cd C:\Users\edgar\Desktop\agentes\mas_8engine
   ```

3. **Enciende el servidor:**
   Ejecuta este comando:
   ```powershell
   .\.venv\Scripts\python.exe main.py
   ```

4. **Confirmación de encendido:**
   Verás una pantalla similar a esta indicando que el servidor está listo:
   ```text
   INFO:     Started server process [12345]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
   ```

---

## 🌐 4. ¿Cómo usar el sistema desde tu Navegador Web?

No necesitas escribir código para usar el sistema. Incluye una **interfaz gráfica visual** accesible desde cualquier navegador (Chrome, Edge, Firefox, Safari).

### Paso 1: Abrir el panel de control
Abre tu navegador e ingresa a la siguiente dirección:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

### Paso 2: Realizar una pregunta o consulta

1. Busca la sección de color verde que dice **`POST /api/v1/solve`** y haz clic sobre ella para desplegarla.
2. Haz clic en el botón gris que dice **`Try it out`** (Pruébalo).
3. En la casilla de texto donde dice `Request body`, escribe tu consulta dentro del campo `"query"`.

#### Ejemplo de consulta:
```json
{
  "query": "Evaluar la estrategia de expansión de mercado para una empresa de tecnología en América Latina considerando riesgos de inflación",
  "max_depth": 3,
  "branching_factor": 3
}
```

4. Haz clic en el botón azul grande que dice **`Execute`** (Ejecutar).

---

## 📊 5. ¿Cómo entender la respuesta?

Tras unos segundos, el sistema te devolverá un resultado estructurado. Aquí te mostramos cómo interpretar las partes más importantes:

| Campo en la Respuesta | Significado Práctico |
| :--- | :--- |
| **`optimal_solution`** | ⭐️ **La respuesta final recomendada** por el comité de expertos. |
| **`execution_time_ms`** | El tiempo que tardó el sistema en pensar (en milisegundos). |
| **`thought_tree`** | La lista de todas las alternativas y rutas de pensamiento analizadas. |
| **`pruning_log`** | Las ideas que el sistema descartó por contener contradicciones o fallos lógicos. |

---

## 📝 6. Ejemplos Prácticos de Preguntas

Puedes consultar al sistema sobre cualquier problema estratégico o de toma de decisiones:

- **Estrategia y Negocio:**
  > `"Estructurar un plan de contingencia para la cadena de suministro ante el incremento de costes de transporte."`

- **Asignación de Recursos:**
  > `"Determinar la distribución óptima de presupuesto entre marketing digital y desarrollo de producto."`

- **Análisis de Riesgos:**
  > `"Evaluar el impacto de introducir una nueva regulación de protección de datos en la plataforma."`

---

## ❓ 7. Preguntas Frecuentes (FAQ)

### ¿Cómo apago el sistema?
En la ventana de la consola donde lo encendiste, presiona las teclas **`CTRL + C`**.

### ¿Qué hago si me aparece un error al abrir `http://localhost:8000/docs`?
Asegúrate de que la consola siga abierta y no haya mostrado ningún mensaje de error al arrancar `main.py`.

### ¿Puedo cambiar la profundidad con la que piensa el sistema?
Sí. En la consulta puedes ajustar:
- **`max_depth`**: Cuántos pasos de profundidad analizará (por defecto `3`).
- **`branching_factor`**: Cuántas alternativas explorará por cada paso (por defecto `3`).
