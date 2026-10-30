"""Unit and Adversarial Tests for Taxonomy Governance Module."""

import unittest
from pipeline.taxonomy import (
    TaxonomyValidator,
    normalize_token,
    sanitize_categories,
    validate_post_categories,
)


class TestTaxonomyNormalization(unittest.TestCase):
    """Verifies string token normalization and accent stripping."""

    def test_accent_and_casing_stripping(self):
        self.assertEqual(normalize_token("Separación"), "separacion")
        self.assertEqual(normalize_token("Térmico"), "termico")
        self.assertEqual(normalize_token("  ASPEN HYSYS  "), "aspen hysys")
        self.assertEqual(normalize_token("DWSIM-Open_Source"), "dwsim open source")
        self.assertEqual(normalize_token(""), "")


class TestTaxonomySanitization(unittest.TestCase):
    """Verifies canonical 3-tier mapping and orthogonality."""

    def setUp(self):
        self.validator = TaxonomyValidator()

    def test_canonical_platforms(self):
        # Aspen synonyms
        for tag in ["hysys", "aspen", "ASPEN HYSYS", "hysys v12"]:
            cats = sanitize_categories([tag])
            self.assertEqual(cats[0], "Aspen HYSYS")

        # DWSIM synonyms
        for tag in ["dwsim", "dwsim open source", "DWSIM v8"]:
            cats = sanitize_categories([tag])
            self.assertEqual(cats[0], "DWSIM")

        # Python synonyms
        for tag in ["python", "colab", "jupyter", "biosteam"]:
            cats = sanitize_categories([tag])
            self.assertEqual(cats[0], "Python")

    def test_canonical_domains(self):
        cats = sanitize_categories(["hysys", "destilacion", "hsc"])
        self.assertIn("Separación", cats)

        cats = sanitize_categories(["python", "reactores quimicos", "colab"])
        self.assertIn("Reactores", cats)

        cats = sanitize_categories(["dwsim", "intercambiadores", "dwxml"])
        self.assertIn("Intercambio Térmico", cats)

    def test_canonical_deliverables(self):
        cats = sanitize_categories(["python", "termodinamica", "colab notebook"])
        self.assertIn("Notebook Colab", cats)

        cats = sanitize_categories(["hysys", "separacion", "video"])
        self.assertIn("Video Tutorial", cats)

    def test_adversarial_hybrid_and_messy_inputs(self):
        """Red Team Auditor: test chaotic inputs and verify clean output."""
        messy_input = ["   hYsYs   ", "  SEPARACIÓN  ", "dEstilaCiOn", "VIDEO TUTORIAL", "HYSYS"]
        sanitized = sanitize_categories(messy_input)

        # Must not contain duplicates
        self.assertEqual(len(sanitized), len(set(sanitized)))
        # Must contain exactly 1 platform
        platforms = [c for c in sanitized if c in ["Aspen HYSYS", "DWSIM", "Python"]]
        self.assertEqual(len(platforms), 1)
        self.assertEqual(platforms[0], "Aspen HYSYS")
        # Must contain canonical domain
        self.assertIn("Separación", sanitized)
        # Must contain deliverable
        self.assertIn("Video Tutorial", sanitized)

    def test_missing_tiers_injection(self):
        """When user provides only a domain, defaults must be injected."""
        cats = sanitize_categories(["destilacion"])
        self.assertEqual(cats[0], "Python")  # default platform
        self.assertIn("Separación", cats)
        self.assertIn("Notebook Colab", cats)  # default deliverable

    def test_validation_function(self):
        valid, errors = validate_post_categories(["Aspen HYSYS", "Separación", "Caso HSC"])
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

        # Invalid: missing platform
        valid, errors = validate_post_categories(["Separación", "Caso HSC"])
        self.assertFalse(valid)
        self.assertTrue(any("Missing Level 1" in e for e in errors))

        # Invalid: multiple platforms
        valid, errors = validate_post_categories(["Aspen HYSYS", "DWSIM", "Separación", "Caso HSC"])
        self.assertFalse(valid)
        self.assertTrue(any("multiple specified" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
