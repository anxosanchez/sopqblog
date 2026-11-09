# DECISIONS.md · Registro de Decisiones de Arquitectura e Ingeniería (ADR) & Auditoría Adversarial

Este documento recoge todas las decisiones arquitectónicas, resoluciones de diseño, compensaciones (*trade-offs*) y los hallazgos críticos detectados durante la auditoría adversarial (Red Team) para la infraestructura del blog técnico **ProcessSim** y su pipeline de automatización.

---

## 1. Arquitectura de Compilación Dual (Quarto HTML + Revealjs)

### Contexto
El encargo requería soporte para artículos técnicos en formato HTML y presentaciones complementarias en Revealjs dentro del mismo sitio Quarto, manteniendo idéntico sistema de diseño SCSS y renderizado KaTeX.

### Problema Detectado (Auditoría Adversarial)
Al configurar simultáneamente `html` y `revealjs` como formatos globales de nivel superior en `_quarto.yml`, el compilador de Quarto intentaba compilar cada archivo `.qmd` del sitio a ambos formatos. Esto causaba:
1. Una colisión crítica de nombres en `index.qmd` al generar `index.html` para HTML y para Revealjs al mismo tiempo, provocando el error `Deno.renameSync (NotFound os error 2)`.
2. Una presentación Revealjs en `index.qmd` no tiene sentido semántico para la portada del blog.
3. El tema de Revealjs `darkly` no existe en la biblioteca estándar de temas de Revealjs (donde los temas oscuros canónicos son `night`, `black`, `moon` o `dracula`), lo que disparaba excepciones `readfile ... darkly.scss not found`.

### Decisión de Ingeniería
- Se fijó `format: html` como el formato maestro por defecto a nivel de proyecto en `_quarto.yml`.
- Se configuró Revealjs en `pipeline/slides_generator.py` y en las presentaciones complementarias (`posts/slides-*.qmd`) utilizando el tema canónico `theme: [night, ../styles/custom.scss]`.
- Se garantiza la interoperabilidad total: los posts de artículos compilan a HTML editorial con ancho extendido de 900px, mientras que los decks de diapositivas compilan a presentaciones Revealjs 16:9 con navegación interactiva y enlace bidireccional al artículo.

---

## 2. Taxonomía Técnica Canónica Ortogonal de 3 Niveles

### Contexto
Un blog técnico multimodal sufre de entropía taxonómica (ej. etiquetas duplicadas como `hysys`, `aspen`, `ASPEN HYSYS`, `destilacion`, `separacion`). Si las categorías no son estrictas, los filtros por pestañas (`.panel-tabset`) en `index.qmd` se rompen o muestran listas vacías.

### Decisión de Ingeniería (`pipeline/taxonomy.py`)
Se implementó un motor de gobernanza ortogonal estricto de 3 niveles:
- **Nivel 1 (Plataforma canónica):** Exactamente una entre `"Aspen HYSYS"`, `"DWSIM"` y `"Python"`. Se normalizan sinónimos (`aspen`, `colab`, `jupyter`, `dwsim open source`, `biosteam`, `scipy`).
- **Nivel 2 (Dominio de proceso):** Al menos un dominio físico (`"Separación"`, `"Reactores"`, `"Intercambio Térmico"`, `"Termodinámica"`, `"Control de Procesos"`, `"Servicios Industriales"`, `"Dinámica de Fluidos"`, `"Optimización"`).
- **Nivel 3 (Entregable industrial):** Al menos un artefacto reproducible (`"Caso HSC"`, `"Simulación DWSIM"`, `"Notebook Colab"`, `"Video Tutorial"`, `"Slide Deck"`).

### Mecanismo de Sanitización
- Descomposición Unicode NFKD para eliminar tildes y diacríticos antes del emparejamiento.
- Heurísticas de fallback cuando una etiqueta no tiene match directo.
- Si falta algún nivel, se inyecta el valor canónico por defecto evitando posts huérfanos.

---

## 3. Manejo de Bloqueo de E/S en Subprocesos (Deno `WouldBlock os error 35`)

### Contexto
Durante la ejecución de comandos en entornos sandbox con tuberías (`pipes`), stdout y stderr pueden quedar configurados con la bandera de no-bloqueo `O_NONBLOCK`. Cuando Quarto o Pandoc escriben ráfagas de trazas superiores a la capacidad del búfer del pipe, Deno lanza la excepción no capturada `WouldBlock: Resource temporarily unavailable (os error 35)`.

### Decisión de Ingeniería
- En `pipeline/publish_pipeline.py`, se invoca `quarto render --quiet` con captura controlada de salida.
- En los scripts de testing y ejecución se restaura el modo bloqueante en los descriptores estándar mediante `fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)`.

