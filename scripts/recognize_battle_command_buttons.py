from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from PIL import Image
from PIL import ImageDraw

from src.app.window_binding import resolve_window_session
from src.executor import ButtonCalibration
from src.perception import (
    BattleCommandProfileCatalog,
    build_battle_command_calibration_suggestion,
    detect_battle_command_buttons,
)
from src.platform import PyWin32WindowGateway


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect battle command buttons from current battle frame.")
    parser.add_argument(
        "--profile",
        default="character_battle_command_bar",
        help="Battle command profile key defined in configs/ui/battle-command-profiles.json.",
    )
    parser.add_argument("--label", default="battle-command-detect")
    parser.add_argument(
        "--image-path",
        default=None,
        help="Optional path to a previously captured client screenshot. When set, detection runs on this image instead of a live capture.",
    )
    parser.add_argument(
        "--sync-candidates",
        action="store_true",
        help="Write the detected calibration suggestion to configs/ui/battle-command-detection-candidates.json.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    project_root = Path(__file__).resolve().parents[1]
    output_root = project_root / "runs" / "artifacts" / "probes"
    output_root.mkdir(parents=True, exist_ok=True)

    profile_catalog = BattleCommandProfileCatalog.load(project_root / "configs" / "ui" / "battle-command-profiles.json")
    profile = profile_catalog.get(str(args.profile).strip())
    if profile is None:
        raise ValueError(f"unknown battle command profile={args.profile}")

    menu_template = Image.open(project_root / "resources" / "templates" / "battle" / "battle_action_menu.png")
    button_calibration = ButtonCalibration.load(project_root / "configs" / "ui" / "button-calibration.json")

    if args.image_path:
        session = None
        raw_input_path = Path(str(args.image_path)).resolve()
        image = Image.open(raw_input_path).convert("RGB")
        frame_hash = "offline-image"
        handle = None
    else:
        session = resolve_window_session(
            project_root / "configs" / "accounts" / "instance-1.json",
            gateway=PyWin32WindowGateway(),
        )
        session.focus()
        frame = session.capture_client()
        image = frame.image.convert("RGB")
        frame_hash = frame.frame_hash
        handle = session.handle

    detections = detect_battle_command_buttons(
        image,
        list(profile.menu_button_names),
        action_menu_template=menu_template,
    )
    suggestion = build_battle_command_calibration_suggestion(
        detections,
        labels_by_name=profile.labels_by_name,
    )
    seeded_buttons = _build_seeded_buttons(profile.seed_button_refs, profile.labels_by_name, button_calibration)

    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)
    for entry in detections:
        x1, y1, x2, y2 = entry.bounds
        draw.rectangle((x1, y1, x2, y2), outline=(0, 255, 255), width=2)
        draw.text((x1 - 70, y1), f"{entry.index}:{entry.name}", fill=(255, 255, 0))
        cx, cy = entry.center
        draw.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(0, 255, 0))
    for button_ref, seeded_payload in seeded_buttons.items():
        point = seeded_payload["point"]
        cx, cy = int(point[0]), int(point[1])
        draw.rectangle((cx - 8, cy - 8, cx + 8, cy + 8), outline=(255, 128, 0), width=2)
        draw.text((cx - 32, cy - 18), button_ref.split(".")[-1], fill=(255, 128, 0))

    raw_path = output_root / f"{args.label}-raw.png"
    ann_path = output_root / f"{args.label}-annotated.png"
    json_path = output_root / f"{args.label}.json"
    image.save(raw_path)
    annotated.save(ann_path)

    payload = {
        "handle": handle,
        "profile_key": profile.profile_key,
        "profile_label": profile.label,
        "frame_hash": frame_hash,
        "raw_path": str(raw_path),
        "annotated_path": str(ann_path),
        "detection_count": len(detections),
        "detections": [asdict(entry) for entry in detections],
        "calibration_suggestion": {
            "group": profile.group,
            "layout": suggestion.layout,
            "buttons": suggestion.buttons,
            "seeded_buttons": seeded_buttons,
        },
    }
    if args.sync_candidates and len(detections) == len(profile.menu_button_names):
        candidate_path = project_root / "configs" / "ui" / "battle-command-detection-candidates.json"
        candidate_payload = {
            "version": 2,
            "source": {
                "type": "template_detection",
                "template": "resources/templates/battle/battle_action_menu.png",
                "profile_key": profile.profile_key,
                "evidence_frame": (
                    str(raw_input_path)
                    if args.image_path
                    else str(raw_path.relative_to(project_root)).replace("\\", "/")
                ),
                "notes": "Detected from battle action menu template. These are recognition candidates, not confirmed click targets.",
            },
            "profiles": {
                profile.group: {
                    "label": profile.label,
                    "layout": suggestion.layout,
                    "buttons": suggestion.buttons,
                    "seeded_buttons": seeded_buttons,
                }
            },
        }
        candidate_path.write_text(json.dumps(candidate_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        payload["candidate_config_path"] = str(candidate_path)
    elif args.sync_candidates:
        payload["candidate_sync_skipped"] = {
            "reason": "incomplete_detection",
            "expected_count": len(profile.menu_button_names),
            "actual_count": len(detections),
        }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _build_seeded_buttons(
    seed_button_refs: tuple[str, ...],
    labels_by_name: dict[str, str],
    calibration: ButtonCalibration,
) -> dict[str, dict[str, object]]:
    seeded: dict[str, dict[str, object]] = {}
    for button_ref in seed_button_refs:
        point = calibration.get(button_ref)
        if point is None:
            continue
        name = button_ref.split(".")[-1]
        seeded[button_ref] = {
            "label": labels_by_name.get(name, point.label or name),
            "status": point.status,
            "point": [point.x, point.y],
            "notes": "seeded from button-calibration.json for non-menu battle command recognition",
        }
    return seeded


if __name__ == "__main__":
    raise SystemExit(main())
