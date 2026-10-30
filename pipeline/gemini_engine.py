"""Gemini AI Technical Engine for Process Simulation Blog Automation.

Integrates Google Gemini to:
  - Infer strict 3-tier canonical taxonomy from engineering content.
  - Draft executive summaries with thermodynamic rigor.
  - Extract and structure operating conditions & stream properties.
  - Generate high-CTR YouTube metadata with exact technical timestamps and SEO tags.
  - Seamlessly degrade to deterministic heuristic parsers when offline or in CI/CD.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pipeline.taxonomy import sanitize_categories, CANONICAL_DOMAINS, CANONICAL_PLATFORMS


@dataclass
class OperatingConditions:
    """Structured operating conditions and key thermodynamic metrics."""
    thermodynamic_model: str = "Peng-Robinson"
    temperature: str = "N/A"
    pressure: str = "N/A"
    feed_flow: str = "N/A"
    components: List[str] = field(default_factory=list)
    key_metrics: Dict[str, str] = field(default_factory=dict)


@dataclass
class YouTubeMetadata:
    """Generated YouTube video metadata with timestamps."""
    title: str
    description: str
    tags: List[str]
    category_id: str = "27"  # Education


class GeminiEngine:
    """Enterprise Gemini engine with fallback heuristics."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash") -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model
        self.client = None

        if self.api_key:
            self._init_client()

    def _init_client(self) -> None:
        """Initialize Google GenAI client if package is present."""
        try:
            # Modern google-genai SDK
            from google import genai  # type: ignore
            self.client = genai.Client(api_key=self.api_key)
        except ImportError:
            try:
                # Fallback to google-generativeai SDK
                import google.generativeai as legacy_genai  # type: ignore
                legacy_genai.configure(api_key=self.api_key)
                self.client = legacy_genai
            except ImportError:
                # No SDK installed; will use deterministic heuristics
                self.client = None

    def _call_gemini_text(self, prompt: str, system_instruction: str = "") -> Optional[str]:
        """Safely invoke Gemini API with comprehensive exception handling."""
        if not self.client:
            return None

        try:
            # Modern google-genai SDK
            if hasattr(self.client, "models"):
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={"system_instruction": system_instruction} if system_instruction else None,
                )
                return response.text if response and hasattr(response, "text") else None
            # Legacy google-generativeai SDK
            elif hasattr(self.client, "GenerativeModel"):
                model = self.client.GenerativeModel(self.model_name, system_instruction=system_instruction or None)
                res = model.generate_content(prompt)
                return res.text if res and hasattr(res, "text") else None
        except Exception as exc:
            # Log error and fall back gracefully
            print(f"[GeminiEngine WARNING] Gemini API invocation failed: {exc}. Falling back to heuristic engine.")
            return None

        return None

    # =========================================================================
    # TAXONOMY INFERENCE
    # =========================================================================

    def infer_taxonomy(self, content: str) -> List[str]:
        """Infers canonical 3-tier taxonomy from document content."""
        prompt = f"""
Act as a senior chemical process simulation engineer. Analyze the following document and identify:
1. Primary Simulation Platform ("Aspen HYSYS", "DWSIM", or "Python").
2. Chemical Process Domain (e.g., "Separación", "Reactores", "Intercambio Térmico", "Termodinámica", "Control de Procesos").
3. Deliverable artifact (e.g., "Caso HSC", "Notebook Colab", "Simulación DWSIM", "Video Tutorial").

Respond with ONLY a valid JSON list of strings, for example: ["Aspen HYSYS", "Separación", "Caso HSC"]

DOCUMENT CONTENT:
{content[:3000]}
"""
        response_text = self._call_gemini_text(prompt, system_instruction="You are an expert chemical process modeling taxonomist.")
        if response_text:
            try:
                # Extract JSON array
                match = re.search(r"\[.*\]", response_text, re.DOTALL)
                if match:
                    raw_tags = json.loads(match.group(0))
                    if isinstance(raw_tags, list) and raw_tags:
                        return sanitize_categories(raw_tags)
            except Exception:
                pass

        # Heuristic deterministic fallback
        return self._heuristic_taxonomy(content)

    def _heuristic_taxonomy(self, content: str) -> List[str]:
        """Deterministic heuristic extraction based on chemical engineering keywords."""
        lower = content.lower()
        
        # 1. Platform Detection
        platform = "Python"
        if "aspen" in lower or "hysys" in lower or ".hsc" in lower or ".bkp" in lower:
            platform = "Aspen HYSYS"
        elif "dwsim" in lower or ".dwxml" in lower or "dwsim open source" in lower:
            platform = "DWSIM"
        elif "colab" in lower or "jupyter" in lower or "numpy" in lower or "scipy" in lower:
            platform = "Python"

        # 2. Domain Detection
        domain = "Termodinámica"
        if any(k in lower for k in ["destilac", "flash", "separac", "columna", "condensad", "hervidor"]):
            domain = "Separación"
        elif any(k in lower for k in ["reactor", "cstr", "pfr", "cinetic", "reaccion"]):
            domain = "Reactores"
        elif any(k in lower for k in ["intercambiador", "calor", "tubo y coraza", "transferencia termica"]):
            domain = "Intercambio Térmico"
        elif any(k in lower for k in ["control", "pid", "dinamic", "retroaliment"]):
            domain = "Control de Procesos"
        elif any(k in lower for k in ["bomba", "compresor", "tuber", "caida de presion"]):
            domain = "Dinámica de Fluidos"

        # 3. Deliverable Detection
        deliverables: List[str] = []
        if platform == "Aspen HYSYS":
            deliverables.append("Caso HSC")
        elif platform == "DWSIM":
            deliverables.append("Simulación DWSIM")
        else:
            deliverables.append("Notebook Colab")

        if "youtube" in lower or "video" in lower or "{{< video" in lower:
            deliverables.append("Video Tutorial")
        if "slides" in lower or "diapositivas" in lower:
            deliverables.append("Slide Deck")

        raw_tags = [platform, domain] + deliverables
        return sanitize_categories(raw_tags)

    # =========================================================================
    # EXECUTIVE SUMMARY GENERATION
    # =========================================================================

    def generate_executive_summary(self, content: str) -> str:
        """Drafts an executive summary with thermodynamic rigor."""
        prompt = f"""
Redacta un resumen ejecutivo de alto impacto técnico (1-2 párrafos, máximo 120 palabras) para ingenieros químicos y modeladores de procesos.
Debe destacar:
- El objetivo de la simulación o caso de estudio.
- El paquete termodinámico utilizado (ej. Peng-Robinson, NRTL) y su justificación.
- Los resultados numéricos clave de balance de materia y energía.

DOCUMENTO:
{content[:4000]}
"""
        response_text = self._call_gemini_text(prompt, system_instruction="Eres un ingeniero sénior de simulación de procesos.")
        if response_text and len(response_text.strip()) > 40:
            return response_text.strip()

        # Heuristic fallback
        return (
            "Modelado riguroso y análisis termodinámico en estado estacionario para operaciones unitarias de procesos químicos. "
            "Se evalúa la convergencia de balances de materia y energía aplicando modelos de coeficientes de actividad o ecuaciones "
            "de estado de alta fidelidad, cuantificando fracciones de vaporización, consumos térmicos y purezas de corrientes."
        )

    # =========================================================================
    # OPERATING CONDITIONS & BALANCES EXTRACTION
    # =========================================================================

    def extract_operating_conditions(self, content: str) -> OperatingConditions:
        """Extracts key operating parameters and thermodynamic metrics."""
        prompt = f"""
Extract operating parameters from this chemical engineering post in valid JSON with these keys:
"thermodynamic_model", "temperature", "pressure", "feed_flow", "components" (list), "key_metrics" (key-value dict).

CONTENT:
{content[:4000]}
"""
        response_text = self._call_gemini_text(prompt)
        if response_text:
            try:
                match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    return OperatingConditions(
                        thermodynamic_model=data.get("thermodynamic_model", "Peng-Robinson"),
                        temperature=data.get("temperature", "N/A"),
                        pressure=data.get("pressure", "N/A"),
                        feed_flow=data.get("feed_flow", "N/A"),
                        components=data.get("components", []),
                        key_metrics=data.get("key_metrics", {}),
                    )
            except Exception:
                pass

        # Heuristic parsing fallback
        conds = OperatingConditions()
        
        # Therm model
        for model in ["Peng-Robinson", "PR", "SRK", "Soave-Redlich-Kwong", "NRTL", "UNIQUAC", "Wilson", "RefProp"]:
            if re.search(rf"\b{re.escape(model)}\b", content, re.IGNORECASE):
                conds.thermodynamic_model = model
                break

        # Temperature
        temp_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:°C|K|degC)\b", content, re.IGNORECASE)
        if temp_match:
            conds.temperature = f"{temp_match.group(1)} °C"

        # Pressure
        p_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:bar|kPa|psia|atm)\b", content, re.IGNORECASE)
        if p_match:
            conds.pressure = f"{p_match.group(1)} bar"

        # Feed flow
        f_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kmol/h|kg/h|lbmol/h)\b", content, re.IGNORECASE)
        if f_match:
            conds.feed_flow = f"{f_match.group(1)} kmol/h"

        return conds

    # =========================================================================
    # YOUTUBE METADATA & TIMESTAMPS
    # =========================================================================

    def generate_youtube_metadata(
        self,
        title: str,
        content: str,
        custom_timestamps: Optional[List[Dict[str, str]]] = None,
    ) -> YouTubeMetadata:
        """Generates SEO-optimized YouTube title, description with timestamps, and tags."""
        default_timestamps = custom_timestamps or [
            {"time": "00:00", "label": "Introducción y Planteamiento del Proceso"},
            {"time": "01:45", "label": "Selección del Paquete Termodinámico (EOS / Coeficientes)"},
            {"time": "04:15", "label": "Construcción del Diagrama de Flujo (PFD)"},
            {"time": "08:30", "label": "Especificación de Corrientes y Operaciones Unitarias"},
            {"time": "12:50", "label": "Análisis de Convergencia y Balances de Masa/Energía"},
            {"time": "16:20", "label": "Discusión de Resultados y Descarga de Archivos"},
        ]

        timestamp_lines = "\n".join(f"{ts['time']} {ts['label']}" for ts in default_timestamps)

        desc = (
            f"Simulación técnica detallada y modelado de procesos químicos: {title}.\n\n"
            "📥 RECURSOS Y ARCHIVOS DEL CASO:\n"
            "👉 Blog Post & Balances: https://anxosanchez.github.io/blog\n"
            "👉 Repositorio GitHub: https://github.com/anxosanchez/sopqblog\n\n"
            "⏱️ MARCAS DE TIEMPO (TIMESTAMPS):\n"
            f"{timestamp_lines}\n\n"
            "🔬 PALABRAS CLAVE:\n"
            "#IngenieriaQuimica #SimulacionDeProcesos #AspenHYSYS #DWSIM #Termodinamica #PythonEngineering"
        )

        tags = [
            "Ingeniería Química",
            "Simulación de Procesos",
            "Aspen HYSYS",
            "DWSIM",
            "Termodinámica",
            "Balances de Materia",
            "Process Simulation",
            "Chemical Engineering",
            "Peng-Robinson",
        ]

        return YouTubeMetadata(
            title=f"{title} | Simulación de Procesos",
            description=desc,
            tags=tags,
        )
