"""
pipeline/telegram_editor_notifier.py
====================================
Notificador automatizado para Telegram do Editor de SOPQ // ProcessSim.

Permite alertar ao editor xefe (Anxo Sánchez) cando se propón unha nova entrada,
se abre unha Pull Request ou se detecta un novo borrador para supervisión editorial.
Funciona con cero dependencias externas usando urllib estándar de Python.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


class TelegramEditorNotifier:
    """Xestiona o envío de alertas e avisos editoriais ao bot de Telegram."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> None:
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "").strip()
        self.dry_run = dry_run or not (self.bot_token and self.chat_id)

    @classmethod
    def from_env(cls, dry_run: bool = False) -> "TelegramEditorNotifier":
        return cls(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            dry_run=dry_run or (os.getenv("TELEGRAM_BOT_TOKEN") is None),
        )

    def parse_post_metadata(self, post_path: Path | str) -> Dict[str, Any]:
        """Extrae metadatos esenciais do frontmatter do post."""
        path = Path(post_path)
        if not path.is_file():
            raise FileNotFoundError(f"Non se atopou o arquivo de post: {post_path}")

        content = path.read_text(encoding="utf-8")
        metadata: Dict[str, Any] = {
            "title": path.stem,
            "subtitle": "",
            "authors": [],
            "categories": [],
            "date": "",
            "is_draft": False,
            "has_hsc": ".hsc" in content,
            "has_dwxml": ".dwxml" in content,
            "has_colab": "colab" in content.lower(),
            "has_video": "{{< video" in content or "youtube" in content.lower(),
        }

        fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if fm_match:
            raw_yaml = fm_match.group(1)
            for line in raw_yaml.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip('"\'')
                    if k == "title" and v:
                        metadata["title"] = v
                    elif k == "subtitle" and v:
                        metadata["subtitle"] = v
                    elif k == "date" and v:
                        metadata["date"] = v
                    elif k == "draft":
                        metadata["is_draft"] = v.lower() in ("true", "1", "yes")
                    elif k == "author" and v:
                        metadata["authors"].append(v)
                    elif k == "name" and v:
                        metadata["authors"].append(v)
                    elif k == "categories" and v:
                        cats = [c.strip().strip('"\'') for c in v.strip("[]").split(",") if c.strip()]
                        metadata["categories"] = cats

        if not metadata["authors"]:
            metadata["authors"] = ["Autor/a por determinar"]

        return metadata

    def format_notification_message(
        self,
        metadata: Dict[str, Any],
        pr_url: Optional[str] = None,
        author_contact: Optional[str] = None,
    ) -> str:
        """Xera a mensaxe con formato Markdown para Telegram."""
        authors_str = ", ".join(metadata["authors"])
        cats_str = " | ".join(metadata["categories"]) if metadata["categories"] else "Xeral"

        attachments = []
        if metadata.get("has_hsc"):
            attachments.append("📁 Aspen HYSYS (.hsc)")
        if metadata.get("has_dwxml"):
            attachments.append("🟢 DWSIM (.dwxml)")
        if metadata.get("has_colab"):
            attachments.append("⚡ Google Colab")
        if metadata.get("has_video"):
            attachments.append("▶ Vídeo titorial")

        attach_str = ", ".join(attachments) if attachments else "Caderno / Artigo técnico"

        status_badge = "🟡 *BORRADOR PROPOSTO (draft: true)*" if metadata.get("is_draft") else "🔵 *NOVA ENTRADA PROPOSTA*"

        msg_lines = [
            f"🔔 {status_badge}",
            f"*SOPQ // ProcessSim · Alerta Editorial*",
            "",
            f"📝 *Título:* {metadata['title']}",
        ]

        if metadata.get("subtitle"):
            msg_lines.append(f"ℹ️ *Subtítulo:* _{metadata['subtitle']}_")

        msg_lines.extend([
            f"👤 *Autor/es:* {authors_str}",
            f"🏷️ *Taxonomía:* `{cats_str}`",
            f"📦 *Adxuntos:* {attach_str}",
        ])

        if author_contact:
            msg_lines.append(f"📬 *Contacto:* {author_contact}")

        if pr_url:
            msg_lines.extend([
                "",
                f"🔗 *Revisar Pull Request:* [Abrir en GitHub]({pr_url})",
            ])

        msg_lines.extend([
            "",
            "⚙️ *Acción do Editor:* Revisa os balances de materia/enerxía e aproba a publicación retirando `draft: true` ou facendo merge da PR.",
        ])

        return "\n".join(msg_lines)

    def send_message(self, text: str) -> bool:
        """Envía a mensaxe a Telegram mediante a API HTTP oficial."""
        if self.dry_run:
            print(f"\n[TelegramNotifier DRY-RUN] Simulando envío a Telegram (Chat ID: {self.chat_id or 'NON_CONFIGURADO'}):")
            print("=" * 60)
            print(text)
            print("=" * 60)
            return True

        if not self.bot_token or not self.chat_id:
            print("⚠️ [AVISO] TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID non configurados. Saltando notificación.", file=sys.stderr)
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                if result.get("ok"):
                    print(f"✓ [TELEGRAM] Notificación enviada con éxito ao chat {self.chat_id}.")
                    return True
                else:
                    print(f"❌ [TELEGRAM ERROR] Resposta: {result}", file=sys.stderr)
                    return False
        except Exception as e:
            print(f"❌ [TELEGRAM ERROR] Erro enviando mensaxe: {e}", file=sys.stderr)
            return False

    def notify_post_proposal(
        self,
        post_path: Path | str,
        pr_url: Optional[str] = None,
        author_contact: Optional[str] = None,
    ) -> bool:
        """Lé o post, formatea a notificación e envíaa ao editor."""
        metadata = self.parse_post_metadata(post_path)
        message = self.format_notification_message(metadata, pr_url, author_contact)
        return self.send_message(message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Notificador de Telegram para o Editor de SOPQ // ProcessSim")
    parser.add_argument("--post", type=str, help="Ruta ao ficheiro .qmd do post a notificar")
    parser.add_argument("--pr-url", type=str, default=None, help="URL da Pull Request de GitHub (opcional)")
    parser.add_argument("--author-contact", type=str, default=None, help="Correo ou contacto do autor (opcional)")
    parser.add_argument("--test", action="store_true", help="Enviar unha mensaxe de proba para verificar a conexión co bot")
    parser.add_argument("--dry-run", action="store_true", help="Modo simulación sen conexión de rede real")

    args = parser.parse_args()

    notifier = TelegramEditorNotifier(dry_run=args.dry_run)

    if args.test:
        test_msg = (
            "🚀 *[SOPQ Bot Test]* O servizo de notificacións editoriais de SOPQ // ProcessSim está funcionando correctamente!"
        )
        success = notifier.send_message(test_msg)
        sys.exit(0 if success else 1)

    if args.post:
        success = notifier.notify_post_proposal(
            post_path=args.post,
            pr_url=args.pr_url,
            author_contact=args.author_contact,
        )
        sys.exit(0 if success else 1)

    parser.print_help()


if __name__ == "__main__":
    main()
