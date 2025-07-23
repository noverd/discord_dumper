import os
import asyncio
import discord

from logging import getLogger, basicConfig
from typing import Optional
from rich.traceback import install
from bot import DumpingBot
from html_gen import HTMLGenerator
from tui import TUI


log = getLogger(__name__)
basicConfig(level=os.environ.get("LOGLEVEL", "FATAL"))
install() # Installing traceback handler

async def get_bot_token(tui: TUI) -> Optional[str]:
    while True:
        token = tui.get_user_input("Enter Discord User Token", password=True)
        if token:
            return token
        tui.show_msg_panel("Error", "User token was not entered. Please re-enter the token.", "red")


async def connect_bot(tui: TUI, bot: DumpingBot, token: str) -> bool:
    tui.start_status("Connecting to Discord...")
    bot_task: Optional[asyncio.Task] = None
    bot_ready_task: Optional[asyncio.Task] = None
    try:
        bot_ready_event = asyncio.Event()
        bot.ready_event = bot_ready_event

        bot_task = asyncio.create_task(bot.start(token))
        bot_ready_task = asyncio.create_task(bot_ready_event.wait())

        done: set[asyncio.Task]
        pending: set[asyncio.Task]
        done, pending = await asyncio.wait(
            [bot_task, bot_ready_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        if bot_task in done:
            await bot_task
            tui.show_msg_panel("Connection Error", "Bot task completed prematurely without becoming ready or raising an error.", "red")
            tui.log_message("[bold red]Connection Error:[/bold red] Bot task completed prematurely.", "error")
            return False

        if bot_ready_task in done:
            await bot_ready_task
            tui.log_message(f"[green]Bot successfully connected to Discord.[/green]", "success")
        else:
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            tui.show_msg_panel("Connection Error", "Unexpected state: Bot did not become ready.", "red")
            tui.log_message("[bold red]Connection Error:[/bold red] Bot did not become ready.", "error")
            return False

        if not bot.available_guilds:
            tui.show_msg_panel("Connection Error", "Bot found no available servers. Please invite the bot to a server.", "red")
            tui.log_message("[bold red]Connection Error:[/bold red] No available servers found.", "error")
            return False

        return True

    except discord.errors.LoginFailure:
        tui.show_msg_panel("Authentication Error", "Invalid token. Check your Discord Token.", "red")
        tui.log_message("[bold red]Authentication Error:[/bold red] Invalid token.", "error")
        return False
    except Exception as e:
        tui.show_msg_panel("Critical Error", f"A critical error occurred during connection: {e}", "red")
        log.exception("Critical error during bot connection.")
        tui.traceback()
        return False
    finally:
        tui.stop_status()
        if bot_task and not bot_task.done():
            bot_task.cancel()
            try: await bot_task
            except asyncio.CancelledError: pass
        if bot_ready_task and not bot_ready_task.done():
            bot_ready_task.cancel()
            try: await bot_ready_task
            except asyncio.CancelledError: pass


async def select_and_setup_guild(tui: TUI, bot: DumpingBot) -> bool:
    selected_guild: Optional[discord.Guild] = await tui.select_server_interactive(bot.available_guilds)

    if not selected_guild:
        tui.log_message("[yellow]Archiving cancelled: no server selected.[/yellow]", "warning")
        return False

    bot.guild = selected_guild
    bot.text_channels = [channel for channel in bot.guild.channels if isinstance(channel, discord.TextChannel)]

    tui.log_message(f"[green]Bot successfully selected server: [bold]{bot.guild.name}[/bold][/green]", "success")
    return True

async def select_theme(tui: TUI) -> Optional[str]:
    current_script_dir: str = os.path.dirname(__file__)
    project_root: str = os.path.abspath(os.path.join(current_script_dir, os.pardir))
    themes_dir: str = os.path.join(project_root, 'themes')

    if not os.path.isdir(themes_dir):
        tui.show_msg_panel("Error", f"Themes directory not found at {themes_dir}. Exiting.", "red")
        tui.log_message(f"[bold red]Error:[/bold red] Themes directory not found: {themes_dir}", "error")
        return None

    available_themes: list[str] = [d for d in os.listdir(themes_dir) if os.path.isdir(os.path.join(themes_dir, d))]

    if not available_themes:
        tui.show_msg_panel("Error", "No themes found in 'themes' directory. Exiting.", "red")
        tui.log_message("[bold red]Error:[/bold red] No themes found in 'themes' directory.", "error")
        return None

    selected_theme_name: Optional[str] = tui.select_theme_interactive(available_themes)
    if not selected_theme_name:
        tui.log_message("[yellow]Theme selection cancelled.[/yellow]", "warning")
        return None

    theme_path: str = os.path.join(themes_dir, selected_theme_name)
    tui.log_message(f"[green]Selected theme: [bold]{selected_theme_name}[/bold][/green]", "success")
    return theme_path


async def archive_channels(tui: TUI, bot: DumpingBot, main_progress_bar, html_gen: HTMLGenerator) -> bool:
    channels_to_archive: list[discord.TextChannel] = await tui.select_channels_interactive(bot.text_channels)

    if not channels_to_archive:
        tui.log_message("[yellow]Archiving cancelled: no channels selected.[/yellow]", "warning")
        return False

    tui.log_message("[bold green]Starting archiving process...[/bold green]")

    with main_progress_bar:
        try:
            await bot.start_archiving_process(channels_to_archive, html_gen)
            tui.log_message("[bold green]Archiving completed![/bold green]", "success")
            return True
        except Exception as e:
            tui.show_msg_panel("Critical Error", f"A critical error occurred during archiving: {e}", "red")
            tui.log_message(f"[bold red]Critical Error:[/bold red] {e}", "error")
            log.exception("Critical error during archiving.")
            tui.traceback()
            return False


async def main():
    tui = TUI()
    tui.display_welcome()

    main_progress_bar = tui.init_progress_bars()

    while True:
        bot_token: Optional[str] = await get_bot_token(tui)
        if not bot_token:
            break

        bot = DumpingBot(tui=tui)

        if not await connect_bot(tui, bot, bot_token):
            if not bot.is_closed():
                await bot.close()
            continue

        try:
            if not await select_and_setup_guild(tui, bot):
                continue

            theme_path: Optional[str] = await select_theme(tui)
            if theme_path is None:
                continue

            html_gen: HTMLGenerator = HTMLGenerator(theme_path, tui)

            if not await archive_channels(tui, bot, main_progress_bar, html_gen):
                continue

            tui.show_msg_panel("Process Complete", "Archiving finished. You can close the program or start a new archiving process.")
            if not tui.confirm_action("Do you want to archive more channels or servers?"):
                break
            else:
                if not bot.is_closed():
                    await bot.close()
                continue

        except Exception as e:
            tui.show_msg_panel("Runtime Error", f"An unexpected error occurred during the archiving flow: {e}", "red")
            tui.log_message(f"[bold red]Runtime Error:[/bold red] {e}", "error")
            log.exception("Unexpected error during archiving flow.")
            tui.traceback()
            if not tui.confirm_action("An error occurred. Do you want to try again from the beginning?"):
                break
            else:
                if not bot.is_closed():
                    await bot.close()
                continue
        finally:
            if not bot.is_closed():
                await bot.close()

    tui.log_message("[bold yellow]Program exited. Goodbye![/bold yellow]", "info")


if __name__ == "__main__":
    asyncio.run(main())