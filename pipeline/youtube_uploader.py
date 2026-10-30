"""YouTube Data API v3 Automated Uploader & Quarto Shortcode Injector.

Handles:
  - Resumable OAuth2 video uploads to YouTube.
  - Token persistence and refresh flow.
  - Graceful dry-run and offline mocking for testing/CI environments.
  - Idempotent injection of Quarto video shortcodes ({{< video ... >}}) and
    resource badges (Colab, Drive, Revealjs, YouTube) into post frontmatter/body.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class UploadResult:
    """Result of YouTube upload execution."""
    video_id: str
    video_url: str
    title: str
    success: bool
    is_mock: bool = False
    error: Optional[str] = None


class YouTubeUploader:
    """Enterprise YouTube Uploader with OAuth2 resumable upload."""

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    def __init__(
        self,
        client_secrets_file: Optional[str] = None,
        credentials_token_file: Optional[str] = None,
    ) -> None:
        self.client_secrets_file = client_secrets_file or os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json")
        self.credentials_token_file = credentials_token_file or os.getenv("YOUTUBE_TOKEN_FILE", "token.json")

    def _get_authenticated_service(self):
        """Constructs an authenticated YouTube API client or raises exception."""
        from google.oauth2.credentials import Credentials  # type: ignore
        from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
        from googleapiclient.discovery import build  # type: ignore
        from google.auth.transport.requests import Request  # type: ignore

        creds = None
        if os.path.exists(self.credentials_token_file):
            creds = Credentials.from_authorized_user_file(self.credentials_token_file, self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError(
                        f"YouTube client secrets file '{self.client_secrets_file}' not found. "
                        "Please provide credentials or run with --dry-run."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, self.SCOPES)
                creds = flow.run_local_server(port=0)

            with open(self.credentials_token_file, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())

        return build("youtube", "v3", credentials=creds)

    def upload_video(
        self,
        video_path: str | Path,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        privacy_status: str = "unlisted",
        dry_run: bool = False,
    ) -> UploadResult:
        """Uploads a video to YouTube with resumable protocol or mock mode."""
        v_path = Path(video_path)
        if not v_path.exists() and not dry_run:
            raise FileNotFoundError(f"Video file not found at: {video_path}")

        if dry_run or not os.path.exists(self.client_secrets_file):
            # Deterministic mock ID based on filename
            mock_id = f"demo_{v_path.stem[:8]}"
            mock_url = f"https://www.youtube.com/watch?v={mock_id}"
            print(f"[YouTubeUploader DRY-RUN] Simulating upload for '{v_path.name}'. Video ID: {mock_id}")
            return UploadResult(
                video_id=mock_id,
                video_url=mock_url,
                title=title,
                success=True,
                is_mock=True,
            )

        try:
            from googleapiclient.http import MediaFileUpload  # type: ignore

            youtube = self._get_authenticated_service()

            body = {
                "snippet": {
                    "title": title[:100],
                    "description": description[:5000],
                    "tags": tags or ["Chemical Engineering", "Process Simulation"],
                    "categoryId": "27",  # Education
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False,
                },
            }

            media = MediaFileUpload(
                str(v_path),
                mimetype="video/*",
                resumable=True,
                chunksize=1024 * 1024 * 4,  # 4MB chunks
            )

            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            response = None

            print(f"[YouTubeUploader] Starting resumable upload for '{v_path.name}'...")
            while response is None:
                status, response = request.next_chunk()
                if status:
                    pct = int(status.progress() * 100)
                    print(f"  Uploading chunk... {pct}% complete")

            video_id = response.get("id")
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"[YouTubeUploader] Upload successful! URL: {video_url}")

            return UploadResult(
                video_id=video_id,
                video_url=video_url,
                title=title,
                success=True,
                is_mock=False,
            )

        except Exception as exc:
            err_msg = f"Failed to upload video: {exc}"
            print(f"[YouTubeUploader ERROR] {err_msg}")
            return UploadResult(
                video_id="",
                video_url="",
                title=title,
                success=False,
                error=err_msg,
            )

    @staticmethod
    def inject_video_and_badges(
        post_path: str | Path,
        video_url: str,
        colab_url: Optional[str] = None,
        drive_url: Optional[str] = None,
        slides_url: Optional[str] = None,
    ) -> Path:
        """Injects Quarto video shortcode and resource badge bar idempotently."""
        p_path = Path(post_path)
        content = p_path.read_text(encoding="utf-8")

        # 1. Build Badge Bar HTML
        badges_html_parts = ['<div class="resource-badge-bar">', '<span class="badge-label">Recursos del Caso:</span>']

        if colab_url:
            badges_html_parts.append(
                f'<a href="{colab_url}" target="_blank" rel="noopener" class="resource-badge resource-badge-colab">'
                f'⚡ Abrir en Google Colab</a>'
            )

        if drive_url:
            badges_html_parts.append(
                f'<a href="{drive_url}" target="_blank" rel="noopener" class="resource-badge resource-badge-drive">'
                f'📁 Descargar Simulación (.hsc / .bkp)</a>'
            )

        if slides_url:
            badges_html_parts.append(
                f'<a href="{slides_url}" target="_blank" rel="noopener" class="resource-badge resource-badge-slides">'
                f'📊 Ver Diapositivas Revealjs</a>'
            )

        if video_url:
            badges_html_parts.append(
                f'<a href="{video_url}" target="_blank" rel="noopener" class="resource-badge resource-badge-youtube">'
                f'▶ Ver en YouTube</a>'
            )

        badges_html_parts.append('</div>')
        badge_bar_html = "\n".join(badges_html_parts)

        # 2. Check if badge bar already exists
        if '<div class="resource-badge-bar">' in content:
            # Replace existing badge bar
            content = re.sub(
                r'<div class="resource-badge-bar">.*?</div>',
                badge_bar_html,
                content,
                flags=re.DOTALL,
            )
        else:
            # Inject right after frontmatter
            fm_end = re.search(r"^---\s*\n.*?\n---\s*\n", content, re.DOTALL)
            if fm_end:
                idx = fm_end.end()
                content = content[:idx] + "\n" + badge_bar_html + "\n\n" + content[idx:]
            else:
                content = badge_bar_html + "\n\n" + content

        # 3. Inject video shortcode if video_url provided and not already present
        if video_url:
            video_shortcode = f"{{{{< video {video_url} >}}}}"
            if "{{< video" in content:
                # Replace existing video shortcode
                content = re.sub(r"\{\{<\s*video\s+[^>]+>\}\}", video_shortcode, content)
            else:
                # Find Video section or append before conclusions
                video_section_match = re.search(r"(##\s+(?:Video\s+Tutorial|Simulación\s+en\s+Vídeo|Video\s+Explicativo)[^\n]*\n)", content, re.IGNORECASE)
                if video_section_match:
                    pos = video_section_match.end()
                    content = content[:pos] + f"\n{video_shortcode}\n\n" + content[pos:]
                else:
                    # Append video section before Conclusiones or at the end
                    conclusions_match = re.search(r"(##\s+Conclusiones)", content, re.IGNORECASE)
                    if conclusions_match:
                        pos = conclusions_match.start()
                        video_block = f"## Video Tutorial y Demostración Operacional\n\n{video_shortcode}\n\n"
                        content = content[:pos] + video_block + content[pos:]
                    else:
                        content += f"\n\n## Video Tutorial y Demostración Operacional\n\n{video_shortcode}\n"

        p_path.write_text(content, encoding="utf-8")
        return p_path
