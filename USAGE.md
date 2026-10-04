# DUB

A calm blob that sits in the corner of your screen and keeps you posted on your Claudes.

Open it with the **DUB** shortcut on your desktop. Quit with **right-click → Quit**.

## Modes (click DUB to switch)

- **Work**: sits at a black desk with a laptop and types with its little hands when Claudes are working.
  - The mushroom lamp turns on by itself at night (between 7 pm and 7 am).
  - The props change every now and then (every 15 to 40 minutes): steaming tea, a vinyl record, a cassette or nothing.
- **Music**: sits on the floor with a walkman and slowly squashes to the beat. When the music heats up it closes its eyes. On drops it puts a hand to its headphones.

## Alerts

- When a Claude finishes, DUB gives a thumbs up and shows a speech bubble.
- When a Claude needs you (a permission prompt, for example), DUB shows you its phone and a speech bubble. It works with no extra setup. Clicking DUB dismisses the alert, and the square goes back to normal when the Claude resumes work.

## Claude usage (5-hour and weekly)

- Two small bars in the bottom-left corner (**5H** and **7D**). Green up to 80%, coral from there, and blinking above 95%. They turn grey if there has been no update for more than an hour.
- Right-click shows the percentage and the reset time of each one.
- **On-screen usage** (in the right-click menu) has three options: **Off**, **Small bars** (the ones above) and **Large bars with %** (two horizontal bars with the percentage written out). The large bars widen the window on the left, and DUB does not move.
- At **80%** DUB shows a speech bubble, once per window (the 5-hour and weekly windows warn separately).
- The data comes from the Claude Code status line: `dub_statusline.py` saves the values to `~/.dub/usage.json` and DUB only reads that file. To enable it, add this to `~/.claude/settings.json`:
  ```json
  "statusLine": { "type": "command", "command": "python \"C:\\path\\to\\dub_statusline.py\"" }
  ```
- It only updates while a Claude is open, after the session's first response. It is only available on Pro and Max subscriptions.

## Installing on another computer

- Run `installer\Output\DUB-Setup.exe`. It installs for your user only (no administrator needed), creates the shortcut, and can turn on Claude usage and start-with-Windows.
- To rebuild the installer after changing the code, run `installer\build.ps1` (it needs Python with pyinstaller, pillow, pycaw, comtypes and aalink, plus Inno Setup 6).
- The installer is not signed, so Windows SmartScreen may warn you the first time ("More info" → "Run anyway").
- To uninstall: Settings → Apps → DUB. It removes the status line the installer added, and your data in `~/.dub/` stays.

## Look (right-click)

- **Colour**: 15 shades.
  - Light: Mochi, Matcha, Hojicha, Ube, Névoa, Sakura, Momo, Yuzu, Kinako, Mint and Sora.
  - Dark: Black sesame, Azuki, Coffee and Sumi (with amber eyes).
- The **DUB** shortcut icon updates itself to match the colour and cap you pick.
- **Cap**: on or off.
- **Cheeks**: on or off (they are subtle by default, in a tone close to the body colour).

**Dragging** moves DUB. **Right-click** opens the Claudes, modes, sounds, size, language and Ableton Link.
Everything is read-only and local, and your data lives in `~/.dub/`.

## Language

DUB comes in **English** and **Portuguese**. Pick one in the right-click menu under **Language**; it is remembered next time. It does not depend on your Windows language.
