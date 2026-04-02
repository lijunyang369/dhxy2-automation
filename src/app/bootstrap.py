from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.app.account_loader import AccountBindingLoader
from src.app.action_feedback import ActionFeedbackVerifier
from src.app.config_refs import configs_root, resolve_config_reference
from src.app.observation_provider import DefaultObservationProvider, DefaultObservationProviderConfig
from src.app.profile_loader import CharacterProfileLoader
from src.app.service import BattleAutomationApp
from src.app.window_binding import resolve_window_session
from src.domain import AccountBinding, ActionType, AutomationContext, BattleState, MatchResult
from src.executor import ActionExecutor, ActionTranslator, ButtonCalibration, InputGateway
from src.perception import (
    NullTemplateMatcher,
    ObservationBuilder,
    OpenCvTemplateMatcher,
    RegionRequest,
    StaticTemplateMatcher,
    BattleButtonSemanticCatalog,
    TemplateCatalog,
)
from src.perception.ocr_client import OCRServiceClient
from src.perception.ocr_models import OCRServiceConfig
from src.platform import PyWin32WindowGateway, WindowSession
from src.policy import (
    FixedActionRule,
    FixedRulePolicy,
    ScriptedActionRule,
    ScriptedRoundPolicy,
    ScriptedRoundRule,
)
from src.runtime import RuntimeSession
from src.state_machine import BattleStateMachine


@dataclass(frozen=True)
class BootstrapPaths:
    env_config: Path
    account_config: Path
    scenario_config: Path


@dataclass(frozen=True)
class ObservationPipeline:
    builder: ObservationBuilder
    config: DefaultObservationProviderConfig
    template_matcher: object


