import logging
import re
import aiofiles
import jinja2

from markdown import Markdown
from jinja2 import FileSystemLoader, select_autoescape
from jinja2.sandbox import SandboxedEnvironment
from discord import TextChannel, Message
from tui import TUI


class HTMLGenerator:
    """
    Generate HTML from discord messages.
    """

    def __init__(self, theme_path: str, tui: TUI):
        self.theme_path = theme_path
        self.tui = tui
        self.md = Markdown(extensions=['fenced_code', 'codehilite'])

        if not self.theme_path:
            raise ValueError("Path to the theme (theme_path) cannot be empty.")

        self.env = SandboxedEnvironment(
            loader=FileSystemLoader(self.theme_path),
            enable_async=True
        )

    def _is_image(self, filename: str) -> bool:
        return filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))

    def _parse_markdown(self, content: str) -> str:
        content = re.sub(r'\|\|(.+?)\|\|', r'<span class="spoiler">\1</span>', content) # Spoilers

        html_content = self.md.convert(content)
        return html_content

    async def generate_html(self, channel: TextChannel, messages: list[Message], output_path: str):
        try:
            template = self.env.get_template("channel.html")

            rendered_messages = []
            for msg in messages:
                attachments_data = [
                    {
                        "filename": attachment.filename,
                        "url": attachment.url,
                        "is_image": self._is_image(attachment.filename)
                    }
                    for attachment in msg.attachments
                ]

                embeds_data = [embed.to_dict() for embed in msg.embeds]

                rendered_messages.append({
                    "author_name": msg.author.display_name,
                    "author_avatar": msg.author.avatar.url if msg.author.avatar else None,
                    "timestamp": msg.created_at,
                    "content": self._parse_markdown(msg.clean_content),
                    "attachments": attachments_data,
                    "embeds": embeds_data
                })

            html_content = await template.render_async(
                channel_name=channel.name,
                messages=rendered_messages,
            )

            async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                await f.write(html_content)

            self.tui.log_message(
                f"HTML for #{channel.name} successful saved: [bold cyan]{output_path}[/bold cyan]", "success")

        except jinja2.exceptions.TemplateNotFound:
            self.tui.log_message(
                f"[bold red]Error:[/bold red] Template 'channel.html' not found in {self.theme_path}.", "error")
            logging.error(f"Not found template 'channel.html' in {self.theme_path}")
        except Exception as e:
            self.tui.log_message(f"[bold red]HTMl generation error:[/bold red] {e}", "error")
            logging.exception("Error while HTML generation")
            self.tui.traceback()