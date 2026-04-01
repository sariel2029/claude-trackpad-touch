import random
from event_model import build_interpreted_event


def classify_pressure(avg_pressure, max_pressure):
    pressure = max(avg_pressure, max_pressure)
    if pressure < 0.12:
        return "蜻蜓点水"
    if pressure < 0.4:
        return "若有若无"
    if pressure < 0.75:
        return "落到实处"
    return "沉下去了"


def describe_gesture(session):
    gesture = session["gesture"]
    direction = session["direction"]
    duration_ms = session["duration_ms"]
    avg_p = session.get("avg_pressure", 0.0)
    max_p = session.get("max_pressure", 0.0)
    pressure_label = classify_pressure(avg_p, max_p)

    if gesture == "tap":
        return _tap_phrase(pressure_label)

    if gesture == "hold":
        return _hold_phrase(pressure_label, duration_ms)

    if gesture == "swipe":
        return _swipe_phrase(direction, pressure_label)

    if gesture == "drag":
        return _drag_phrase(direction, pressure_label, duration_ms, avg_p)

    return "指尖擦过，还没来得及读懂就结束了。"


def _tap_phrase(pressure_label):
    if pressure_label == "蜻蜓点水":
        return random.choice([
            "指尖碰了一下就收回去了，像怕惊扰到什么。",
            "很轻很快的一点，像试探水温。",
        ])
    if pressure_label == "若有若无":
        return "轻叩了一下，不重，但意图是清楚的。"
    return random.choice([
        "实实在在地按了一下，不是犹豫，是确认。",
        "笃定地点了一下，指腹压实了才松开。",
    ])


def _hold_phrase(pressure_label, duration_ms):
    long = duration_ms >= 1500
    if pressure_label in ("落到实处", "沉下去了"):
        if long:
            return "指腹压住不放，力气沉着地往下走，像是有话要说但还在措辞。"
        return "手指落下来就没打算马上走，带着点重量地停在那里。"
    if long:
        return "指尖搁在那里很久，轻得几乎感觉不到，但就是不肯离开。"
    return "手指停了一会儿，安静地留在原处，不急。"


def _swipe_phrase(direction, pressure_label):
    heavy = pressure_label in ("落到实处", "沉下去了")
    phrases = {
        "up": "往上一抹就收了，" + ("带着点不耐烦的果断。" if heavy else "像把什么轻轻掀开。"),
        "down": "往下一带就结束了，" + ("力气是沉的，有决意。" if heavy else "像随手翻过一页。"),
        "left": "朝左一划就过去了，" + ("指腹压着走的，不是漫不经心。" if heavy else "轻飘飘地掠过。"),
        "right": "朝右一送就没了，" + ("带着推出去的力道。" if heavy else "像在说——去吧。"),
        "stationary": "蹭了一下就停了，方向还没展开就结束了。",
    }
    return phrases.get(direction, "快速地划过去，还没回味就已经结束了。")


def _drag_phrase(direction, pressure_label, duration_ms, avg_pressure):
    slow = duration_ms >= 1200
    heavy = pressure_label in ("落到实处", "沉下去了")

    if slow and heavy:
        tempo_feel = "沉而缓"
    elif slow:
        tempo_feel = "慢悠悠"
    elif heavy:
        tempo_feel = "稳而快"
    else:
        tempo_feel = "轻且匀"

    phrases = {
        "up": {
            "沉而缓": "手指沉沉地往上推，每一寸都走得很慢，像在把什么沉重的东西托起来。",
            "慢悠悠": "手指往上游走，不着急，像指尖在丈量这段距离。",
            "稳而快": "稳稳地往上带了一段，力气清楚，方向笃定。",
            "轻且匀": "轻轻往上蹭了一段，没什么重量，像手指自己想动一动。",
        },
        "down": {
            "沉而缓": "手指慢慢往下沉，压感始终在，像不舍得断开这段接触。",
            "慢悠悠": "手指悠悠地往下滑，不赶时间，像雨滴顺着玻璃走。",
            "稳而快": "往下拽了一段，利落但不粗暴，有分寸。",
            "轻且匀": "手指往下溜了一小段，轻的，像在走神。",
        },
        "left": {
            "沉而缓": "手指沉着地往左拖过去，走得很慢，像在犹豫要不要走到尽头。",
            "慢悠悠": "往左慢慢挪了一段，像手指在地图上描一条路线。",
            "稳而快": "稳稳地往左带过去，一气呵成。",
            "轻且匀": "手指往左飘了一段，轻得像在摸一匹丝绸。",
        },
        "right": {
            "沉而缓": "手指沉沉地往右碾过去，压着走的，不肯浮起来。",
            "慢悠悠": "手指慢慢往右移，走得从容，不赶也不停。",
            "稳而快": "往右干脆地推过去了，带着明确的去向。",
            "轻且匀": "轻轻地往右蹭了一段，不经意的，像顺手做的事。",
        },
        "stationary": {
            "沉而缓": "指腹压在原地没真正走开，力气是有的，但方向悬而未决。",
            "慢悠悠": "手指留在原处磨蹭了一会儿，不走也不停。",
            "稳而快": "在原地压了一下就结束了，像话到嘴边又咽回去。",
            "轻且匀": "手指搁在那儿动了动，轻的，更像是一种存在感。",
        },
    }

    dir_phrases = phrases.get(direction, phrases["stationary"])
    return dir_phrases.get(tempo_feel, f"手指{tempo_feel}地拖了一段，安静地结束了。")


def structured_summary(session):
    return (
        f"{session['gesture']} | {session['direction']} | "
        f"{session['duration_ms']}ms | dist {session['total_distance']:.4f} | "
        f"pressure avg {session['avg_pressure']:.2f} peak {session['max_pressure']:.2f}"
    )


def translate_session(session):
    return build_interpreted_event(
        source="touch_session",
        gesture=session["gesture"],
        direction=session["direction"],
        structured=structured_summary(session),
        natural_zh=describe_gesture(session),
        duration_ms=session["duration_ms"],
        pressure={
            "avg": round(session.get("avg_pressure", 0.0), 4),
            "max": round(session.get("max_pressure", 0.0), 4),
            "stage": session.get("max_stage", 0),
        },
        metadata={
            "touch_id": session["touch_id"],
            "point_count": session["point_count"],
            "total_distance": session["total_distance"],
            "delta_x": session["delta_x"],
            "delta_y": session["delta_y"],
        },
    )