---

## 4. Degradación Elegante en APIs Externas (Gemini & YouTube)

### Contexto
En entornos de integración continua (CI/CD) o auditorías sin credenciales de red activas, invocar directamente las APIs de Gemini o YouTube provocaría fallos de compilación si las librerías o las claves de API no están presentes.

### Decisión de Ingeniería
- **Motor Gemini (`pipeline/gemini_engine.py`):** Arquitectura híbrida. Si `GEMINI_API_KEY` está disponible y la librería `google-genai` o `google-generativeai` está instalada, realiza inferencia con modelos avanzados. Si no, activa de forma automática e inmediata un analizador heurístico determinista basado en reglas termodinámicas y palabras clave de ingeniería química.
- **Subidor de YouTube (`pipeline/youtube_uploader.py`):** Dispone de modo `--dry-run` e inyección simulada de URLs e identificadores de vídeo sin requerir credenciales activas, garantizando que los tests unitarios y el pipeline de publicación funcionen al 100% de manera autónoma.
- **Inyección Idempotente:** El método `inject_video_and_badges` verifica la presencia previa de la barra de badges o del shortcode `{{< video ... >}}`, reemplazándolos de forma limpia sin duplicar elementos HTML ni marcadores Markdown.

---

## 5. Sistema de Diseño SCSS Awwwards-Level y Accesibilidad WCAG AAA

### Contexto
Los blogs de Quarto suelen presentar una apariencia genérica con fuentes estándar. Para este portal técnico se requería una estética editorial de ingeniería de alta precisión.

### Decisión de Ingeniería (`styles/custom.scss`)
- **Tipografía Técnica Tríadica:**
  - *Plus Jakarta Sans*: lectura limpia y proporciones modernas para cuerpo y encabezados.
  - *Fira Code*: tipografía monoespaciada para ecuaciones, números de corrientes, parámetros y bloques de código.
  - *Instrument Serif*: toques editoriales en destacados visuales y citas conceptuales.
- **Paleta de Contraste Oscuro Estricto:**
  - Fondo de superficie `#0a0d14`, tarjetas elevadas `#141b2a`, bordes sutiles `#232d42`, texto principal `#f1f5f9` (ratio de contraste superior a 12:1, superando WCAG AAA).
- **Componentes de Ingeniería Químico-Termodinámica:**
  - `.resource-badge-bar`: Barra interactiva con microinteracciones y botones con colores de acento (ámbar Colab, azul Drive, púrpura Revealjs, rojo YouTube).
  - `.metric-grid` & `.metric-card`: Tarjetas métricas con borde lateral coloreado por variables de proceso, unidades en subíndice y pie de consistencia.
  - `.stream-table-wrapper` & `.stream-table`: Tablas de corrientes con alineación numérica monospace a la derecha, cabecera fija y soporte de scroll horizontal en dispositivos móviles.

---

## 6. Configuración CI/CD con GitHub Actions (`.github/workflows/publish.yml`)

### Contexto
Garantizar despliegue continuo en GitHub Pages tras cada commit en la rama `main` sin dependencias manuales.

### Decisión de Ingeniería
- Permisos explícitos: `contents: read`, `pages: write`, `id-token: write`.
- Concurrencia de despliegue: `group: "pages"`, `cancel-in-progress: false` para evitar artefactos huérfanos.
- Cache de pip integrado mediante `actions/setup-python@v5`.
- Ejecución obligatoria de la suite de pruebas unitarias (`python -m unittest discover tests -v`) y auditoría de taxonomía (`python pipeline/publish_pipeline.py --check-all`) antes de compilar y desplegar la web con `actions/deploy-pages@v4`.

---

## 7. Estratexia de Internacionalización Trilingüe (Galego, Castelán, English)

### Contexto
O blog requiría soporte trilingüe onde o **galego** é a lingua principal e nativa do proxecto institucional (Escola de Enxeñaría Industrial, Universidade de Vigo), con equivalentes completos en castelán e inglés para máxima visibilidade internacional.

### Decisión de Enxeñaría
- **Canonicidade e Enrutamento:** 
  - `index.qmd` e `posts/caso-*.qmd` en galego como punto de entrada predeterminado (`lang: gl`).
  - Páxinas paralelas `index.es.qmd` e `index.en.qmd` (así como `posts/caso-*.es.qmd`, `posts/caso-*.en.qmd`) con selector interactivo (`.lang-switcher-bar`) enlazado dinamicamente.
- **Terminoloxía Técnica:** Rigor terminolóxico en enxeñaría química galega (*mestura ternaria*, *fraccionamento*, *refervedor*, *equilibrio líquido-vapor*, *balanzo de materia e enerxía*).

---

