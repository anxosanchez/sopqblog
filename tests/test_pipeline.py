"""Unit and Integration Tests for Publishing Pipeline & YouTube Uploader."""

import unittest
from pathlib import Path
from pipeline.publish_pipeline import PublishPipeline
from pipeline.youtube_uploader import YouTubeUploader


class TestYouTubeUploader(unittest.TestCase):
    """Verifies YouTube uploader mock modes and HTML badge injection."""

    def setUp(self):
        self.uploader = YouTubeUploader()

    def test_dry_run_upload(self):
        res = self.uploader.upload_video(
            video_path="test_video.mp4",
            title="Prueba de Upload",
            description="Descripción técnica",
            dry_run=True,
        )
        self.assertTrue(res.success)
        self.assertTrue(res.is_mock)
        self.assertIn("https://www.youtube.com/watch?v=", res.video_url)

    def test_badge_and_video_injection_idempotency(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            post_file = Path(tmp_dir) / "post.qmd"
            initial_content = """---
title: "Post de Prueba"
categories: ["Python", "Termodinámica", "Notebook Colab"]
---

## 1. Introducción
Contenido inicial...

## Conclusiones
Fin.
"""
            post_file.write_text(initial_content, encoding="utf-8")

            # First injection
            self.uploader.inject_video_and_badges(
                post_path=post_file,
                video_url="https://www.youtube.com/watch?v=12345",
                colab_url="https://colab.research.google.com/test",
                drive_url="https://drive.google.com/test",
                slides_url="slides-test.html",
            )
            content_1 = post_file.read_text(encoding="utf-8")
            self.assertEqual(content_1.count('<div class="resource-badge-bar">'), 1)
            self.assertEqual(content_1.count("{{< video https://www.youtube.com/watch?v=12345 >}}"), 1)

            # Second injection (must be idempotent, not duplicate badges or video)
            self.uploader.inject_video_and_badges(
                post_path=post_file,
                video_url="https://www.youtube.com/watch?v=12345",
                colab_url="https://colab.research.google.com/test",
                drive_url="https://drive.google.com/test",
                slides_url="slides-test.html",
            )
            content_2 = post_file.read_text(encoding="utf-8")
            self.assertEqual(content_2.count('<div class="resource-badge-bar">'), 1)
            self.assertEqual(content_2.count("{{< video https://www.youtube.com/watch?v=12345 >}}"), 1)


class TestPublishPipeline(unittest.TestCase):
    """Verifies pipeline audit and processing."""

    def setUp(self):
        self.pipeline = PublishPipeline(dry_run=True)

    def test_check_all_posts(self):
        # Must audit existing posts in posts/
        valid = self.pipeline.check_all_posts(posts_dir="posts")
        self.assertTrue(valid)


if __name__ == "__main__":
    unittest.main()
