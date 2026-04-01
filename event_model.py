def build_interpreted_event(
    source,
    gesture,
    direction,
    structured,
    natural_zh,
    device="mac_trackpad",
    duration_ms=None,
    pressure=None,
    metadata=None,
):
    event = {
        "kind": "interpreted_gesture",
        "device": device,
        "source": source,
        "gesture": gesture,
        "direction": direction,
        "structured": structured,
        "natural_zh": natural_zh,
    }
    if duration_ms is not None:
        event["duration_ms"] = duration_ms
    if pressure is not None:
        event["pressure"] = pressure
    if metadata:
        event["metadata"] = metadata
    return event
