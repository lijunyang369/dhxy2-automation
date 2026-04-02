from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from src.perception import BattleButtonSemanticCatalog, ObservationBuilder, OpenCvTemplateMatcher, RegionRequest, TemplateCatalog
from src.platform import FrameCapture, PyWin32WindowGateway, Rect, WindowSession
from src.app.window_binding import resolve_window_session
from src.executor import ButtonCalibration, Win32SendInputGateway


@dataclass(frozen=True)
class ExecuteResult:
    button_ref: str
    handle: int
    client_x: int
    client_y: int
    before_hash: str
    after_hash: str
    frame_changed: bool
    before_matches: tuple[str, ...]
    after_matches: tuple[str, ...]
    semantic_confirmed: bool
    semantic_status: str
    semantic_reason: str
    before_path: str
    after_path: str
    elapsed_ms: int


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Execute one battle button click by button_ref.")
    parser.add_argument("--button-ref", required=True)
    parser.add_argument("--label", default="battle-action")
    parser.add_argument("--delay", type=float, default=0.25, help="Seconds to wait after click before capture.")
    parser.add_argument(
        "--wait-for-action-prompt-timeout",
        type=float,
        default=0.0,
        help="Seconds to wait for battle_action_prompt before clicking. 0 disables waiting.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    project_root = Path(__file__).resolve().parents[1]
    calibration = ButtonCalibration.load(project_root / "configs" / "ui" / "button-calibration.json")
    semantics = BattleButtonSemanticCatalog.load(project_root / "configs" / "ui" / "battle-button-semantics.json")
    client_x, client_y = calibration.resolve(args.button_ref)

    output_root = project_root / "runs" / "artifacts" / "probes"
    output_root.mkdir(parents=True, exist_ok=True)

    session = resolve_window_session(
        project_root / "configs" / "accounts" / "instance-1.json",
        gateway=PyWin32WindowGateway(),
    )
    session.focus()
    gateway = Win32SendInputGateway()
    if float(args.wait_for_action_prompt_timeout) > 0:
        _wait_for_action_prompt(project_root, session, float(args.wait_for_action_prompt_timeout))

    started_at = time.time()
    before = session.capture_client()
    before_observation = _observe_battle_frame(project_root, session, before)
    gateway.click(client_x, client_y)
    time.sleep(max(0.0, float(args.delay)))
    after = session.capture_client()
    after_observation = _observe_battle_frame(project_root, session, after)
    elapsed_ms = int((time.time() - started_at) * 1000)

    before_path = output_root / f"{args.label}-{args.button_ref.replace('.', '-')}-before.png"
    after_path = output_root / f"{args.label}-{args.button_ref.replace('.', '-')}-after.png"
    before.image.save(before_path)
    after.image.save(after_path)

    semantic_result = semantics.verify(args.button_ref, before_observation, after_observation)

    result = ExecuteResult(
        button_ref=args.button_ref,
        handle=session.handle,
        client_x=client_x,
        client_y=client_y,
        before_hash=before.frame_hash,
        after_hash=after.frame_hash,
        frame_changed=before.frame_hash != after.frame_hash,
        before_matches=semantic_result.before_matches,
        after_matches=semantic_result.after_matches,
        semantic_confirmed=semantic_result.confirmed,
        semantic_status=semantic_result.verification_status,
        semantic_reason=semantic_result.reason,
        before_path=str(before_path),
        after_path=str(after_path),
        elapsed_ms=elapsed_ms,
    )

    json_path = output_root / f"{args.label}-{args.button_ref.replace('.', '-')}.json"
    json_path.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


def _observe_battle_frame(project_root: Path, session: WindowSession, frame: FrameCapture):
    catalog = TemplateCatalog.load(project_root / "resources" / "templates" / "battle" / "catalog.json")
    matcher = OpenCvTemplateMatcher(catalog)
    builder = ObservationBuilder()
    window_info = session.snapshot()
    matches = []
    for region in _battle_regions():
        matches.extend(matcher.match(frame, region.name, region.rect))
    return builder.build(
        frame=frame,
        window_info=window_info,
        matches=tuple(matches),
        named_regions={region.name: region.rect for region in _battle_regions()},
    )


def _battle_regions() -> tuple[RegionRequest, ...]:
    return (
        RegionRequest(name="battle_main", rect=Rect(0, 40, 140, 170), use_template_match=True),
        RegionRequest(name="battle_prompt", rect=Rect(1170, 245, 1320, 530), use_template_match=True),
        RegionRequest(name="skill_bar", rect=Rect(950, 680, 1378, 831), use_template_match=True),
    )


def _wait_for_action_prompt(project_root: Path, session: WindowSession, timeout_seconds: float) -> None:
    deadline = time.time() + max(0.0, timeout_seconds)
    while time.time() <= deadline:
        observation = _observe_battle_frame(project_root, session, session.capture_client())
        if any(match.template_id == "battle_action_prompt" for match in observation.matches):
            return
        time.sleep(0.15)
    raise TimeoutError("battle_action_prompt was not observed before timeout")


if __name__ == "__main__":
    raise SystemExit(main())
