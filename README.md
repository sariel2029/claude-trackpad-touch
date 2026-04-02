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
