"""Taxonomy Governance Module for Process Simulation Blog.

Enforces a strict 3-level orthogonal taxonomy:
  - Level 1: Canonical Simulation Platform ("Aspen HYSYS", "DWSIM", "Python")
  - Level 2: Chemical Process Domain ("Separación", "Reactores", "Intercambio Térmico", ...)
  - Level 3: Deliverable Artifact Type ("Caso HSC", "Notebook Colab", "Video Tutorial", ...)

Normalizes synonyms, eliminates casing/accent discrepancies, prevents duplicate tags,
and guarantees clean filtering in the Quarto exploration hub.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


class TaxonomyLevel(str, Enum):
    """Hierarchical taxonomic tiers."""
    PLATFORM = "Platform"
    DOMAIN = "Domain"
    DELIVERABLE = "Deliverable"


# =============================================================================
# CANONICAL TAXONOMY DICTIONARIES & SYNONYM MAPPINGS
# =============================================================================

CANONICAL_PLATFORMS: Dict[str, str] = {
    # Key: normalized token -> Value: Canonical Name
    "aspen hysys": "Aspen HYSYS",
    "hysys": "Aspen HYSYS",
    "aspen": "Aspen HYSYS",
    "aspenone": "Aspen HYSYS",
    "hysys v12": "Aspen HYSYS",
    "hysys v14": "Aspen HYSYS",
    "aspen plus": "Aspen HYSYS",  # Normalized to core Aspen suite
    
    "dwsim": "DWSIM",
    "dwsim open source": "DWSIM",
    "dwsim v8": "DWSIM",
    "dwsim v7": "DWSIM",
    "open source": "DWSIM",
    
    "python": "Python",
    "python & termodinamica": "Python",
    "python termodinamica": "Python",
    "colab": "Python",
    "google colab": "Python",
    "jupyter": "Python",
    "jupyter notebook": "Python",
    "biosteam": "Python",
    "scipy": "Python",
    "cantera": "Python",
    "thermo": "Python",
}

CANONICAL_DOMAINS: Dict[str, str] = {
    # Separation
    "separacion": "Separación",
    "separacion de mezclas": "Separación",
    "destilacion": "Separación",
    "distillation": "Separación",
    "flash": "Separación",
    "absorcion": "Separación",
    "stripping": "Separación",
    "extraccion": "Separación",
    "columnas": "Separación",
    "rectificacion": "Separación",
    
    # Reactors & Kinetics
    "reactores": "Reactores",
    "reactor": "Reactores",
    "cinetica": "Reactores",
    "cinetica quimica": "Reactores",
    "cstr": "Reactores",
    "pfr": "Reactores",
    "pbr": "Reactores",
    "reactores quimicos": "Reactores",
    "conversion": "Reactores",
    "equilibrio quimico": "Reactores",

    # Heat Exchange
    "intercambio termico": "Intercambio Térmico",
    "intercambiador": "Intercambio Térmico",
    "intercambiadores": "Intercambio Térmico",
    "transferencia de calor": "Intercambio Térmico",
    "heat exchanger": "Intercambio Térmico",
    "reboiler": "Intercambio Térmico",
    "condensador": "Intercambio Térmico",
    "redes de intercambio": "Intercambio Térmico",

    # Thermodynamics & Phase Equilibria
    "termodinamica": "Termodinámica",
    "thermodynamics": "Termodinámica",
    "vle": "Termodinámica",
    "lle": "Termodinámica",
    "vlfe": "Termodinámica",
    "equilibrio de fases": "Termodinámica",
    "ecuaciones de estado": "Termodinámica",
    "eos": "Termodinámica",
    "peng robinson": "Termodinámica",
    "nrtl": "Termodinámica",
    "srk": "Termodinámica",
    "actividad": "Termodinámica",

    # Process Control & Dynamics
    "control de procesos": "Control de Procesos",
    "control": "Control de Procesos",
    "dinamica": "Control de Procesos",
    "sintonia": "Control de Procesos",
    "pid": "Control de Procesos",
    "control avanzado": "Control de Procesos",

    # Utilities & Piping
    "servicios industriales": "Servicios Industriales",
    "utilities": "Servicios Industriales",
    "vapor": "Servicios Industriales",
    "redes de vapor": "Servicios Industriales",
    "agua de enfriamiento": "Servicios Industriales",

    # Fluid Flow & Turbomachinery
    "dinamica de fluidos": "Dinámica de Fluidos",
    "fluidos": "Dinámica de Fluidos",
    "bombas": "Dinámica de Fluidos",
    "compresores": "Dinámica de Fluidos",
    "tuberias": "Dinámica de Fluidos",
    "caida de presion": "Dinámica de Fluidos",

    # Optimization & Synthesis
    "optimizacion": "Optimización",
    "optimization": "Optimización",
    "analisis pinch": "Optimización",
    "pinch": "Optimización",
    "integracion energetica": "Optimización",
}

CANONICAL_DELIVERABLES: Dict[str, str] = {
    "caso hsc": "Caso HSC",
    "hsc": "Caso HSC",
    "archivo hsc": "Caso HSC",
    "aspen case": "Caso HSC",
    "bkp": "Caso HSC",
    
    "simulacion dwsim": "Simulación DWSIM",
    "dwsim file": "Simulación DWSIM",
    "dwxml": "Simulación DWSIM",
    
    "notebook colab": "Notebook Colab",
    "colab notebook": "Notebook Colab",
    "jupyter notebook": "Notebook Colab",
    "codigo python": "Notebook Colab",
    "script python": "Notebook Colab",
    
    "video tutorial": "Video Tutorial",
    "video": "Video Tutorial",
    "youtube": "Video Tutorial",
    "screencast": "Video Tutorial",
    
    "slide deck": "Slide Deck",
    "presentacion": "Slide Deck",
    "diapositivas": "Slide Deck",
    "revealjs": "Slide Deck",
}


def normalize_token(text: str) -> str:
    """Strip accents, lowercase, and eliminate punctuation/extra spaces."""
    if not text:
        return ""
    # NFKD decomposition to separate characters from diacritics
    nfkd = unicodedata.normalize("NFKD", text)
    cleaned = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Replace common symbols with space and lower
    cleaned = cleaned.replace("_", " ").replace("-", " ").replace("/", " ")
    tokens = [t.strip() for t in cleaned.lower().split() if t.strip()]
    return " ".join(tokens)


@dataclass
class TaxonomyResolution:
    """Resolved taxonomic entities with metadata."""
    platforms: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    unrecognized: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """True if exactly 1 platform, >=1 domain, and >=1 deliverable exist."""
        return (len(self.platforms) == 1) and (len(self.domains) >= 1) and (len(self.deliverables) >= 1)

    @property
    def canonical_categories(self) -> List[str]:
        """Ordered list conforming to Quarto listing standards:
        [Platform, Domain(s), Deliverable(s)] without duplicates."""
        out: List[str] = []
        for p in self.platforms:
            if p not in out:
                out.append(p)
        for d in self.domains:
            if d not in out:
                out.append(d)
        for deliv in self.deliverables:
            if deliv not in out:
                out.append(deliv)
        return out


class TaxonomyValidator:
    """Enterprise-grade taxonomy validator and sanitizer."""

    def __init__(self) -> None:
        self.platforms = CANONICAL_PLATFORMS
        self.domains = CANONICAL_DOMAINS
        self.deliverables = CANONICAL_DELIVERABLES

    def resolve(self, raw_tags: Sequence[str]) -> TaxonomyResolution:
        """Parse raw tag strings and assign to orthogonal taxonomic tiers."""
        res = TaxonomyResolution()

        for tag in raw_tags:
            token = normalize_token(tag)
            if not token:
                continue

            matched = False

            # Check Platform
            if token in self.platforms:
                canonical = self.platforms[token]
                if canonical not in res.platforms:
                    res.platforms.append(canonical)
                matched = True

            # Check Domain
            if token in self.domains:
                canonical = self.domains[token]
                if canonical not in res.domains:
                    res.domains.append(canonical)
                matched = True

            # Check Deliverable
            if token in self.deliverables:
                canonical = self.deliverables[token]
                if canonical not in res.deliverables:
                    res.deliverables.append(canonical)
                matched = True

            if not matched:
                # Sub-string / keyword heuristics fallback
                if "hysys" in token or "aspen" in token:
                    if "Aspen HYSYS" not in res.platforms:
                        res.platforms.append("Aspen HYSYS")
                    matched = True
                elif "dwsim" in token:
                    if "DWSIM" not in res.platforms:
                        res.platforms.append("DWSIM")
                    matched = True
                elif "python" in token or "colab" in token:
                    if "Python" not in res.platforms:
                        res.platforms.append("Python")
                    matched = True

                if "separac" in token or "destil" in token or "flash" in token:
                    if "Separación" not in res.domains:
                        res.domains.append("Separación")
                    matched = True
                elif "termo" in token or "equilibri" in token:
                    if "Termodinámica" not in res.domains:
                        res.domains.append("Termodinámica")
                    matched = True
                elif "reactor" in token or "cinetic" in token:
                    if "Reactores" not in res.domains:
                        res.domains.append("Reactores")
                    matched = True

                if "video" in token or "youtube" in token:
                    if "Video Tutorial" not in res.deliverables:
                        res.deliverables.append("Video Tutorial")
                    matched = True
                elif "hsc" in token or "bkp" in token:
                    if "Caso HSC" not in res.deliverables:
                        res.deliverables.append("Caso HSC")
                    matched = True
                elif "slide" in token or "presentac" in token:
                    if "Slide Deck" not in res.deliverables:
                        res.deliverables.append("Slide Deck")
                    matched = True

            if not matched:
                res.unrecognized.append(tag.strip())

        return res

    def sanitize(
        self,
        raw_tags: Sequence[str],
        default_platform: str = "Python",
        default_domain: str = "Termodinámica",
        default_deliverable: str = "Notebook Colab",
    ) -> List[str]:
        """Sanitizes raw tags and returns a guaranteed valid orthogonal category list.
        
        If any tier is missing, it injects the specified default tier to ensure the
        post appears correctly in the Quarto exploration tabs and listings.
        """
        resolution = self.resolve(raw_tags)

        # Enforce exactly one platform
        if not resolution.platforms:
            resolution.platforms.append(default_platform)
        elif len(resolution.platforms) > 1:
            # Preserve the first valid platform
            resolution.platforms = [resolution.platforms[0]]

        # Enforce at least one domain
        if not resolution.domains:
            resolution.domains.append(default_domain)

        # Enforce at least one deliverable
        if not resolution.deliverables:
            # Infer deliverable from platform if possible
            if resolution.platforms[0] == "Aspen HYSYS":
                resolution.deliverables.append("Caso HSC")
            elif resolution.platforms[0] == "DWSIM":
                resolution.deliverables.append("Simulación DWSIM")
            else:
                resolution.deliverables.append(default_deliverable)

        return resolution.canonical_categories


# Module-level convenience functions
_DEFAULT_VALIDATOR = TaxonomyValidator()


def sanitize_categories(
    raw_categories: Sequence[str],
    default_platform: str = "Python",
    default_domain: str = "Termodinámica",
    default_deliverable: str = "Notebook Colab",
) -> List[str]:
    """Canonical category sanitizer for Quarto posts."""
    return _DEFAULT_VALIDATOR.sanitize(
        raw_categories,
        default_platform=default_platform,
        default_domain=default_domain,
        default_deliverable=default_deliverable,
    )


def validate_post_categories(categories: Sequence[str]) -> Tuple[bool, List[str]]:
    """Validates whether a post adheres strictly to the 3-level orthogonal taxonomy.
    
    Returns (is_valid, error_messages).
    """
    resolution = _DEFAULT_VALIDATOR.resolve(categories)
    errors: List[str] = []

    if len(resolution.platforms) == 0:
        errors.append("Missing Level 1 Platform: must include 'Aspen HYSYS', 'DWSIM', or 'Python'.")
    elif len(resolution.platforms) > 1:
        errors.append(f"Ambiguous Level 1 Platform: multiple specified ({resolution.platforms}). Exactly one allowed.")

    if len(resolution.domains) == 0:
        errors.append("Missing Level 2 Process Domain: e.g. 'Separación', 'Reactores', 'Termodinámica', etc.")

    if len(resolution.deliverables) == 0:
        errors.append("Missing Level 3 Deliverable: e.g. 'Caso HSC', 'Notebook Colab', 'Video Tutorial', etc.")

    if resolution.unrecognized:
        errors.append(f"Unrecognized non-canonical categories: {resolution.unrecognized}")

    return (len(errors) == 0, errors)