class JsonConfigLoader:
    def load(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8-sig"))


class NoOpInputGateway(InputGateway):
    def __init__(self) -> None:
        self.operations: list[tuple[str, object]] = []

    def click(self, x: int, y: int) -> None:
        self.operations.append(("click", (x, y)))

    def press_key(self, key: str) -> None:
        self.operations.append(("key", key))

    def wait(self, seconds: float) -> None:
        self.operations.append(("wait", seconds))


def build_app(
    paths: BootstrapPaths,
    window_session: WindowSession,
    input_gateway: InputGateway | None = None,
) -> BattleAutomationApp:
    loader = JsonConfigLoader()
    env_config = loader.load(paths.env_config)
    account_binding = AccountBindingLoader().load(paths.account_config)
    scenario_config = loader.load(paths.scenario_config)

    initial_state = BattleState(scenario_config.get("initial_state", "OUT_OF_BATTLE"))
    context = AutomationContext(
        instance_id=account_binding.instance_id,
        battle_session_id=f"{scenario_config['scenario_id']}-session",
        state=initial_state,
        previous_stable_state=initial_state,
        previous_state=initial_state,
    )
    character_profile = _load_character_profile(paths.account_config, account_binding)
    if character_profile is not None:
        context.character_profile = character_profile
        context.metadata["character_profile"] = character_profile.to_dict()

    runtime_session = RuntimeSession.create(Path(env_config["runs_root"]), context)

    policy = _build_policy(scenario_config)

    observation_pipeline = _build_observation_pipeline_from_configs(
        scenario_config=scenario_config,
        env_config=env_config,
    )
    observation_provider = DefaultObservationProvider(
        template_matcher=observation_pipeline.template_matcher,
        builder=observation_pipeline.builder,
        config=observation_pipeline.config,
    )
    executor = _build_executor(env_config)
    feedback_verifier = _build_feedback_verifier(env_config)

    return BattleAutomationApp(
        context=context,
        window_session=window_session,
        observation_provider=observation_provider,
        state_machine=BattleStateMachine(),
        policy=policy,
        executor=executor,
        runtime_session=runtime_session,
        input_gateway=input_gateway or NoOpInputGateway(),
        feedback_verifier=feedback_verifier,
    )


def build_app_from_configs(
    paths: BootstrapPaths,
    input_gateway: InputGateway | None = None,
    gateway: PyWin32WindowGateway | None = None,
) -> BattleAutomationApp:
    window_session = resolve_window_session(paths.account_config, gateway=gateway)
    return build_app(paths=paths, window_session=window_session, input_gateway=input_gateway)


def build_observation_pipeline(
    paths: BootstrapPaths,
    *,
    force_live: bool = False,
) -> ObservationPipeline:
    loader = JsonConfigLoader()
    env_config = loader.load(paths.env_config)
    scenario_config = loader.load(paths.scenario_config)
    if force_live:
        env_config["dry_run"] = False
    return _build_observation_pipeline_from_configs(
        scenario_config=scenario_config,
        env_config=env_config,
    )


def build_ocr_service_client(env_config: dict[str, Any]) -> OCRServiceClient | None:
    payload = env_config.get("ocr_service")
    if not isinstance(payload, dict):
        return None
    config = OCRServiceConfig(
        enabled=bool(payload.get("enabled", False)),
        base_url=str(payload.get("base_url", "http://127.0.0.1:18080")).rstrip("/"),
        timeout_ms=int(payload.get("timeout_ms", 1500)),
    )
    if not config.enabled:
        return None
    return OCRServiceClient(config)

def _build_executor(env_config: dict[str, Any]) -> ActionExecutor:
    button_calibration_path = env_config.get("button_calibration")
    button_calibration = None
    if button_calibration_path:
        calibration_file = Path(button_calibration_path)
        if calibration_file.exists():
            button_calibration = ButtonCalibration.load(calibration_file)
    return ActionExecutor(translator=ActionTranslator(button_calibration=button_calibration))


def _load_character_profile(account_config_path: Path, account_binding: AccountBinding):
    character_config_ref = account_binding.character_config_ref
    if not character_config_ref:
        return None
    character_root = configs_root(account_config_path) / "characters"
    character_config_path = resolve_config_reference(
        account_config_path,
        str(character_config_ref),
        allowed_root=character_root,
    )
    return CharacterProfileLoader().load(character_config_path)


def _build_observation_pipeline_from_configs(
    scenario_config: dict[str, Any],
    env_config: dict[str, Any],
) -> ObservationPipeline:
    ocr_client = build_ocr_service_client(env_config)
    regions = tuple(
        RegionRequest(
            name=entry["name"],
            rect=_to_rect(entry.get("rect")),
            use_template_match=bool(entry.get("use_template_match", True)),
        )
        for entry in scenario_config.get("regions", [])
    )
    dry_run = bool(env_config.get("dry_run", False))
    return ObservationPipeline(
        builder=ObservationBuilder(ocr_client=ocr_client),
        config=DefaultObservationProviderConfig(regions=regions),
        template_matcher=_build_template_matcher(scenario_config, env_config, dry_run),
    )


def _build_template_matcher(scenario_config: dict[str, Any], env_config: dict[str, Any], dry_run: bool):
    if dry_run:
        matches_by_region: dict[str, tuple[MatchResult, ...]] = {}
        for region_name, entries in scenario_config.get("mock_matches", {}).items():
            matches_by_region[region_name] = tuple(
                MatchResult(
                    template_id=entry["template_id"],
                    confidence=float(entry["confidence"]),
                    region_name=region_name,
                    bounds=tuple(entry["bounds"]) if entry.get("bounds") else None,
                    note=entry.get("note"),
                )
                for entry in entries
            )
        return StaticTemplateMatcher(matches_by_region)

    template_catalog_path = env_config.get("template_catalog")
    if template_catalog_path:
        catalog = TemplateCatalog.load(Path(template_catalog_path))
        if not catalog.is_empty():
            return OpenCvTemplateMatcher(catalog)
    return NullTemplateMatcher()


def _to_rect(raw: list[int] | tuple[int, int, int, int] | None):
    if raw is None:
        return None
    from src.platform import Rect

    left, top, right, bottom = raw
    return Rect(left=left, top=top, right=right, bottom=bottom)


def _build_feedback_verifier(env_config: dict[str, Any]) -> ActionFeedbackVerifier:
    semantic_catalog_path = env_config.get("battle_button_semantics")
    semantic_file: Path | None = None
    if semantic_catalog_path:
        semantic_file = Path(semantic_catalog_path)
    else:
        button_calibration = env_config.get("button_calibration")
        if button_calibration:
            semantic_file = Path(button_calibration).with_name("battle-button-semantics.json")
    if semantic_file is not None and semantic_file.is_file():
        return ActionFeedbackVerifier(BattleButtonSemanticCatalog.load(semantic_file))
    return ActionFeedbackVerifier()


def _build_policy(scenario_config: dict[str, Any]):
    round_script = scenario_config.get("round_script")
    if round_script:
        rounds: list[ScriptedRoundRule] = []
        for round_payload in round_script:
            rounds.append(
                ScriptedRoundRule(
                    reason=str(round_payload["reason"]),
                    actions=tuple(
                        ScriptedActionRule(
                            action_type=ActionType(action_payload["action_type"]),
                            target=action_payload.get("target"),
                            parameters=dict(action_payload.get("parameters", {})),
                        )
                        for action_payload in round_payload.get("actions", [])
                    ),
                )
            )
        return ScriptedRoundPolicy(tuple(rounds))

    primary_rule = scenario_config["primary_rule"]
    return FixedRulePolicy(
        FixedActionRule(
            action_type=ActionType(primary_rule["action_type"]),
            reason=primary_rule["reason"],
            target=primary_rule.get("target"),
            parameters=dict(primary_rule.get("parameters", {})),
        )
    )
