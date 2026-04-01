import json
import time
import hashlib

import AppKit
import Foundation
from PyObjCTools import AppHelper
from gesture_translator import translate_gesture_event
from output_sinks import build_output_router
from trackpad_session import TrackpadSessionAggregator
from touch_translator import translate_session

_APP_DELEGATE = None
SESSION_AGGREGATOR = TrackpadSessionAggregator()
OUTPUT_ROUTER = build_output_router()
VERBOSE_SESSION_POINTS = False
PHASE_LABELS = {
    0: "unknown",
    1: "began",
    2: "moved",
    4: "stationary",
    8: "ended",
    16: "cancelled",
}
EVENT_TOUCH_PHASES = {
    "touches_began": AppKit.NSTouchPhaseBegan,
    "touches_moved": AppKit.NSTouchPhaseMoved,
    "touches_ended": AppKit.NSTouchPhaseEnded,
    "touches_cancelled": AppKit.NSTouchPhaseCancelled,
}


def safe_event_float(event, name, default=0.0):
    value = getattr(event, name, None)
    if value is None:
        return default
    try:
        return float(value())
    except Exception:
        return default


def safe_event_int(event, name, default=0):
    value = getattr(event, name, None)
    if value is None:
        return default
    try:
        return int(value())
    except Exception:
        return default


def event_payload(event_type, **fields):
    payload = {
        "timestamp": round(time.time(), 3),
        "device": "mac_trackpad",
        "event_type": event_type,
    }
    payload.update(fields)
    return payload


def log_event(event_type, **fields):
    print(json.dumps(event_payload(event_type, **fields), ensure_ascii=True))


def log_human_summary(translation):
    print(f"[zh] {translation['natural_zh']}")


def emit_translated_gesture(event_type, **payload):
    log_event(event_type, **payload)
    translation = translate_gesture_event(event_type, payload)
    if translation is not None:
        log_event("interpreted_event", source_event=event_type, event=translation)
        log_human_summary(translation)
        OUTPUT_ROUTER.handle_translation(translation)


def touch_to_dict(touch):
    pos = touch.normalizedPosition()
    device_size = touch.deviceSize()
    raw_id = str(touch.identity())
    phase = int(touch.phase())
    return {
        "id": short_touch_id(raw_id),
        "phase": phase,
        "phase_name": PHASE_LABELS.get(phase, f"phase_{phase}"),
        "is_resting": bool(getattr(touch, "isResting", lambda: False)()),
        "x": round(pos.x, 4),
        "y": round(pos.y, 4),
        "device_width": round(device_size.width, 4),
        "device_height": round(device_size.height, 4),
        "raw_id": raw_id,
    }


def short_touch_id(raw_id):
    digest = hashlib.sha1(raw_id.encode("utf-8")).hexdigest()
    return f"touch_{digest[:8]}"


def summarize_touches(touches):
    if not touches:
        return None

    primary = touches[0]
    return {
        "finger_count": len(touches),
        "primary_touch_id": primary["id"],
        "primary_phase": primary["phase_name"],
        "primary_x": primary["x"],
        "primary_y": primary["y"],
    }


