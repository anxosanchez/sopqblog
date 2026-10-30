"""Unit Tests for Slide Deck Generator."""

import unittest
from pathlib import Path
from pipeline.slides_generator import SlidesGenerator


class TestSlidesGenerator(unittest.TestCase):
    """Verifies synthesis of technical articles into Revealjs presentations."""

    def setUp(self):
        self.generator = SlidesGenerator()
        self.sample_qmd = """---
title: "Prueba de Simulación"
subtitle: "Subtítulo de Prueba"
author: "Ingeniero Químico"
date: "2026-10-30"
categories: ["Python", "Separación", "Notebook Colab"]
---

::: {.metric-grid}
::: {.metric-card}
<div class="metric-header">Temperatura</div>
<div class="metric-value">80.0<span class="metric-unit">°C</span></div>
:::
:::

$$
f(\\psi) = 0
$$

| C | Val |
|---|---|
| A | 10  |
"""

    def test_parse_post(self):
        data = self.generator.parse_post(self.sample_qmd)
        self.assertEqual(data["title"], "Prueba de Simulación")
        self.assertEqual(data["subtitle"], "Subtítulo de Prueba")
        self.assertEqual(data["categories"], ["Python", "Separación", "Notebook Colab"])
        self.assertEqual(len(data["metrics"]), 1)
        self.assertEqual(data["metrics"][0]["value"], "80.0 °C")
        self.assertTrue(len(data["equations"]) >= 1)

    def test_generate_slides_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            post_file = Path(tmp_dir) / "test-post.qmd"
            post_file.write_text(self.sample_qmd, encoding="utf-8")
            
            slides_path = self.generator.generate_slides_qmd(post_file)
            self.assertTrue(slides_path.exists())
            content = slides_path.read_text(encoding="utf-8")
            self.assertIn("format:\n  revealjs:", content)
            self.assertIn("Prueba de Simulación", content)
            self.assertIn("80.0 °C", content)


if __name__ == "__main__":
    unittest.main()
