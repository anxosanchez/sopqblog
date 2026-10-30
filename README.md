# ProcessSim // Chemical Engineering & Thermodynamic Simulation Blog

> Infraestructura de publicación técnica editorial, modelado computacional de procesos y pipeline de automatización integral basado en **Quarto**, **Python** y **GitHub Pages**.

[![Deploy Quarto Blog to GitHub Pages](https://github.com/anxosanchez/sopqblog/actions/workflows/publish.yml/badge.svg)](https://github.com/anxosanchez/sopqblog/actions/workflows/publish.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.15-blue.svg)](https://www.python.org/)
[![Quarto Version](https://img.shields.io/badge/quarto-v1.5%20%7C%20v1.10-75AADB.svg)](https://quarto.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

## 🔬 Visión General del Proyecto

**ProcessSim** es una plataforma editorial de ingeniería química y termodinámica computacional diseñada bajo estándares visuales de nivel *Awwwards* y rigor matemático estricto. Combina:

1. **Blog Técnico Multimodal en Quarto:**
   - Soporte nativo para artículos técnicos (`html`) y presentaciones ejecutivas complementarias (`revealjs`).
   - Modo oscuro/claro con tokens SCSS y cumplimiento estricto de contraste **WCAG AAA**.
   - Renderizado matemático de alto rendimiento con **KaTeX**.
   - Componentes de proceso: barras de recursos interactivos, tarjetas métricas de balance y tablas de corrientes industriales con scroll horizontal adaptable.
   - Hub de exploración con panel por pestañas nativas (`.panel-tabset`) filtrado por plataformas: **Aspen HYSYS**, **DWSIM (Open Source)** y **Python**.

2. **Pipeline de Automatización CLI (`pipeline/publish_pipeline.py`):**
   - **Gobernanza de Taxonomía (`pipeline/taxonomy.py`):** Normalización canónica ortogonal en 3 niveles (Plataforma, Dominio de Proceso, Entregable).
   - **Motor Gemini AI (`pipeline/gemini_engine.py`):** Inferencia taxonómica, redacción técnica, extracción de condiciones de operación y generación de metadatos SEO con timestamps para YouTube (con fallback determinista sin conexión).
   - **Generador de Diapositivas (`pipeline/slides_generator.py`):** Síntesis desatendida del caso en diapositivas Revealjs con el mismo tema visual.
   - **Gestor Multimedia (`pipeline/youtube_uploader.py`):** Subida resumible OAuth2 a YouTube Data API v3 e inyección de badges y shortcodes `{{< video ... >}}`.

3. **Integración y Despliegue Continuo (CI/CD):**
   - Workflow de GitHub Actions (`.github/workflows/publish.yml`) con pruebas unitarias automáticas, auditoría taxonómica y despliegue continuo en **GitHub Pages**.

---

## 📁 Estructura del Repositorio

```text
.
├── _quarto.yml                     # Configuración central del sitio Quarto (HTML + Revealjs + KaTeX)
├── index.qmd                       # Hub de exploración: hero, métricas, grid y pestañas por plataforma
├── styles/
│   └── custom.scss                 # Sistema de diseño: variables CSS, tipografías, tarjetas y tablas
├── posts/
│   ├── _template_post.qmd          # Plantilla base canónica con badges y secciones de balance
│   ├── caso-destilacion-flash.qmd  # Caso real: Separación flash ternaria con Peng-Robinson y Rachford-Rice
│   ├── slides-destilacion-flash.qmd# Presentación Revealjs complementaria del caso flash
│   ├── caso-hysys-columna-debutanizadora.qmd # Caso Aspen HYSYS: Fraccionamiento de GLP
│   ├── slides-hysys-columna-debutanizadora.qmd
│   ├── caso-dwsim-reactor-cstr-esterificacion.qmd # Caso DWSIM: Reactor continuo con NRTL
│   └── slides-dwsim-reactor-cstr-esterificacion.qmd
├── pipeline/
│   ├── __init__.py
│   ├── taxonomy.py                 # Regla de 3 niveles ortogonales y normalización de sinónimos
│   ├── gemini_engine.py            # Motor Gemini para inferencia técnica y metadatos SEO
│   ├── slides_generator.py         # Síntesis automática a Revealjs
│   ├── youtube_uploader.py         # Subida resumible a YouTube e inyección de badges/shortcodes
│   └── publish_pipeline.py         # Orquestador CLI unificado
├── tests/
│   ├── test_taxonomy.py            # Pruebas unitarias y de auditoría adversarial de taxonomía
│   ├── test_gemini.py              # Pruebas del motor Gemini y heurísticas de fallback
│   ├── test_slides.py              # Pruebas de generación y parsing de Revealjs
│   └── test_pipeline.py            # Pruebas de integración del pipeline y subida a YouTube
├── assets/
│   └── images/                     # Diagramas vectoriales PFD (SVG)
├── .github/workflows/
│   └── publish.yml                 # Workflow CI/CD para GitHub Pages
├── requirements.txt                # Dependencias del entorno Python
├── .env.example                    # Plantilla de variables de entorno (claves de API y tokens)
├── DECISIONS.md                    # Registro de decisiones de ingeniería y auditoría adversarial
└── README.md                       # Documentación técnica completa
```

---

## ⚡ Instalación y Configuración

### 1. Requisitos Previos
- **Python 3.11+**
- **Quarto CLI 1.5+** ([Descargar Quarto](https://quarto.org/docs/get-started/))

### 2. Clonar el Repositorio e Instalar Dependencias
```bash
git clone https://github.com/anxosanchez/sopqblog.git
cd blog

# Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno (Opcional para APIs externas)
Copia la plantilla de entorno:
```bash
cp .env.example .env
```
Edita `.env` con tus claves según corresponda:
```ini
GEMINI_API_KEY=tu_clave_de_gemini
YOUTUBE_CLIENT_SECRETS_FILE=client_secrets.json
```

> **Nota de Resiliencia:** El pipeline opera de forma 100% funcional y autónoma incluso sin claves de API gracias a su motor heurístico determinista y modo de prueba (`--dry-run`).

---

## 🚀 Uso del Pipeline de Publicación (CLI)

El script `pipeline/publish_pipeline.py` es el punto de entrada unificado para procesar artículos, generar presentaciones y compilar la web.

### 1. Auditar la Integridad de Todos los Posts
Verifica que cada artículo en `posts/` cumpla estrictamente con la regla taxonómica canónica:
```bash
python pipeline/publish_pipeline.py --check-all
```

### 2. Procesar un Borrador y Generar Diapositivas
Infiere o normaliza categorías, genera la presentación Revealjs complementaria e inyecta enlaces de Drive y Colab:
```bash
python pipeline/publish_pipeline.py \
  --post posts/caso-destilacion-flash.qmd \
  --colab-url "https://colab.research.google.com/drive/ejemplo" \
  --drive-url "https://drive.google.com/drive/folders/ejemplo"
```

### 3. Simular Subida de Vídeo e Inyección Automática (Dry-Run)
Registra un vídeo de simulación `.mp4`, calcula marcas de tiempo SEO e inyecta el shortcode de vídeo:
```bash
python pipeline/publish_pipeline.py \
  --post posts/caso-destilacion-flash.qmd \
  --video assets/videos/simulacion.mp4 \
  --dry-run
```

### 4. Compilación Completa del Blog Quarto
Compila todos los artículos y diapositivas en el directorio `_site/`:
```bash
python pipeline/publish_pipeline.py --check-all --render
```
O directamente con el CLI de Quarto:
```bash
quarto render
```

### 5. Previsualización Local con Recarga en Vivo
```bash
quarto preview
```

---

## 🏷️ Gobernanza de Taxonomía Técnica

Para evitar categorías fragmentadas o duplicadas, el blog impone una **regla de 3 niveles ortogonales**:

| Nivel | Nombre de Nivel | Valores Canónicos Permitidos | Sinónimos Normalizados Automáticamente |
| :---: | :--- | :--- | :--- |
| **1** | **Plataforma** (Exactamente 1) | `Aspen HYSYS`, `DWSIM`, `Python` | `hysys`, `aspen`, `colab`, `jupyter`, `biosteam`, `dwsim open source` |
| **2** | **Dominio de Proceso** ($\ge 1$) | `Separación`, `Reactores`, `Intercambio Térmico`, `Termodinámica`, `Control de Procesos`, `Servicios Industriales`, `Dinámica de Fluidos`, `Optimización` | `destilacion`, `flash`, `cstr`, `cinetica`, `vle`, `calor`, `utilities` |
| **3** | **Entregable** ($\ge 1$) | `Caso HSC`, `Simulación DWSIM`, `Notebook Colab`, `Video Tutorial`, `Slide Deck` | `bkp`, `hsc`, `dwxml`, `video`, `youtube`, `slides`, `revealjs` |

Si se detectan etiquetas con diferente formato (mayúsculas, minúsculas, tildes omitidas o guiones), `pipeline/taxonomy.py` las mapea a su equivalente oficial sin duplicidades.

---

## 🧪 Ejecución de Pruebas Unitarias

La suite de pruebas automatizadas valida la normalización taxonómica, la resiliencia del motor Gemini, la generación de presentaciones Revealjs y la idempotencia de las modificaciones de archivos:

```bash
python -m unittest discover tests -v
```

Resultado verificado:
```text
test_check_all_posts ... ok
test_badge_and_video_injection_idempotency ... ok
test_dry_run_upload ... ok
test_generate_slides_file ... ok
test_adversarial_hybrid_and_messy_inputs ... ok
test_canonical_platforms ... ok
test_validation_function ... ok
----------------------------------------------------------------------
Ran 17 tests in 0.010s

OK
```

---

## 🌐 Despliegue Continuo (CI/CD)

El workflow `.github/workflows/publish.yml` gestiona el ciclo completo de entrega continua:
1. Detecta cambios en la rama `main` o se activa manualmente mediante `workflow_dispatch`.
2. Instala dependencias de Python y Quarto CLI (`v1.5+`).
3. Ejecuta la suite de pruebas unitarias y la auditoría de taxonomía.
4. Compila el sitio completo en `_site/`.
5. Publica automáticamente en GitHub Pages usando `actions/deploy-pages@v4`.

---

## 📄 Licencia

Este proyecto está bajo la Licencia **MIT** para el código fuente y **Creative Commons Attribution 4.0 International (CC BY 4.0)** para los contenidos y modelos de simulación.
