# Discord Dumper

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![License](https://img.shields.io/badge/License-Apache%202.0-yellow.svg?logo=apache)](https://opensource.org/licenses/Apache-2.0)

Tool for archiving Discord servers/channels into HTML files with theme support. Preserves messages, attachments, and
formatting.

## ⚠️ Critical Notice

**This tool uses self-bot functionality which violates [Discord Terms of Service](https://discord.com/terms). Use at
your own risk.**

## Features

- Archive entire servers or selected channels
- HTML output with:
    - Light theme
    - Dark theme
- Preserves:
    - Message content
    - Attachments (images, videos)
    - User mentions
    - Formatting (bold, italic, etc.)

## Installation

```bash
git clone https://github.com/noverd/discord_dumper.git
cd discord_dumper
pip install -r requirements.txt
```

## Usage

1. Obtain your Discord token (see instructions below)
2. Run main script:

```bash
python discord_dumper/main.py
```

## 🔐 Obtaining Discord Token

1. Open Discord in browser
2. Login to your account
3. Open Developer Tools (Ctrl+Shift+I)
4. Go to Network tab → Refresh page
5. Find any request → Copy "Authorization" header value

## ⚙️ Environment Variables

| Variable           | Default | Description                                        |
|--------------------|---------|----------------------------------------------------|
| `LOGLEVEL`         | FATAL   | Log verbosity (DEBUG, INFO, WARNING, ERROR, FATAL) |
| `DUMPER_TRACEBACK` | 0       | Show error traces (1=enabled, 0=disabled)          |

Example:

```bash
export LOGLEVEL=INFO
export DUMPER_TRACEBACK=1
python discord_dumper/main.py
```

## Output Structure

```
discord_archive_server_id/
├── server_channel_1.html
├── server_channel_2.html
```

## Future Plans

- [ ] Direct Messages (DMs) support
- [ ] PyPI package distribution
- [ ] Additional export formats:
    - JSON
    - CSV
- [ ] User-friendly TUI

## ⚖️ Legal Disclaimer

This project is for educational purposes only. The developers assume no liability for:

- Account bans or violations of Discord ToS
- Improper use of archived data
- Legal consequences in your jurisdiction


## Support

For issues, please open a GitHub ticket.

## License
Licensed under Apache License 2.0. Check LICENSE.TXT for more information.
