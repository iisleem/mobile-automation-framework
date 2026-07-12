from __future__ import annotations


class GestureHelper:
    def __init__(self, driver) -> None:
        self.driver = driver

    def scroll_down(self, percent: float = 0.75) -> None:
        size = self.driver.get_window_size()
        self.swipe(
            start_x=size["width"] // 2,
            start_y=int(size["height"] * percent),
            end_x=size["width"] // 2,
            end_y=int(size["height"] * (1 - percent)),
        )

    def scroll_up(self, percent: float = 0.75) -> None:
        size = self.driver.get_window_size()
        self.swipe(
            start_x=size["width"] // 2,
            start_y=int(size["height"] * (1 - percent)),
            end_x=size["width"] // 2,
            end_y=int(size["height"] * percent),
        )

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration_ms: int = 600) -> None:
        try:
            self.driver.swipe(start_x, start_y, end_x, end_y, duration_ms)
        except Exception:
            self.driver.execute_script(
                "mobile: dragGesture",
                {
                    "startX": start_x,
                    "startY": start_y,
                    "endX": end_x,
                    "endY": end_y,
                    "speed": max(250, duration_ms),
                },
            )

    def long_press(self, element=None, x: int | None = None, y: int | None = None, duration_ms: int = 1000) -> None:
        args = {"duration": duration_ms}
        if element is not None:
            args["elementId"] = element.id
        else:
            args.update({"x": x, "y": y})

        try:
            self.driver.execute_script("mobile: longClickGesture", args)
        except Exception:
            self.driver.execute_script("mobile: touchAndHold", args)

    def tap_coordinates(self, x: int, y: int) -> None:
        try:
            self.driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
        except Exception:
            self.driver.tap([(x, y)])
