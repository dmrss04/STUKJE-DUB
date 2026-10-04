<p align="center">
  <img src="docs/banner.png" alt="DUB in several colours" width="100%">
</p>

# DUB

**DUB is a calm blob that lives in the corner of your Windows screen.** While you work, it tells you what your [Claude Code](https://claude.com/claude-code) sessions are up to. When you listen to music, it bobs its head to the beat.

It is a quiet companion: it never asks for attention, and only shows up when it has something useful to tell you.

## What it does

| | |
|---|---|
| **Work mode** | Sits at its desk with a laptop and types while Claudes are working. One square per Claude shows its state: green when working, grey when free, coral when it needs you. |
| **Music mode** | Sits on the floor with a walkman and squashes to the beat of whatever is playing on your PC. It closes its eyes when the music heats up. |
| **Chill mode** | Sits at its desk and just keeps you company, for example while you watch a video. It ignores the audio completely: no dancing, only the calm little animations every now and then (sipping tea, looking around, yawning). Pick it from the right-click menu. |
| **Alerts** | When a Claude finishes, it gives a thumbs up. When one needs you (a permission prompt, for example), it shows its phone and a speech bubble. |
| **Claude usage** | Bars with your **5-hour** and **weekly** usage, always in view. It warns you once when either passes **80%**. |
| **Personalisation** | 15 colours, a cap, cheeks and 4 sizes. The shortcut icon changes with the colour you pick. |
| **Languages** | English and Portuguese, chosen in the menu (right-click → **Language**). |

Click DUB to switch between work and music, drag it to move it, and **right-click** for the menu (Claudes, usage, colours, sounds, size, language and quit).

## Claude usage

DUB shows two bars, **5H** and **7D**. They stay green up to 80%, turn coral from there, and blink above 95%. In the menu (right-click → **On-screen usage**) you choose between:

- **Small bars**: discreet, in the corner.
- **Large bars with %**: with the percentage written out.
- **Off**.

The same menu shows when each window resets.

**How it works:** Claude Code sends your usage limits to its *status line*. The small `dub_statusline` program saves those values to `~/.dub/usage.json`, and DUB only reads that file. There are no accounts, tokens or internet requests.

**Good to know:**
- It is only available on Claude **Pro** and **Max** subscriptions.
- It updates while a Claude is open, after the session's first response. If the data is more than an hour old, the bars turn grey.

## Installation

### Installer (recommended)

Download `DUB-Setup.exe` from the [latest release](https://github.com/dmrss04/STUKJE-DUB/releases/latest) and run it. It installs for your user only, with no administrator rights, and lets you choose:

- a desktop shortcut;
- showing Claude usage (turns on the Claude Code status line);
- starting DUB when Windows starts.

If you already have a Claude Code status line, the installer leaves it alone and tells you. To uninstall, use **Settings → Apps → DUB**.

> The installer is not signed, so Windows SmartScreen may warn you the first time. Choose **More info → Run anyway**.

### From source

You need Windows 10 or 11 and Python 3.12 or later.

```powershell
pip install pycaw comtypes aalink
python dub.py
```

To see Claude usage when running from source, add this to `~/.claude/settings.json` (adjust the path):

```json
"statusLine": {
  "type": "command",
  "command": "python \"C:\\path\\to\\dub_statusline.py\""
}
```

## Privacy

Everything is local and read-only. DUB sends nothing to the internet.

- **Audio:** it only reads the Windows volume meter. It does not record or intercept sound.
- **Claudes:** it only reads `~/.claude/sessions/*.json`, the state Claude Code already writes.
- **Usage:** it only reads `~/.dub/usage.json`.
- **Ableton Link:** off by default, optional in the menu.

Preferences are stored in `~/.dub/`.

## Building the installer

Most people can just download it from the [Releases](https://github.com/dmrss04/STUKJE-DUB/releases) page. To build it yourself, you need Python with `pyinstaller`, `pillow`, `pycaw`, `comtypes` and `aalink`, plus [Inno Setup 6](https://jrsoftware.org/isinfo.php) (`winget install JRSoftware.InnoSetup`).

```powershell
.\installer\build.ps1
```

The result is `installer\Output\DUB-Setup.exe`.

## Project layout

| File | What it is for |
|---|---|
| `dub.py` | The app: pixel-art sprite, modes, alerts and menu. |
| `dub_statusline.py` | Claude Code status line that saves usage for DUB. |
| `installer/` | Installer script (Inno Setup), wizard images and `build.ps1`. |
| `DUB.spec` | Builds a single portable `DUB.exe` with PyInstaller. |
| `USAGE.md` | More detailed usage notes. |

## License

[MIT](LICENSE)
