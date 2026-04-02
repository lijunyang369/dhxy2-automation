from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.app import BootstrapPaths, JsonConfigLoader, NoOpInputGateway, build_app_from_configs
from src.domain import BattleState
from src.executor import Win32SendInputGateway
from src.platform import PyWin32WindowGateway


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run battle automation app once or multiple ticks.")
    parser.add_argument("--env", default="configs/env/local.json")
    parser.add_argument("--account", default="configs/accounts/instance-1.json")
    parser.add_argument("--scenario", default="configs/scenarios/battle-smoke.json")
    parser.add_argument("--ticks", type=int, default=1)
    parser.add_argument("--max-ticks", type=int, default=12, help="Upper bound used with --until-out-of-battle.")
    parser.add_argument(
        "--until-out-of-battle",
        action="store_true",
        help="Run until state becomes OUT_OF_BATTLE or max-ticks is reached.",
    )
    parser.add_argument("--live", action="store_true", help="Enable real input gateway and force dry_run=false.")
    parser.add_argument("--detect-only", action="store_true", help="Only run scene recognition; do not emit real input.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    env_path = PROJECT_ROOT / args.env
    account_path = PROJECT_ROOT / args.account
    scenario_path = PROJECT_ROOT / args.scenario

    loader = JsonConfigLoader()
    env_config = loader.load(env_path)
    runtime_env_path = env_path
    temp_env_path: Path | None = None
    if args.live:
        env_config["dry_run"] = False
        temp_env = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8")
        temp_env.write(json.dumps(env_config, ensure_ascii=False, indent=2))
        temp_env.flush()
        temp_env.close()
        temp_env_path = Path(temp_env.name)
        runtime_env_path = temp_env_path

    input_gateway = Win32SendInputGateway() if (args.live and not args.detect_only) else NoOpInputGateway()
    try:
        app = build_app_from_configs(
            BootstrapPaths(
                env_config=runtime_env_path,
                account_config=account_path,
                scenario_config=scenario_path,
            ),
            input_gateway=input_gateway,
            gateway=PyWin32WindowGateway(),
        )

        app.window_session.focus()

        last_result, ticks_run = _run_ticks(
            app=app,
            ticks=max(1, int(args.ticks)),
            until_out_of_battle=bool(args.until_out_of_battle),
            max_ticks=max(1, int(args.max_ticks)),
        )
        assert last_result is not None

        payload = {
            "state": app.context.state.value,
            "window_handle": app.window_session.handle,
            "ticks": ticks_run,
            "live_mode": bool(args.live),
            "detect_only": bool(args.detect_only),
            "until_out_of_battle": bool(args.until_out_of_battle),
            "transition_count": len(last_result.transitions),
            "executed_action_count": len(last_result.executed_actions),
            "executed_action_types": [entry.action_type for entry in last_result.executed_actions],
            "observation_confidence": last_result.observation.confidence_summary,
            "observation_flags": {
                "battle_ui_visible": last_result.observation.battle_ui_visible,
                "action_prompt_visible": last_result.observation.action_prompt_visible,
                "skill_panel_visible": last_result.observation.skill_panel_visible,
                "settlement_visible": last_result.observation.settlement_visible,
                "window_focused": last_result.observation.window_focused,
            },
            "matched_templates": [
                {
                    "template_id": match.template_id,
                    "region": match.region_name,
                    "confidence": match.confidence,
                }
                for match in last_result.observation.matches
            ],
            "input_operations": getattr(input_gateway, "operations", []),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    finally:
        if temp_env_path is not None and temp_env_path.exists():
            temp_env_path.unlink()


def _run_ticks(
    app,
    *,
    ticks: int,
    until_out_of_battle: bool,
    max_ticks: int,
):
    last_result = None
    ticks_run = 0
    if until_out_of_battle:
        while ticks_run < max_ticks:
            last_result = app.run_once()
            ticks_run += 1
            if app.context.state == BattleState.OUT_OF_BATTLE:
                break
        return last_result, ticks_run

    for _ in range(ticks):
        last_result = app.run_once()
        ticks_run += 1
    return last_result, ticks_run


if __name__ == "__main__":
    raise SystemExit(main())
