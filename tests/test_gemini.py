"""Unit and Fallback Tests for Gemini AI Engine."""

import unittest
from pipeline.gemini_engine import GeminiEngine


class TestGeminiEngine(unittest.TestCase):
    """Verifies deterministic heuristic fallbacks and API robustness."""

    def setUp(self):
        # Initialized without API key to test offline / heuristic engine
        self.engine = GeminiEngine(api_key=None)

    def test_heuristic_taxonomy_inference_hysys(self):
        text = "En este caso modelamos una columna debutanizadora en Aspen HYSYS para fraccionamiento de GLP con archivo .hsc."
        tags = self.engine.infer_taxonomy(text)
        self.assertEqual(tags[0], "Aspen HYSYS")
        self.assertIn("Separación", tags)
        self.assertIn("Caso HSC", tags)

    def test_heuristic_taxonomy_inference_dwsim(self):
        text = "Simulación en DWSIM open source de un reactor CSTR exotérmico con chaqueta de refrigeración."
        tags = self.engine.infer_taxonomy(text)
        self.assertEqual(tags[0], "DWSIM")
        self.assertIn("Reactores", tags)
        self.assertIn("Simulación DWSIM", tags)

    def test_executive_summary_fallback(self):
        text = "Balances de flash multicomponente a 78.4 C y 1.20 bar."
        summary = self.engine.generate_executive_summary(text)
        self.assertTrue(len(summary) > 20)
        self.assertIn("termodinámico", summary.lower())

    def test_operating_conditions_extraction(self):
        text = "El tambor opera con modelo Peng-Robinson a 78.4 °C y 1.20 bar con flujo de 100.0 kmol/h."
        conds = self.engine.extract_operating_conditions(text)
        self.assertEqual(conds.thermodynamic_model, "Peng-Robinson")
        self.assertEqual(conds.temperature, "78.4 °C")
        self.assertEqual(conds.pressure, "1.20 bar")
        self.assertEqual(conds.feed_flow, "100.0 kmol/h")

    def test_youtube_metadata_generation(self):
        yt = self.engine.generate_youtube_metadata("Destilación Flash", "Contenido técnico...")
        self.assertIn("Destilación Flash", yt.title)
        self.assertIn("00:00", yt.description)
        self.assertIn("#IngenieriaQuimica", yt.description)
        self.assertTrue(len(yt.tags) >= 5)


if __name__ == "__main__":
    unittest.main()