class TrackpadView(AppKit.NSView):
    def initWithFrame_(self, frame):
        self = AppKit.NSView.initWithFrame_(self, frame)
        if self is None:
            return None

        self.setAcceptsTouchEvents_(True)
        self.setWantsRestingTouches_(True)
        return self

    def acceptsFirstResponder(self):
        return True

    def viewDidMoveToWindow(self):
        AppKit.NSView.viewDidMoveToWindow(self)
        window = self.window()
        if window is not None:
            window.makeFirstResponder_(self)
            log_event("window_ready", title=str(window.title()))

    def _emit_touches(self, event_type, event):
        event_phase = EVENT_TOUCH_PHASES.get(event_type, AppKit.NSTouchPhaseAny)
        event_touches = event.touchesMatchingPhase_inView_(event_phase, self)
        active_touches = event.touchesMatchingPhase_inView_(AppKit.NSTouchPhaseTouching, self)

        event_payload_touches = [touch_to_dict(touch) for touch in event_touches]
        active_payload_touches = [touch_to_dict(touch) for touch in active_touches]

        summary = summarize_touches(event_payload_touches) or {
            "finger_count": 0,
            "primary_touch_id": None,
            "primary_phase": "none",
            "primary_x": None,
            "primary_y": None,
        }
        log_event(
            event_type,
            phase=event_type.removeprefix("touches_"),
            touches=event_payload_touches,
            active_touches=active_payload_touches,
            active_touch_count=len(active_payload_touches),
            pressure=round(safe_event_float(event, "pressure"), 4),
            stage=safe_event_int(event, "stage"),
            stage_pressure=round(safe_event_float(event, "stagePressure"), 4),
            **summary,
        )

        completed_sessions = SESSION_AGGREGATOR.process_event(
            event_type=event_type,
            timestamp=round(time.time(), 3),
            touches=event_payload_touches,
            pressure=round(safe_event_float(event, "pressure"), 4),
            stage=safe_event_int(event, "stage"),
        )
        for session in completed_sessions:
            session_summary = dict(session)
            if not VERBOSE_SESSION_POINTS:
                session_summary.pop("points", None)
            log_event("touch_session_completed", session=session_summary)
            translation = translate_session(session)
            log_event("interpreted_event", source_event="touch_session", event=translation)
            log_human_summary(translation)
            OUTPUT_ROUTER.handle_translation(translation)

    def touchesBeganWithEvent_(self, event):
        self._emit_touches("touches_began", event)

    def touchesMovedWithEvent_(self, event):
        self._emit_touches("touches_moved", event)

    def touchesEndedWithEvent_(self, event):
        self._emit_touches("touches_ended", event)

    def touchesCancelledWithEvent_(self, event):
        self._emit_touches("touches_cancelled", event)

    def pressureChangeWithEvent_(self, event):
        pressure = round(safe_event_float(event, "pressure"), 4)
        stage = safe_event_int(event, "stage")
        updated_touch_ids = SESSION_AGGREGATOR.process_pressure_event(
            timestamp=round(time.time(), 3),
            pressure=pressure,
            stage=stage,
        )
        log_event(
            "pressure_change",
            phase="changed",
            pressure=pressure,
            stage=stage,
            stage_pressure=round(safe_event_float(event, "stagePressure"), 4),
            attached_touch_ids=updated_touch_ids,
        )

    def magnifyWithEvent_(self, event):
        emit_translated_gesture(
            "magnify",
            phase="changed",
            magnification=round(safe_event_float(event, "magnification"), 4),
            pressure=round(safe_event_float(event, "pressure"), 4),
        )

    def rotateWithEvent_(self, event):
        emit_translated_gesture(
            "rotate",
            phase="changed",
            rotation=round(safe_event_float(event, "rotation"), 4),
            pressure=round(safe_event_float(event, "pressure"), 4),
        )

    def swipeWithEvent_(self, event):
        emit_translated_gesture(
            "swipe",
            phase="ended",
            delta_x=round(safe_event_float(event, "deltaX"), 4),
            delta_y=round(safe_event_float(event, "deltaY"), 4),
            pressure=round(safe_event_float(event, "pressure"), 4),
        )

    def scrollWheel_(self, event):
        emit_translated_gesture(
            "scroll",
            phase_name=PHASE_LABELS.get(safe_event_int(event, "phase"), "unknown"),
            scrolling_delta_x=round(safe_event_float(event, "scrollingDeltaX"), 4),
            scrolling_delta_y=round(safe_event_float(event, "scrollingDeltaY"), 4),
            has_precise_deltas=bool(event.hasPreciseScrollingDeltas()),
            phase=safe_event_int(event, "phase"),
            momentum_phase=safe_event_int(event, "momentumPhase"),
        )

    def mouseDown_(self, event):
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        log_event(
            "mouse_down",
            phase="began",
            x=round(point.x, 2),
            y=round(point.y, 2),
            click_count=int(event.clickCount()),
            pressure=round(safe_event_float(event, "pressure"), 4),
        )

    def mouseDragged_(self, event):
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        log_event(
            "mouse_dragged",
            phase="changed",
            x=round(point.x, 2),
            y=round(point.y, 2),
            pressure=round(safe_event_float(event, "pressure"), 4),
        )

    def mouseUp_(self, event):
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        log_event(
            "mouse_up",
            phase="ended",
            x=round(point.x, 2),
            y=round(point.y, 2),
            pressure=round(safe_event_float(event, "pressure"), 4),
        )


class AppDelegate(AppKit.NSObject):
    window = None
    label = None

    def applicationDidFinishLaunching_(self, notification):
        style_mask = (
            AppKit.NSWindowStyleMaskTitled
            | AppKit.NSWindowStyleMaskClosable
            | AppKit.NSWindowStyleMaskMiniaturizable
            | AppKit.NSWindowStyleMaskResizable
        )
        frame = Foundation.NSMakeRect(240.0, 240.0, 760.0, 480.0)
        self.window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            style_mask,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self.window.setTitle_("Mac Trackpad Probe")
        self.window.setReleasedWhenClosed_(False)

        view = TrackpadView.alloc().initWithFrame_(frame)
        view.setAutoresizingMask_(AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable)
        self.window.setContentView_(view)

        label_frame = Foundation.NSMakeRect(24.0, 24.0, 520.0, 72.0)
        self.label = AppKit.NSTextField.alloc().initWithFrame_(label_frame)
        self.label.setBezeled_(False)
        self.label.setDrawsBackground_(False)
        self.label.setEditable_(False)
        self.label.setSelectable_(False)
        self.label.setFont_(AppKit.NSFont.systemFontOfSize_(18.0))
        self.label.setStringValue_("Focus this window and use the trackpad. JSON events print in the terminal.")
        view.addSubview_(self.label)

        self.window.makeKeyAndOrderFront_(None)
        AppKit.NSApp.activateIgnoringOtherApps_(True)

        log_event("app_started", message="Trackpad probe window is ready")

    def applicationShouldTerminateAfterLastWindowClosed_(self, app):
        return True


def main():
    global _APP_DELEGATE
    app = AppKit.NSApplication.sharedApplication()
    _APP_DELEGATE = AppDelegate.alloc().init()
    app.setDelegate_(_APP_DELEGATE)
    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyRegular)
    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()
