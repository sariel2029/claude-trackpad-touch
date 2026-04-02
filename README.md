# Claude Trackpad Touch

A personal macOS trackpad experiment for turning touch and gesture input into structured events and touch-like descriptions for Claude-oriented workflows.

Built with PyObjC and AppKit. This project is mainly for local use and exploration rather than broad compatibility.

## What it tries to capture

- Single-touch sessions such as tap, hold, swipe, and drag
- System gesture events such as scroll, magnify, rotate, and swipe
- Force Touch pressure changes when macOS exposes them
- Structured event objects plus Chinese touch-style summaries

## Gesture Summary

Single-touch gestures:

- `tap`
- `hold`
- `swipe`
- `drag`

System and multi-touch gestures:

- `scroll`
- `magnify`
- `rotate`
- `swipe_gesture`

## Install

```bash
/opt/homebrew/bin/python3.11 -m pip install --user -U pyobjc
```

Tested with Python 3.11 on macOS.

## Run

```bash
/opt/homebrew/bin/python3.11 app.py
```

To also copy the latest translated sentence to the clipboard:

```bash
TRACKPAD_COPY_TO_CLIPBOARD=1 /opt/homebrew/bin/python3.11 app.py
```

## Expected behavior

- A small window opens.
- Keep that window focused and move the pointer over it.
- Interact with the trackpad.
- Events are printed to stdout as JSON lines.

## Notes

- This prototype is intentionally window-scoped. It validates AppKit input delivery first.
- Some system gestures may never reach the app because macOS reserves them.
- Force Touch pressure requires compatible hardware.
- Pressure is currently treated as an optional enhancement signal, not a guaranteed input channel.

## Credits & Acknowledgements

This project was inspired by [ClaudeTabletTouch](https://github.com/digi-the-robot/ClaudeTabletTouch) by @digi-the-robot, which captures pressure-sensitive pen input from a drawing tablet and sends it to Claude via Discord. I adapted the core concept — translating physical touch into natural-language descriptions for Claude — to work with macOS trackpads using PyObjC and AppKit's native touch APIs, with MCP as the transport layer instead of Discord.

Most of the code in this prototype was written through AI-assisted collaboration:

- Codex (GPT-5.4): initial PyObjC exploration, touch data capture testing, Python environment setup
- Claude (Cowork): MCP server implementation, gesture translation, and event model architecture

My role was project direction, architecture decisions, gesture design, testing, and integration. I work by shaping the system, steering the implementation, and iterating with AI coding tools.
