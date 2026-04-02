from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class ButtonDetection:
    index: int
    name: str
    center: tuple[int, int]
    bounds: tuple[int, int, int, int]
    area: int


@dataclass(frozen=True)
class BattleCommandCalibrationSuggestion:
    layout: dict[str, object]
    buttons: dict[str, dict[str, object]]


def detect_battle_command_buttons(
    client_rgb: Image.Image,
    names: list[str] | tuple[str, ...],
    action_menu_template: Image.Image | None = None,
    min_menu_confidence: float = 0.95,
) -> tuple[ButtonDetection, ...]:
    template_boxes = _detect_by_action_menu_template(
        client_rgb=client_rgb,
        button_count=len(names),
        action_menu_template=action_menu_template,
        min_menu_confidence=min_menu_confidence,
    )
    boxes = template_boxes if template_boxes else _detect_button_boxes_by_color(client_rgb)

    detections: list[ButtonDetection] = []
    for idx, (x1, y1, x2, y2, area) in enumerate(boxes):
        center = ((x1 + x2) // 2, (y1 + y2) // 2)
        name = names[idx] if idx < len(names) else f"button_{idx + 1}"
        detections.append(
            ButtonDetection(
                index=idx,
                name=name,
                center=center,
                bounds=(x1, y1, x2, y2),
                area=area,
            )
        )
    return tuple(detections)


def _detect_by_action_menu_template(
    client_rgb: Image.Image,
    button_count: int,
    action_menu_template: Image.Image | None,
    min_menu_confidence: float,
) -> list[tuple[int, int, int, int, int]]:
    if action_menu_template is None or button_count <= 0:
        return []

    frame_rgb = client_rgb.convert("RGB")
    template_rgb = action_menu_template.convert("RGB")
    frame_gray = cv2.cvtColor(np.array(frame_rgb), cv2.COLOR_RGB2GRAY)
    template_gray = cv2.cvtColor(np.array(template_rgb), cv2.COLOR_RGB2GRAY)

    result = cv2.matchTemplate(frame_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)
    if float(max_val) < min_menu_confidence:
        return []

    menu_x, menu_y = max_loc
    menu_width, menu_height = template_rgb.size
    row_height = menu_height / button_count
    boxes: list[tuple[int, int, int, int, int]] = []
    for index in range(button_count):
        top = int(round(menu_y + (index * row_height)))
        bottom = int(round(menu_y + ((index + 1) * row_height)))
        left = menu_x
        right = menu_x + menu_width
        area = max(0, (right - left) * (bottom - top))
        boxes.append((left, top, right, bottom, area))
    return boxes


def _detect_button_boxes_by_color(client_rgb: Image.Image) -> list[tuple[int, int, int, int, int]]:
    frame = np.array(client_rgb.convert("RGB"))
    height, width, _channels = frame.shape
    roi_x1, roi_x2 = max(0, width - 140), width
    roi_y1, roi_y2 = max(0, int(height * 0.18)), min(height, int(height * 0.68))
    roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]

    hsv = cv2.cvtColor(roi, cv2.COLOR_RGB2HSV)
    lower1 = np.array([0, 30, 20], dtype=np.uint8)
    upper1 = np.array([10, 255, 255], dtype=np.uint8)
    lower2 = np.array([170, 30, 20], dtype=np.uint8)
    upper2 = np.array([180, 255, 255], dtype=np.uint8)
    hsv_mask = cv2.inRange(hsv, lower1, upper1) | cv2.inRange(hsv, lower2, upper2)

    red = roi[:, :, 0].astype(np.int16)
    green = roi[:, :, 1].astype(np.int16)
    blue = roi[:, :, 2].astype(np.int16)
    rgb_mask = np.where((red > 60) & (red > green + 12) & (red > blue + 12), 255, 0).astype(np.uint8)
    mask = cv2.bitwise_or(hsv_mask, rgb_mask)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detections: list[tuple[int, int, int, int, int]] = []
    for contour in contours:
        x, y, box_width, box_height = cv2.boundingRect(contour)
        area = int(box_width * box_height)
        if area < 350 or area > 4000:
            continue
        if box_width < 24 or box_height < 20:
            continue
        x1 = roi_x1 + x
        y1 = roi_y1 + y
        x2 = x1 + box_width
        y2 = y1 + box_height
        detections.append((x1, y1, x2, y2, area))

    detections.sort(key=lambda item: item[1])
    filtered: list[tuple[int, int, int, int, int]] = []
    for item in detections:
        if not filtered:
            filtered.append(item)
            continue

        prev = filtered[-1]
        if item[1] <= prev[3] - 8:
            x1 = min(prev[0], item[0])
            y1 = min(prev[1], item[1])
            x2 = max(prev[2], item[2])
            y2 = max(prev[3], item[3])
            area = max(prev[4], item[4])
            filtered[-1] = (x1, y1, x2, y2, area)
            continue

        filtered.append(item)

    return filtered


def build_battle_command_calibration_suggestion(
    detections: tuple[ButtonDetection, ...],
    labels_by_name: dict[str, str] | None = None,
) -> BattleCommandCalibrationSuggestion:
    labels = labels_by_name or {}
    if not detections:
        return BattleCommandCalibrationSuggestion(
            layout={"notes": "no detections"},
            buttons={},
        )

    center_x_values = [entry.center[0] for entry in detections]
    center_y_values = [entry.center[1] for entry in detections]
    inferred_steps = [
        center_y_values[index + 1] - center_y_values[index]
        for index in range(len(center_y_values) - 1)
    ]
    step_y = round(sum(inferred_steps) / len(inferred_steps)) if inferred_steps else 0

    buttons: dict[str, dict[str, object]] = {}
    for entry in detections:
        buttons[entry.name] = {
            "label": labels.get(entry.name, entry.name),
            "status": "candidate",
            "point": [entry.center[0], entry.center[1]],
            "notes": "template-detected candidate from battle_action_menu",
        }

    return BattleCommandCalibrationSuggestion(
        layout={
            "x": round(sum(center_x_values) / len(center_x_values)),
            "start_y": center_y_values[0],
            "step_y": step_y,
            "notes": "template-detected from battle_action_menu; review before promoting status",
        },
        buttons=buttons,
    )
