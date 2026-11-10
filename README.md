# ProcessSim // Blog de Simulación Termodinámica e Enxeñaría de Procesos

> Infraestrutura de publicación técnica editorial, modelado computacional de procesos e pipeline de automatización integral trilingüe baseada en **Quarto**, **Python** e **GitHub Pages**.

[![Deploy Quarto Blog to GitHub Pages](https://github.com/anxosanchez/sopqblog/actions/workflows/publish.yml/badge.svg)](https://github.com/anxosanchez/sopqblog/actions/workflows/publish.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.15-blue.svg)](https://www.python.org/)
[![Quarto Version](https://img.shields.io/badge/quarto-v1.5%20%7C%20v1.10-75AADB.svg)](https://quarto.org/)
[![Idiomas](https://img.shields.io/badge/idiomas-Galego%20(Principal)%20%7C%20Castel%C3%A1n%20%7C%20English-00d4aa.svg)](#arquitectura-trilingüe)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## Arquitectura Trilingüe (Galego, Castelán, English)

O portal está deseñado cunha arquitectura trilingüe nativa onde o **galego é o idioma vehicular e principal**, ofrecendo navegación integrada e selector de lingua na barra superior e en cada artigo:

- **Galego (Idioma Principal):** Contorno por defecto (`/`, `index.html`), toda a terminoloxía técnica de enxeñaría de procesos, táboas de correntes, métricas operacionais e presentacións executivas.

- **Castelán:** Versión completa do explorador (`index.es.html`) e artigos equivalentes (`caso-[slug].es.html`).

- **English:** Versión completa para a comunidade internacional (`index.en.html`) e artigos correspondentes (`caso-[slug].en.html`).

## Visión Xeral do Proxecto

**ProcessSim** é unha plataforma editorial de enxeñaría química e termodinámica computacional deseñada baixo estándares visuais de nivel *Awwwards* e rigor matemático estrito. Combina:

1. **Blog Técnico Multimodal en Quarto:**
   - Soporte nativo para artigos técnicos (`html`) e presentacións executivas complementarias (`revealjs`).
   - Modo escuro/claro con tokens SCSS e cumprimento estrito de contraste **WCAG AAA**.
   - Renderizado matemático de alto rendemento con **KaTeX**.
   - Compoñentes de proceso: barras de recursos interactivos, selector de idioma, tarxetas métricas de balance e táboas de correntes industriais con scroll horizontal adaptable.
   - Hub de exploración con panel por pestanas nativas (`.panel-tabset`) filtrado por plataformas: **Aspen HYSYS**, **DWSIM (Código Aberto)** e **Python**.

2. **Pipeline de Automatización CLI (`pipeline/publish_pipeline.py`):**
   - **Gobernanza de Taxonomía (`pipeline/taxonomy.py`):** Normalización canónica ortogonal en 3 niveis (Plataforma, Dominio de Proceso, Entregable), recoñecendo sinónimos en galego, castelán e inglés.
   - **Motor Gemini AI (`pipeline/gemini_engine.py`):** Inferencia taxonómica, redacción técnica, extracción de condicións de operación e xeración de metadatos SEO con timestamps para YouTube (con fallback determinista sen conexión).
   - **Xerador de Diapositivas (`pipeline/slides_generator.py`):** Síntese desatendida do caso en diapositivas Revealjs co mesmo tema visual e soporte multilingüe.
   - **Xestor Multimedia (`pipeline/youtube_uploader.py`):** Subida resumible OAuth2 a YouTube Data API v3 e inxección de badges e shortcodes `{{< video ... >}}`.

3. **Integración e Despregamento Continuo (CI/CD):**
   - Workflow de GitHub Actions (`.github_disabled/publish.yml`) con probas unitarias automáticas, auditoría taxonómica e despregamento continuo en **GitHub Pages** mediante `quarto publish gh-pages`.

## Estrutura do Repositorio

```text
.
├── _quarto.yml                     # Configuración central (Galego principal, KaTeX, temas dark/light)
├── index.qmd                       # Hub de exploración en Galego (Portada principal)
├── index.es.qmd                    # Hub de exploración en Castelán
├── index.en.qmd                    # Hub de exploración en English
├── styles/
│   └── custom.scss                 # Sistema de deseño: tokens, tipografía, tarxetas, selector de lingua
├── posts/
│   ├── _template_post.qmd          # Modelo base canónico con frontmatter e balances
│   ├── caso-destilacion-flash.qmd  # Caso real (Galego): Separación flash con Peng-Robinson e Rachford-Rice
│   ├── caso-destilacion-flash.es.qmd # Versión en Castelán
│   ├── caso-destilacion-flash.en.qmd # Versión en English
│   ├── slides-destilacion-flash.qmd  # Diapositivas Revealjs (Galego)
│   ├── slides-destilacion-flash.es.qmd
│   ├── slides-destilacion-flash.en.qmd
│   ├── caso-hysys-columna-debutanizadora.qmd # Caso Aspen HYSYS (Galego)
│   ├── slides-hysys-columna-debutanizadora.qmd
│   ├── caso-dwsim-reactor-cstr-esterificacion.qmd # Caso DWSIM (Galego)
│   └── slides-dwsim-reactor-cstr-esterificacion.qmd
├── pipeline/
│   ├── __init__.py
│   ├── taxonomy.py                 # Regra de 3 niveis ortogonais con soporte trilingüe
│   ├── gemini_engine.py            # Motor Gemini con fallback determinista
│   ├── slides_generator.py         # Xerador automático de Revealjs
│   ├── youtube_uploader.py         # Xestor YouTube e inxección de recursos
│   └── publish_pipeline.py         # CLI orquestrador unificado
├── tests/
│   ├── test_taxonomy.py            # Tests de taxonomía, sinónimos trilingües e robustez
│   ├── test_gemini.py              # Tests de inferencia e fallbacks
│   ├── test_slides.py              # Tests de diapositivas Revealjs
│   └── test_pipeline.py            # Tests de integración e idempotencia
├── assets/images/                  # Diagramas vectoriais PFD (SVG)
├── requirements.txt                # Dependencias Python
├── .env.example                    # Modelo de variables de contorno
├── DECISIONS.md                    # Rexistro de decisións de enxeñaría e auditoría adversarial
└── README.md                       # Documentación técnica completa
```

## ⚡ Instalación e Uso

### 1. Requisitos

- **Python 3.11+**

- **Quarto CLI 1.5+**

```bash
# Clonar o repositorio
git clone https://github.com/anxosanchez/sopqblog.git
cd sopqblog

# Crear contorno virtual e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Executar a Suite de Probas
```bash
python -m unittest discover tests -v
```

### 3. Compilar o Sitio Web Trilingüe
```bash
quarto render
```

### 4. Despregar en GitHub Pages
```bash
quarto publish gh-pages
```

## Taxonomía Canónica Ortogonal de 3 Niveis

| Nivel | Nome | Valores Canónicos (Galego) | Sinónimos Mapeados (GL / ES / EN) |
| :---: | :--- | :--- | :--- |
| **1** | **Plataforma** | `Aspen HYSYS`, `DWSIM`, `Python` | `hysys`, `aspen`, `colab`, `jupyter`, `biosteam`, `dwsim open source` |
| **2** | **Dominio** | `Separación`, `Reactores`, `Intercambio Térmico`, `Termodinámica`, `Control de Procesos`, `Servizos Industriais`, `Dinámica de Fluídos`, `Optimización` | `destilacion`, `distillation`, `cstr`, `cinetica`, `heat exchange`, `utilities`, `fluid dynamics` |
| **3** | **Entregable** | `Caso HSC`, `Simulación DWSIM`, `Caderno Colab`, `Vídeo Titorial`, `Slide Deck` | `hsc`, `dwxml`, `notebook colab`, `video tutorial`, `slides`, `presentacion` |


## Licenza

Este proxecto está baixo a Licenza **MIT** para o código fonte e **Creative Commons Attribution 4.0 International (CC BY 4.0)** para os contidos e modelos de simulación.
