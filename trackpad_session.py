import math


PHASE_TO_LABEL = {
    "touches_began": "began",
    "touches_moved": "moved",
    "touches_ended": "ended",
    "touches_cancelled": "cancelled",
}


class TrackpadSessionAggregator:
    def __init__(self):
        self.sessions = {}
        self.last_active_touch_ids = []

    def process_event(self, event_type, timestamp, touches, pressure=0.0, stage=0):
        phase = PHASE_TO_LABEL.get(event_type)
        if phase is None:
            return []

        completed = []
        for touch in touches:
            touch_id = touch["id"]
            session = self.sessions.get(touch_id)

            if session is None:
                session = self._new_session(touch_id, timestamp)
                self.sessions[touch_id] = session

            session["end_timestamp"] = timestamp
            session["last_phase"] = phase
            session["max_pressure"] = max(session["max_pressure"], pressure)
            session["max_stage"] = max(session["max_stage"], stage)
            session["points"].append(
                {
                    "timestamp": timestamp,
                    "phase": phase,
                    "x": touch["x"],
                    "y": touch["y"],
                    "pressure": pressure,
                    "stage": stage,
                    "is_resting": touch["is_resting"],
                }
            )

            if phase in ("ended", "cancelled"):
                completed.append(self._finalize_session(touch_id))

        if phase in ("began", "moved"):
            self.last_active_touch_ids = [touch["id"] for touch in touches]
        elif phase in ("ended", "cancelled"):
            ended_ids = {touch["id"] for touch in touches}
            self.last_active_touch_ids = [
                touch_id for touch_id in self.last_active_touch_ids
                if touch_id not in ended_ids
            ]

        return [session for session in completed if session is not None]

    def process_pressure_event(self, timestamp, pressure=0.0, stage=0):
        updated_touch_ids = []
        for touch_id in list(self.last_active_touch_ids):
            session = self.sessions.get(touch_id)
            if session is None:
                continue

            session["end_timestamp"] = timestamp
            session["max_pressure"] = max(session["max_pressure"], pressure)
            session["max_stage"] = max(session["max_stage"], stage)
            last_point = session["points"][-1] if session["points"] else None

            if last_point and abs(last_point["timestamp"] - timestamp) < 0.02:
                last_point["pressure"] = max(last_point["pressure"], pressure)
                last_point["stage"] = max(last_point["stage"], stage)
            else:
                session["points"].append(
                    {
                        "timestamp": timestamp,
                        "phase": "pressure",
                        "x": last_point["x"] if last_point else None,
                        "y": last_point["y"] if last_point else None,
                        "pressure": pressure,
                        "stage": stage,
                        "is_resting": last_point["is_resting"] if last_point else False,
                    }
                )

            updated_touch_ids.append(touch_id)

        return updated_touch_ids

    def _new_session(self, touch_id, timestamp):
        return {
            "touch_id": touch_id,
            "start_timestamp": timestamp,
            "end_timestamp": timestamp,
            "last_phase": "began",
            "points": [],
            "max_pressure": 0.0,
            "max_stage": 0,
        }

    def _finalize_session(self, touch_id):
        session = self.sessions.pop(touch_id, None)
        if not session or not session["points"]:
            return None

        points = session["points"]
        start = points[0]
        end = points[-1]
        duration_ms = round((session["end_timestamp"] - session["start_timestamp"]) * 1000)
        total_distance = 0.0

        for prev, curr in zip(points, points[1:]):
            total_distance += math.hypot(curr["x"] - prev["x"], curr["y"] - prev["y"])

        delta_x = round(end["x"] - start["x"], 4)
        delta_y = round(end["y"] - start["y"], 4)
        avg_pressure = round(
            sum(point["pressure"] for point in points) / len(points),
            4,
        )
        gesture = classify_session(duration_ms, total_distance, delta_x, delta_y)
        direction = describe_direction(delta_x, delta_y)

        return {
            "touch_id": touch_id,
            "phase": session["last_phase"],
            "gesture": gesture,
            "direction": direction,
            "point_count": len(points),
            "duration_ms": duration_ms,
            "start_x": start["x"],
            "start_y": start["y"],
            "end_x": end["x"],
            "end_y": end["y"],
            "delta_x": delta_x,
            "delta_y": delta_y,
            "total_distance": round(total_distance, 4),
            "avg_pressure": avg_pressure,
            "max_pressure": round(session["max_pressure"], 4),
            "max_stage": session["max_stage"],
            "points": points,
        }


def classify_session(duration_ms, total_distance, delta_x, delta_y):
    displacement = math.hypot(delta_x, delta_y)

    if duration_ms < 220 and total_distance < 0.025 and displacement < 0.02:
        return "tap"
    if duration_ms >= 400 and total_distance < 0.03 and displacement < 0.025:
        return "hold"
    if displacement >= 0.12 and duration_ms <= 300:
        return "swipe"
    return "drag"


def describe_direction(delta_x, delta_y):
    if abs(delta_x) < 0.015 and abs(delta_y) < 0.015:
        return "stationary"
    if abs(delta_x) > abs(delta_y):
        return "right" if delta_x > 0 else "left"
    return "down" if delta_y > 0 else "up"
