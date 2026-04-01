from event_model import build_interpreted_event


def describe_scroll(delta_x, delta_y):
    if abs(delta_y) >= abs(delta_x):
        direction = "down" if delta_y > 0 else "up"
    else:
        direction = "right" if delta_x > 0 else "left"

    magnitude = max(abs(delta_x), abs(delta_y))
    if magnitude < 2:
        intensity = "gentle"
    elif magnitude < 8:
        intensity = "steady"
    else:
        intensity = "brisk"

    phrases = {
        ("up", "gentle"): "两根手指轻轻往上推了推，像在慢慢翻阅什么。",
        ("up", "steady"): "双指顺畅地往上滚了一段，节奏稳定，在找什么东西。",
        ("up", "brisk"): "双指飞快地往上翻，急着要看到更前面的内容。",
        ("down", "gentle"): "两根手指轻轻往下带了带，不急不慢地浏览着。",
        ("down", "steady"): "双指匀速地往下滑，像在读一封长信。",
        ("down", "brisk"): "双指急促地往下拉，一口气跳过了很长一段。",
        ("left", "gentle"): "两根手指往左轻轻拨了一下，像在翻到下一张。",
        ("left", "steady"): "双指稳稳地往左扫过去，横向推开了一片。",
        ("left", "brisk"): "双指快速往左一扫，像翻书翻得急了。",
        ("right", "gentle"): "两根手指往右轻轻带了一下，像在退回上一张。",
        ("right", "steady"): "双指往右匀匀地拉回来，在回看刚才的内容。",
        ("right", "brisk"): "双指快速往右一拽，急着回到前面去。",
    }
    return direction, phrases.get((direction, intensity), f"双指滑动了一下，方向朝{direction}。")


def describe_magnify(magnification):
    mag = abs(magnification)
    if magnification > 0:
        if mag > 0.05:
            return "expand", "双指用力张开，像要把什么拽到眼前来看清楚。"
        if mag > 0.01:
            return "expand", "双指缓缓撑开，凑近了一点，想看得更仔细。"
        return "expand", "双指微微张了张，几乎没动，像在试探缩放的手感。"
    else:
        if mag > 0.05:
            return "contract", "双指快速收拢，像在把什么推回到远处去看全貌。"
        if mag > 0.01:
            return "contract", "双指慢慢合拢了一点，退远了些，想看到更多。"
        return "contract", "双指轻轻收了收，只挪了一点点，像在微调距离。"


def describe_rotate(rotation):
    direction = "clockwise" if rotation < 0 else "counterclockwise"
    degree = abs(rotation)
    if direction == "clockwise":
        if degree > 5:
            return direction, "双指大幅度地顺时针一拧，像在拧开什么瓶盖。"
        return direction, "双指顺时针转了一点，很小心的，像在对齐一个角度。"
    else:
        if degree > 5:
            return direction, "双指逆时针用力旋了一下，像要把什么拧回原位。"
        return direction, "双指逆时针微微调了一下，像在纠正一个不到一度的偏差。"


def describe_swipe(delta_x, delta_y):
    if abs(delta_y) >= abs(delta_x):
        direction = "down" if delta_y > 0 else "up"
    else:
        direction = "right" if delta_x > 0 else "left"

    phrases = {
        "up": "手指猛地往上一甩，短促而果断，像在说——走开。",
        "down": "往下干脆地一抹，一下就收了，没有多余的动作。",
        "left": "手指往左利落地一送，像翻过一页不想再看的东西。",
        "right": "手指往右一拨就收了，像在说——回去。",
    }
    return direction, phrases.get(direction, "快速地划了过去，来不及细看就结束了。")


def translate_gesture_event(event_type, payload):
    if event_type == "scroll":
        delta_x = payload["scrolling_delta_x"]
        delta_y = payload["scrolling_delta_y"]
        momentum_phase = payload.get("momentum_phase", 0)

        if abs(delta_x) < 0.01 and abs(delta_y) < 0.01:
            return None
        if momentum_phase and abs(delta_x) < 0.5 and abs(delta_y) < 0.5:
            return None

        direction, natural_zh = describe_scroll(
            delta_x,
            delta_y,
        )
        structured = (
            f"scroll | {direction} | dx {delta_x:.2f} | "
            f"dy {delta_y:.2f}"
        )
        return build_interpreted_event(
            source="scroll",
            gesture="scroll",
            direction=direction,
            structured=structured,
            natural_zh=natural_zh,
            metadata={
                "delta_x": delta_x,
                "delta_y": delta_y,
                "phase": payload.get("phase"),
                "momentum_phase": momentum_phase,
            },
        )

    if event_type == "magnify":
        direction, natural_zh = describe_magnify(payload["magnification"])
        structured = f"magnify | {direction} | mag {payload['magnification']:.4f}"
        return build_interpreted_event(
            source="magnify",
            gesture="magnify",
            direction=direction,
            structured=structured,
            natural_zh=natural_zh,
            metadata={
                "magnification": payload["magnification"],
            },
        )

    if event_type == "rotate":
        direction, natural_zh = describe_rotate(payload["rotation"])
        structured = f"rotate | {direction} | rot {payload['rotation']:.4f}"
        return build_interpreted_event(
            source="rotate",
            gesture="rotate",
            direction=direction,
            structured=structured,
            natural_zh=natural_zh,
            metadata={
                "rotation": payload["rotation"],
            },
        )

    if event_type == "swipe":
        direction, natural_zh = describe_swipe(
            payload["delta_x"],
            payload["delta_y"],
        )
        structured = (
            f"swipe_gesture | {direction} | dx {payload['delta_x']:.4f} | "
            f"dy {payload['delta_y']:.4f}"
        )
        return build_interpreted_event(
            source="swipe",
            gesture="swipe_gesture",
            direction=direction,
            structured=structured,
            natural_zh=natural_zh,
            metadata={
                "delta_x": payload["delta_x"],
                "delta_y": payload["delta_y"],
            },
        )

    return None
