# Mac Trackpad Probe

Small PyObjC prototype for testing what macOS trackpad data is reachable from a native AppKit view.

## What it tries to capture

- Touch lifecycle events: `touchesBegan/Moved/Ended/Cancelled`
- Gesture events: `magnifyWithEvent`, `rotateWithEvent`, `swipeWithEvent`
- Pressure changes: `pressureChangeWithEvent`
- Scrolling deltas: `scrollWheel`
- Mouse press/drag/release as a fallback signal for click + drag interaction

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
