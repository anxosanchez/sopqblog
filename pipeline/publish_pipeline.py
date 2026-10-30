#!/usr/bin/env python3
"""End-to-End Automated Publishing Pipeline for Process Simulation Blog.

Orchestrates:
  1. Frontmatter parsing & category sanitization via strict 3-tier taxonomy.
  2. Technical content enrichment via Gemini AI (or deterministic heuristics).
  3. Automated companion Revealjs slide deck synthesis.
  4. YouTube video upload and shortcode/badge injection.
  5. Quarto site integrity audit and compilation.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.gemini_engine import GeminiEngine
from pipeline.slides_generator import SlidesGenerator
from pipeline.taxonomy import sanitize_categories, validate_post_categories
from pipeline.youtube_uploader import YouTubeUploader


class PublishPipeline:
    """Orchestrator for automated blog post publishing."""

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        dry_run: bool = False,
    ) -> None:
        self.dry_run = dry_run
        self.gemini = GeminiEngine(api_key=gemini_api_key)
        self.slides_gen = SlidesGenerator()
        self.uploader = YouTubeUploader()

    def process_post(
        self,
        post_path: str | Path,
        video_path: Optional[str | Path] = None,
        colab_url: Optional[str] = None,
        drive_url: Optional[str] = None,
        generate_slides: bool = True,
        upload_video: bool = False,
    ) -> Dict[str, Any]:
        """Executes full publishing lifecycle for a single post."""
        p_path = Path(post_path)
        if not p_path.exists():
            raise FileNotFoundError(f"Target post not found: {post_path}")

        print(f"\n🚀 [PIPELINE] Processing post: {p_path.name}")
        content = p_path.read_text(encoding="utf-8")

        # -----------------------------------------------------------------
        # STEP 1: Frontmatter Extraction & Taxonomy Sanitization
        # -----------------------------------------------------------------
        print("  [1/5] Auditing frontmatter & enforcing 3-level taxonomy...")
        fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        raw_categories: List[str] = []
        post_title = p_path.stem.replace("caso-", "").replace("-", " ").title()

        if fm_match:
            fm_text = fm_match.group(1)
            # Find categories line
            cat_match = re.search(r"categories:\s*(\[.*?\])", fm_text, re.DOTALL)
            if cat_match:
                try:
                    import ast
                    raw_categories = ast.literal_eval(cat_match.group(1))
                except Exception:
                    pass
            else:
                # Check multiline yaml list
                for line in fm_text.splitlines():
                    if line.strip().startswith("- "):
                        raw_categories.append(line.strip().lstrip("- ").strip('"\''))

            title_m = re.search(r"title:\s*[\"']?(.*?)[\"']?$", fm_text, re.MULTILINE)
            if title_m and title_m.group(1):
                post_title = title_m.group(1).strip()

        # If no categories, infer via Gemini
        if not raw_categories:
            print("    No categories detected; inferring with Gemini...")
            sanitized = self.gemini.infer_taxonomy(content)
        else:
            sanitized = sanitize_categories(raw_categories)

        print(f"    ✓ Canonical categories: {sanitized}")

        # Update categories in frontmatter
        cat_formatted = "[" + ", ".join(f'"{c}"' for c in sanitized) + "]"
        if fm_match:
            fm_text = fm_match.group(1)
            if "categories:" in fm_text:
                fm_text = re.sub(r"categories:\s*(\[.*?\]|.*?\n(?!\s*-))", f"categories: {cat_formatted}\n", fm_text)
            else:
                fm_text += f"\ncategories: {cat_formatted}\n"
            content = f"---\n{fm_text.strip()}\n---\n" + content[fm_match.end():]
            p_path.write_text(content, encoding="utf-8")

        # -----------------------------------------------------------------
        # STEP 2: Companion Slide Deck Synthesis
        # -----------------------------------------------------------------
        slides_path: Optional[Path] = None
        slides_url: Optional[str] = None
        if generate_slides:
            print("  [2/5] Synthesizing companion Revealjs presentation...")
            slides_path = self.slides_gen.generate_slides_qmd(p_path)
            slides_url = slides_path.name
            print(f"    ✓ Generated presentation: {slides_path.name}")

        # -----------------------------------------------------------------
        # STEP 3: Video Upload & Shortcode Injection
        # -----------------------------------------------------------------
        video_url: Optional[str] = None
        if video_path:
            v_p = Path(video_path)
            if v_p.exists() or self.dry_run:
                print(f"  [3/5] Handling video simulation ({v_p.name})...")
                # Generate YouTube metadata
                yt_meta = self.gemini.generate_youtube_metadata(post_title, content)
                upload_res = self.uploader.upload_video(
                    video_path=v_p,
                    title=yt_meta.title,
                    description=yt_meta.description,
                    tags=yt_meta.tags,
                    dry_run=self.dry_run or not upload_video,
                )
                if upload_res.success:
                    video_url = upload_res.video_url
                    print(f"    ✓ Video registered: {video_url}")

        # -----------------------------------------------------------------
        # STEP 4: Resource Badges & Shortcodes Injection
        # -----------------------------------------------------------------
        print("  [4/5] Injecting resource badges and video embed...")
        self.uploader.inject_video_and_badges(
            post_path=p_path,
            video_url=video_url or "",
            colab_url=colab_url,
            drive_url=drive_url,
            slides_url=slides_url,
        )
        print("    ✓ Post content updated.")

        # -----------------------------------------------------------------
        # STEP 5: Verification & Integrity
        # -----------------------------------------------------------------
        print("  [5/5] Auditing integrity...")
        is_valid, errors = validate_post_categories(sanitized)
        if not is_valid:
            print(f"    ⚠️ Warning: Category validation issues: {errors}")
        else:
            print("    ✓ All taxonomic tiers strictly satisfied.")

        return {
            "post_path": str(p_path),
            "categories": sanitized,
            "slides_path": str(slides_path) if slides_path else None,
            "video_url": video_url,
            "valid": is_valid,
        }

    def check_all_posts(self, posts_dir: str | Path = "posts") -> bool:
        """Audits all posts in directory for frontmatter integrity and taxonomy."""
        p_dir = Path(posts_dir)
        all_valid = True
        print(f"\n🔍 [AUDIT] Inspecting all posts in {p_dir.resolve()}...")

        qmd_files = [f for f in p_dir.glob("*.qmd") if not f.name.startswith("_") and not f.name.startswith("slides-")]
        if not qmd_files:
            print("  No article posts found to audit.")
            return True

        for post in qmd_files:
            content = post.read_text(encoding="utf-8")
            fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
            if not fm_match:
                print(f"  ❌ {post.name}: Missing YAML frontmatter.")
                all_valid = False
                continue

            fm_text = fm_match.group(1)
            cat_match = re.search(r"categories:\s*(\[.*?\])", fm_text, re.DOTALL)
            if not cat_match:
                print(f"  ❌ {post.name}: Missing 'categories' field.")
                all_valid = False
                continue

            try:
                import ast
                categories = ast.literal_eval(cat_match.group(1))
            except Exception:
                categories = [c.strip().strip('"\'') for c in cat_match.group(1).strip("[]").split(",") if c.strip()]

            is_valid, errors = validate_post_categories(categories)
            if not is_valid:
                print(f"  ❌ {post.name}: Taxonomy violation: {errors}")
                all_valid = False
            else:
                print(f"  ✓ {post.name} [{categories[0]} | {categories[1]} | {categories[2]}]")

        return all_valid

    @staticmethod
    def render_quarto(quarto_bin: Optional[str] = None) -> bool:
        """Executes quarto render with proper binary detection."""
        # Find quarto binary
        candidate_paths = [
            quarto_bin,
            shutil.which("quarto"),
            "/Applications/Positron.app/Contents/Resources/app/quarto/bin/quarto",
            "/opt/homebrew/bin/quarto",
            "/usr/local/bin/quarto",
        ]
        q_bin = next((p for p in candidate_paths if p and os.path.exists(p)), None)

        if not q_bin:
            print("⚠️ [RENDER WARNING] Quarto executable not found in PATH or standard paths.")
            return False

        print(f"\n🔨 [RENDER] Compiling Quarto site using '{q_bin}'...")
        try:
            res = subprocess.run([q_bin, "render", "--quiet"], check=True, capture_output=True, text=True)
            if res.stdout:
                print(res.stdout)
            print("✓ Quarto render completed successfully!")
            return True
        except subprocess.CalledProcessError as exc:
            print(f"❌ Quarto render failed with code {exc.returncode}:\n{exc.stderr}")
            return False


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Automated Publishing Pipeline for Chemical Process Simulation Blog.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--post", type=str, help="Path to .qmd or .ipynb post file.")
    parser.add_argument("--video", type=str, default=None, help="Path to simulation video (.mp4).")
    parser.add_argument("--colab-url", type=str, default=None, help="Google Colab link.")
    parser.add_argument("--drive-url", type=str, default=None, help="Google Drive link for simulation files.")
    parser.add_argument("--no-slides", action="store_true", help="Disable automatic Revealjs slide deck generation.")
    parser.add_argument("--upload-youtube", action="store_true", help="Upload video to YouTube Data API v3.")
    parser.add_argument("--dry-run", action="store_true", help="Execute without external API calls or real uploads.")
    parser.add_argument("--check-all", action="store_true", help="Audit all posts in posts/ for taxonomy compliance.")
    parser.add_argument("--render", action="store_true", help="Compile the Quarto site after processing.")

    args = parser.parse_args()

    pipeline = PublishPipeline(dry_run=args.dry_run)

    if args.check_all:
        valid = pipeline.check_all_posts()
        if not valid:
            sys.exit(1)

    if args.post:
        res = pipeline.process_post(
            post_path=args.post,
            video_path=args.video,
            colab_url=args.colab_url,
            drive_url=args.drive_url,
            generate_slides=not args.no_slides,
            upload_video=args.upload_youtube,
        )
        print(f"\n✨ Post processing complete: {res['post_path']}")

    if args.render:
        success = pipeline.render_quarto()
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