## 8. Integración da Identidade Visual e Logos Dual (Light & Dark)

### Contexto
Deseñáronse dous logotipos institucionais oficiais con Google Gemini para o laboratorio **SOPQ** (Simulación e Optimización de Procesos Químicos · EEI UVigo): unha versión sobre fondo branco para tema claro e unha versión con iluminación neón cian/azul escuro para tema escuro. O requirimento esixía aplicar ambos logos dun xeito orgánico, elegante e non invasivo ao longo de todo o portal.

### Decisión de Enxeñaría
1. **Cabeceira e Barra de Navegación (`navbar`):**
   - Integrado mediante Quarto `navbar: logo: assets/images/logo-light.jpg` e conmutado dinamicamente a `logo-dark.jpg` vía Javascript ultralixeiro con `MutationObserver` (`assets/theme-switcher.html`) e regras CSS reactivas.
   - Efecto *neon cyan glow* (`drop-shadow: 0 0 10px rgba(0, 212, 170, 0.4)`) ao activar o modo escuro.
2. **Hero da Portada (`index.qmd` / `.es` / `.en`):**
   - Tarxeta de marca (`.hero-brand-card`) con efecto de cristal esmerilado (*glassmorphism*) e marco de monitor a xogo co propio deseño do logo.
   - Emprego de parellas de etiquetas `<img>` con clases `.sopq-logo-light` e `.sopq-logo-dark` controladas por visualización CSS pura (`display: none` / `display: inline-block`), evitando calquera pestanexo (*FOUC*).
3. **Pé de Páxina (`page-footer`):**
   - Miniatura de dobre logo con ligazón institucional á Escola de Enxeñaría Industrial da Universidade de Vigo.
4. **Artigos e Cadernos de Simulación (`posts/`):**
   - Distintivo institucional superior (`.post-institutional-badge`) e cabeceira oficial `.post-header-brand` con logo light/dark reactivo, datos departamentais e estado de caso verificado.
5. **Presentacións Revealjs:**
   - Incorporación automática de `logo: ../assets/images/logo-dark.jpg` nos decks xerados polo pipeline, mantendo presenza de marca corporativa durante exposicións e conferencias.

---

## 9. Xestión de Autoría Múltiple e Supervisión Editorial Previa

### Contexto
Coa incorporación de novos investigadores e redactores convidados, o portal precisaba reflectir fielmente a coautoría (nome, filiación, rol específico na simulación, contacto) e establecer un procedemento de filtrado previo para que ningún artigo poida publicarse sen a supervisión directa do editor (Anxo Sánchez).

### Decisión de Enxeñaría
1. **Estrutura de Autoría Múltiple en YAML:**
   - Soporte para listaxes de autores con campos normalizados (`name`, `affiliation`, `email`, `role`).
   - Estilizado CSS en `.quarto-title-meta` que presenta cada autor/a en tarxetas con distintivos tipográficos profesionais.
2. **Mecanismo de Bloqueo e Ocultación (`draft: true` e Pull Requests):**
   - Os novos artigos propostos almacénanse con `draft: true` ou tramítanse mediante Pull Request en GitHub. Quarto exclúe de raíz calquera borrador das listaxes públicas, motores de busca e sitemaps ata a validación definitiva do editor.
3. **Notificador Automático por Telegram (`pipeline/telegram_editor_notifier.py`):**
   - Servizo desacoplado en Python puro (sen dependencias pesadas de terceiros) que envía unha alerta enriquecida ao Telegram privado do editor co título, autor/es, taxonomía, ficheiros de simulación achegados e ligazón directa de revisión.
4. **Guía Pública para Colaboradores (`guia-colaboradores.qmd`):**
   - Páxina de referencia incorporada na barra de navegación superior (`Colaborar`) con directrices paso a paso, modelos descargables, xerarquía de arquivos (`assets/simulations/`, `assets/images/`) e regras de taxonomía.

---

## 10. Integración do Logo en Cabeceira de Artigo e Índice de Contidos (TOC)

### Contexto
O requirimento do usuario solicitaba que o logo oficial (en versións clara e escura) acompañase a lectura dentro de cada post resolto, especificamente na cabeceira do artigo ou no índice de contidos lateral.

### Decisión de Enxeñaría
- **Cabeceira Oficial (`.post-header-brand`):** Banner estilizado ao comezo do artigo con dobre imaxe reactiva, datos de laboratorio e selo de verificación.
- **Inxección Dinámica no TOC (`.toc-brand-badge`):** O script `assets/theme-switcher.html` inxecta automaticamente o distintivo de marca na parte superior do bloque `#TOC` (barra lateral flotante de contidos), asegurando presenza institucional constante durante a navegación e respecto absoluto do modo claro/escuro.
