# Copyright 2025 @noverd aka @gagarinten aka @codtenalt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os import getenv

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn, TaskID
from rich.prompt import Prompt, Confirm
from rich.status import Status
from rich.text import Text

from discord import TextChannel, Guild

DUMPER_TRACEBACK: bool = getenv("DUMPER_TRACEBACK", 0) == 1


class TUI:
    def __init__(self):
        self.console = Console()
        self.main_progress: Progress | None = None
        self.overall_task: TaskID | None = None
        self.channel_task: TaskID | None = None
        self.status: Status | None = None

    def display_welcome(self):
        ascii_art = """
██████╗ ██╗███████╗ ██████╗ ██████╗ ██████╗ ██████╗     ██████╗ ██╗   ██╗███╗   ███╗██████╗ ███████╗██████╗ 
██╔══██╗██║██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔══██╗    ██╔══██╗██║   ██║████╗ ████║██╔══██╗██╔════╝██╔══██╗
██║  ██║██║███████╗██║     ██║   ██║██████╔╝██║  ██║    ██║  ██║██║   ██║██╔████╔██║██████╔╝█████╗  ██████╔╝
██║  ██║██║╚════██║██║     ██║   ██║██╔══██╗██║  ██║    ██║  ██║██║   ██║██║╚██╔╝██║██╔═══╝ ██╔╝    ██╔══██╗
██████╔╝██║███████║╚██████╗╚██████╔╝██║  ██║██████╔╝    ██████╔╝╚██████╔╝██║ ╚═╝ ██║██║     ███████╗██║  ██║
╚═════╝ ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝     ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
"""

        welcome_text_content = Text(ascii_art, style="bold purple", justify="center")
        welcome_text_content.append(
            Text("\nDiscord Server Dumping Tool\n", style="bold cyan", justify="center"))
        welcome_text_content.append(
            Text("by @CodTenAlt(Discord)\n", style="bold dim", justify="center"))
        welcome_text_content.append(Text(
            "GitHub: https://github.com/noverd/DiscordDumper",
            style="bold dim", justify="center"))

        self.console.print(Align.center(
            Panel(welcome_text_content, title="[bold green]Welcome![/bold green]", border_style="green", expand=False)))
        self.console.print("\n")

    def start_status(self, status_str: str):
        if self.status is not None:
            self.status.stop()
        self.status = self.console.status(status_str)
        self.status.start()

    def stop_status(self):
        if self.status is not None:
            self.status.stop()

    def log_message(self, message: str, message_type: str = "info", prefix: bool = True):
        if prefix:
            message = self._format_message(message, message_type)
        if self.main_progress is not None:
            if self.main_progress.live.is_started:
                self.main_progress.console.print(message)
        else:
            self.console.print(message)

    @staticmethod
    def _format_message(message: str, message_type: str) -> str:
        match message_type:
            case "error":
                return f"[bold red][ERROR][/bold red] {message}"
            case "warning":
                return f"[bold yellow][WARNING][/bold yellow] {message}"
            case "success":
                return f"[bold green][SUCCESS][/bold green] {message}"
            case "info":
                return f"[bold cyan][INFO][/bold cyan] {message}"
            case _:
                return message

    def init_progress_bars(self) -> Progress:
        self.main_progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console,
            transient=True
        )
        return self.main_progress

    def update_overall_progress(self, current: int, total: int, description: str = "Overall Archiving"):
        if self.main_progress:
            if self.overall_task is None:
                self.overall_task = self.main_progress.add_task(description, total=total)
            self.main_progress.update(self.overall_task, completed=current, total=total, description=description)
            if current >= total:
                self.main_progress.stop_task(self.overall_task)
                self.overall_task = None

    def update_channel_progress(self, current: int, total: int | None = None, channel_name: str = ""):
        if self.main_progress:
            description = f"Channel: #{channel_name}" if channel_name else "Current Channel"
            if self.channel_task is None:
                self.channel_task = self.main_progress.add_task(description, total=total if total is not None else 100)
            else:
                self.main_progress.update(self.channel_task, completed=current,
                                          total=total if total is not None else self.main_progress.tasks[
                                              self.channel_task].total, description=description)
            if total is not None and current >= total:
                self.main_progress.stop_task(self.channel_task)
                self.channel_task = None

    @staticmethod
    def get_user_input(prompt_message: str, password: bool = False) -> str:
        return Prompt.ask(f"[bold cyan]{prompt_message}[/bold cyan]", password=password)

    def show_msg_panel(self, title: str, message: str, style: str = "blue"):
        t = Text(message)
        self.console.print(Panel(t, title=title, border_style=style))

    def confirm_action(self, prompt_message: str) -> bool:
        return Confirm.ask(f"[bold yellow]{prompt_message}[/bold yellow]")

    async def select_channels_interactive(self, channels: list[TextChannel]) -> list[TextChannel]:
        self.log_message("\n[bold]Select text channels to archive:[/bold]", prefix=False)
        for i, channel in enumerate(channels):
            self.console.print(f"  [bold blue]{i + 1}.[/bold blue] {channel.name} ([dim]ID: {channel.id}[/dim])")

        while True:
            selection_input = Prompt.ask(
                "Enter channel numbers separated by commas (e.g., 1,3,5) or [bold cyan]all[/bold cyan] to select all"
            ).strip()

            if selection_input.lower() == "all":
                self.log_message("[green]ALL channels selected.[/green]", prefix=False)
                return channels

            selected_indices: set[int] = set()
            try:
                parts = selection_input.split(',')
                for part in parts:
                    idx = int(part.strip()) - 1
                    if 0 <= idx < len(channels):
                        selected_indices.add(idx)
                    else:
                        self.log_message(
                            f"[bold red]Error:[/bold red] Channel number {idx + 1} out of range. Please try again.",
                            "error")
                        selected_indices.clear()
                        break

                if selected_indices:
                    selected_channels = [channels[i] for i in sorted(list(selected_indices))]
                    self.log_message("[green]Selected channels:[/green]", prefix=False)
                    for channel in selected_channels:
                        self.log_message(f"  - {channel.name}", prefix=False)

                    if self.confirm_action("Proceed with selected channels?"):
                        return selected_channels
                    else:
                        selected_indices.clear()
            except ValueError:
                self.log_message(
                    "[bold red]Error:[/bold red] Invalid input. Use numbers separated by commas, or 'all'.",
                    "error")
            except Exception as e:
                self.log_message(f"[bold red]Unknown error during channel selection: {e}[/bold red]", "error")
                selected_indices.clear()
        return []

    async def select_server_interactive(self, guilds: list[Guild]) -> Guild | None:
        self.log_message("\n[bold]Select a Discord server to archive:[/bold]", prefix=False)

        filtered_guilds: list[Guild] = list(guilds)

        while True:
            self.console.print("[dim]Use 'search <query>' to filter, 'list' to show all, or enter a number.[/dim]")

            if not filtered_guilds:
                self.log_message(
                    "[bold yellow]No servers to display (check search filter or add bot to servers).[/bold yellow]",
                    "warning")
                filtered_guilds = list(guilds)
                continue

            for i, guild in enumerate(filtered_guilds):
                self.console.print(f"  [bold blue]{i + 1}.[/bold blue] {guild.name} ([dim]ID: {guild.id}[/dim])")

            selection_input = Prompt.ask("Enter server number, 'search <query>', or 'list'").strip()

            if selection_input.lower().startswith("search "):
                query = selection_input[len("search "):].strip().lower()
                filtered_guilds = [g for g in guilds if query in g.name.lower()]
                if filtered_guilds:
                    self.log_message(
                        f"[bold green]Found {len(filtered_guilds)} servers matching '{query}':[/bold green]",
                        prefix=False)
                else:
                    self.log_message(f"[bold yellow]No servers found matching '{query}'. Showing all.[/bold yellow]",
                                     "warning")
                    filtered_guilds = list(guilds)
                continue
            elif selection_input.lower() == "list":
                filtered_guilds = list(guilds)
                self.log_message("[bold green]Displaying all available servers:[/bold green]", prefix=False)
                continue

            try:
                idx = int(selection_input) - 1
                if 0 <= idx < len(filtered_guilds):
                    selected_guild: Guild = filtered_guilds[idx]
                    self.log_message(f"[green]Selected server:[/green] {selected_guild.name}", prefix=False)
                    if self.confirm_action("Proceed with selected server?"):
                        return selected_guild
                else:
                    self.log_message(
                        f"[bold red]Error:[/bold red] Server number {idx + 1} out of range. Please try again.",
                        "error")
            except ValueError:
                self.log_message(
                    "[bold red]Error:[/bold red] Invalid input. Use a number, 'search <query>', or 'list'.", "error")
            except Exception as e:
                self.log_message(f"[bold red]Unknown error during server selection: {e}[/bold red]", "error")
        return None

    def select_theme_interactive(self, theme_names: list[str]) -> str | None:
        self.log_message("\n[bold]Select a theme for HTML generation:[/bold]", prefix=False)
        for i, theme in enumerate(theme_names):
            self.console.print(f"  [bold blue]{i + 1}.[/bold blue] {theme}")

        while True:
            selection_input = Prompt.ask("Enter theme number").strip()
            try:
                idx = int(selection_input) - 1
                if 0 <= idx < len(theme_names):
                    selected_theme: str = theme_names[idx]
                    self.log_message(f"[green]Selected theme:[/green] {selected_theme}", prefix=False)
                    return selected_theme
                else:
                    self.log_message(
                        f"[bold red]Error:[/bold red] Theme number {idx + 1} out of range. Please try again.",
                        "error")
            except ValueError:
                self.log_message(
                    "[bold red]Error:[/bold red] Invalid input. Use a number.", "error")
            except Exception as e:
                self.log_message(f"[bold red]Unknown error during theme selection: {e}[/bold red]", "error")
                self.traceback()
        return None

    def traceback(self):
        if DUMPER_TRACEBACK:
            self.console.print_exception()
        else:
            self.log_message("To get more information about the error, set env var DUMPER_TRACEBACK=1", "error")
