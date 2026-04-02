from __future__ import annotations

import json
import sys
from pathlib import Path
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.app import BootstrapPaths, JsonConfigLoader, build_app_from_configs
from src.domain import BattleState
from src.executor import Win32SendInputGateway
from src.platform import PyWin32WindowGateway


def main() -> int:
    env_path = PROJECT_ROOT / "configs" / "env" / "local.json"
    account_path = PROJECT_ROOT / "configs" / "accounts" / "instance-1.json"
    scenario_path = PROJECT_ROOT / "configs" / "scenarios" / "battle-basic-validation.json"

    loader = JsonConfigLoader()
    env_config = loader.load(env_path)
    env_config["dry_run"] = False

    temp_env = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8")
    temp_env.write(json.dumps(env_config, ensure_ascii=False, indent=2))
    temp_env.flush()
    temp_env.close()
    runtime_env_path = Path(temp_env.name)

    input_gateway = Win32SendInputGateway()
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

        last_result = None
        ticks_run = 0
        while ticks_run < 12:
            last_result = app.run_once()
            ticks_run += 1
            if app.context.state == BattleState.OUT_OF_BATTLE:
                break
        assert last_result is not None

        payload = {
            "scenario": "battle-basic-validation",
            "state": app.context.state.value,
            "ticks": ticks_run,
            "transition_count": len(last_result.transitions),
            "executed_action_count": len(last_result.executed_actions),
            "executed_action_types": [entry.action_type for entry in last_result.executed_actions],
            "matched_templates": [
                {
                    "template_id": match.template_id,
                    "region": match.region_name,
                    "confidence": match.confidence,
                }
                for match in last_result.observation.matches
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    finally:
        runtime_env_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
