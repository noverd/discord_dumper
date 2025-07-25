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

import asyncio
import logging
import os
import discord

from discord import TextChannel, Client, Guild, Message
from tui import TUI
from html_gen import HTMLGenerator

log = logging.getLogger(__name__)


class DumpingBot(Client):
    def __init__(self, tui: TUI):
        super().__init__()
        self.tui = tui
        self.guild: Guild | None = None
        self.text_channels: list[TextChannel] = []
        self.ready_event: asyncio.Event | None = None
        self.available_guilds: list[Guild] = []

    async def on_ready(self):
        log.info(f'Logged in as {self.user} (ID: {self.user.id})')
        self.tui.log_message(f"Bot {self.user} connected to Discord!", "success")

        self.available_guilds = list(self.guilds)

        if self.ready_event:
            self.ready_event.set()

    async def fetch_messages_from_channel(self, channel: TextChannel) -> list[Message]:
        messages: list[Message] = []
        message_count = 0

        self.tui.log_message(f"Starting to load messages from channel #{channel.name}...", "info")

        try:
            self.tui.update_channel_progress(0, total=None, channel_name=channel.name)

            async for message in channel.history(limit=None, oldest_first=True):
                messages.append(message)
                message_count += 1
                if message_count % 50 == 0:
                    self.tui.update_channel_progress(message_count, channel_name=channel.name)

            self.tui.update_channel_progress(message_count, total=message_count, channel_name=channel.name)
            self.tui.log_message(f"Loaded [bold]{message_count}[/bold] messages from [bold]#{channel.name}[/bold].",
                                 "success")
        except discord.Forbidden:
            self.tui.log_message(
                f"Access denied to channel #{channel.name}. Skipping.", "error")
            log.warning(f"Forbidden to access channel #{channel.name} ({channel.id})")
        except Exception as e:
            self.tui.log_message(f"Error loading messages from #{channel.name}: {e}", "error")
            log.exception(f"Error fetching messages for channel #{channel.name}")
        return messages

    async def start_archiving_process(self, channels_to_archive: list[TextChannel], html_generator: HTMLGenerator):
        if not self.guild:
            self.tui.log_message("[bold red]Error:[/bold red] Cannot start archiving without a selected guild.", "error")
            return

        self.tui.log_message("Starting archiving process...")
        total_channels = len(channels_to_archive)

        self.tui.update_overall_progress(0, total_channels, description="Overall Archiving Progress")

        output_dir_base = f"discord_archive_{self.guild.id}"
        os.makedirs(output_dir_base, exist_ok=True)

        for i, channel in enumerate(channels_to_archive):
            self.tui.log_message(
                f"Processing channel [bold blue]#{channel.name}[/bold blue] ({i + 1}/{total_channels})...", "info")
            messages = await self.fetch_messages_from_channel(channel)

            if messages:
                try:
                    self.tui.log_message(f"Generating HTML for channel #{channel.name}...", "info")
                    output_path = os.path.join(output_dir_base, f"{channel.name}_archive.html")
                    await html_generator.generate_html(channel, messages, output_path)
                    self.tui.log_message(f"HTML generated for #{channel.name}: {output_path}", "success")
                except Exception as e:
                    self.tui.log_message(f"[bold red]HTML generation error for #{channel.name}:[/bold red] {e}",
                                         "error")
                    log.exception(f"Error generating HTML for channel #{channel.name}")
            else:
                self.tui.log_message(f"No messages to archive in #{channel.name}.", "warning")

            self.tui.update_overall_progress(i + 1, total_channels)

        self.tui.log_message("All channels processed.", "success")
        self.tui.update_overall_progress(total_channels, total_channels, description="Archiving completed")