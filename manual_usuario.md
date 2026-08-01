# Manual de Usuario del Motor Ontológico v2.0

**Guía Operativa para Usuarios No Técnicos**  
**Versión del Sistema**: 2.0.0  
**Interfaz**: Gráfica Web y Línea de Comandos Básica

---

## 1. ¿Qué es el Motor Ontológico y para qué sirve?

El **Motor Ontológico** es una herramienta que toma textos de documentos (manuales, leyes, procesos, reportes técnicos) y los transforma automáticamente en un **mapa jerárquico de acciones claras y estructuradas**.

### 1.1 El Problema que Resuelve

| Texto Original (Sin Estructura) | Grafo Imperativo Resultante (Estructurado) |
|---|---|
| *"Para procesar una solicitud de crédito, el analista debe revisar los documentos del cliente, verificar que la cédula no esté vencida y luego ingresar los datos en el sistema para que el supervisor los apruebe."* | **1. PROCESAR SOLICITUD DE CRÉDITO**<br>├── **1.1. Revisar Documentación del Cliente**<br>│   └── **1.1.1. Verificar Vigencia de Cédula de Identidad**<br>└── **1.2. Registrar Datos en Sistema Operativo**<br>    └── **1.2.1. Aprobar Registro por Supervisor** |

---

## 2. Modos de Uso del Sistema

El sistema ofrece 3 modos de acceso según el perfil de trabajo:

```
                  ┌─────────────────────────────────────────┐
                  │        MOTOR ONTOLÓGICO v2.0            │
                  └────────────────────┬────────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
 ┌──────────────┐              ┌──────────────┐              ┌──────────────┐
 │ 1. MODO WEB  │              │ 2. MODO CLI  │              │3. MODO DEMO  │
 │ (Recomendado)│              │ (Comandos)   │              │ (Instantáneo)│
 └──────────────┘              └──────────────┘              └──────────────┘
```

---

## 3. Modo 1: Interfaz Web (Recomendado)

La interfaz web no requiere instalar conocimientos técnicos y se ejecuta directamente en el navegador de internet.

### 3.1 Cómo Iniciar la Interfaz Web

1. Abre la terminal o consola de comandos.
2. Escribe el siguiente comando y presiona `Enter`:

```bash
python run.py --serve
```

3. Abre tu navegador web (Chrome, Edge, Firefox) e ingresa a la dirección:

$$\text{http://localhost:8080}$$

---

### 3.2 Componentes de la Pantalla Principal

La aplicación web consta de 5 pestañas de control:

| Pestaña | Función Principal | Cuándo Usarla |
|---|---|---|
| **Pipeline** | Ventana principal de carga de texto y procesamiento. | Para pegar un texto nuevo y generar la ontología. |
| **Árbol Imperativo** | Visualizador en árbol plegable con botones de expandir/contraer. | Para explorar la jerarquía visualmente de forma interactiva. |
| **JSON-LD** | Visor del código estructurado exportable a otros sistemas. | Para descargar el archivo en formato estándar de datos. |
| **Auditoría MECE** | Reporte de coherencia (sin solapamientos ni vacíos). | Para verificar que el mapa generado no tenga errores lógicos. |
| **Acerca de** | Diagrama de arquitectura e información de versión. | Para consultar la ficha técnica del sistema. |

---

### 3.3 Paso a Paso: Procesar un Texto en la Web

```
[ PASO 1 ]               [ PASO 2 ]                [ PASO 3 ]               [ PASO 4 ]
 Copiar y Pegar           Hacer Clic en             Ver Progreso             Explorar
 Texto en el Área  ───►   "Ejecutar Pipeline" ───►  de las 4 Fases  ───►    el Árbol
 de Entrada               en Pantalla               (P1 ➔ P2 ➔ P3 ➔ P4)      Resultante
```

1. Ve a la pestaña **Pipeline**.
2. En el recuadro **"Corpus de Entrada (Texto Seco)"**, pega tu documento.
3. Haz clic en el botón azul **`Ejecutar Pipeline SOTA`**.
4. Observa los indicadores visuales: las 4 fases se iluminarán en verde conforme se procese el texto:
   - **P1 Filtrado**: Limpia el texto de palabras vacías (artículos, conectores).
   - **P2 Clustering**: Agrupa frases que hablan del mismo tema.
   - **P3 Canonicalización**: Estandariza los nombres y resuelve sinónimos.
   - **P4 Grafo**: Convierte los títulos a verbos imperativos (acciones).
5. Automáticamente verás el mapa resultante en pantalla.

---

## 4. Modo 2: Línea de Comandos (CLI)

Este modo se utiliza para procesar documentos de texto guardados en tu equipo.

### 4.1 Comandos Rápidos

#### Ver el árbol estructurado del mapa base:
```bash
python run.py --tree
```

#### Procesar un texto corto directamente desde la consola:
```bash
python run.py --corpus "El sistema de inventario requiere registrar las entradas de mercancía y validar el stock mínimo."
```

#### Procesar un archivo `.txt` guardado en tu carpeta:
```bash
python run.py --corpus-file "C:\MisDocumentos\manual_procesos.txt" --format tree
```

#### Guardar el resultado en un archivo JSON para compartir:
```bash
python run.py --corpus-file manual.txt --export jsonld --output resultado.json
```

---

## 5. Modo 3: Modo Demostración Rápida

Si deseas probar el sistema inmediatamente sin redactar texto:

1. Ejecuta el comando:
```bash
python run.py --demo
```
2. O bien, en la Interfaz Web, dentro de la pestaña **Pipeline**, haz clic en el botón **`Cargar Demo Téc`**.

El sistema procesará un texto técnico predeterminado sobre inteligencia artificial y procesamiento de lenguaje natural, generando la estructura completa de muestra en menos de 10 milisegundos.

---

## 6. Glosario de Términos del Sistema

| Término en Pantalla | Significado Práctico |
|---|---|
| **Corpus** | El texto original que se ingresa al sistema para procesar. |
| **Nodo** | Cada uno de los elementos o cuadritos que conforman el mapa. |
| **Nodo Atómico** | Un elemento final del mapa que ya no se puede subdividir más. |
| **Imperativo** | La conversión de un título a una orden o acción (ej. "Lematizar texto"). |
| **MECE** | Garantía de que no hay temas repetidos (Exclusión Mutua) ni temas olvidados (Exhaustividad Colectiva). |
| **SAT (Satisfacible)** | Indicador verde que confirma que el mapa generado es lógicamente coherente y sin contradicciones. |
