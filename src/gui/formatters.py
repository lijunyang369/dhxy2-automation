from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.domain import AutomationAction, BattleObservation
from src.perception import RecognitionModuleResult

from .models import AutoBattleTickReport


def _utc_stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")


def _slug(value: str) -> str:
    cleaned = [char.lower() if char.isalnum() else "-" for char in value.strip()]
    return "".join(cleaned).strip("-") or "manual-probe"


def _display_bool(value: bool) -> str:
    return "是" if value else "否"


def _snapshot_file_mtimes(paths: tuple[Path, ...]) -> dict[str, float]:
    snapshot: dict[str, float] = {}
    for path in paths:
        if path.is_file():
            snapshot[str(path)] = path.stat().st_mtime
    return snapshot


def _state_label(value: str) -> str:
    return {
        "OUT_OF_BATTLE": "战斗外",
        "BATTLE_ENTERING": "进入战斗",
        "BATTLE_READY": "战斗准备",
        "ROUND_ACTIONABLE": "可操作回合",
        "ACTION_EXECUTING": "执行动作中",
        "ROUND_WAITING": "等待下一回合",
        "BATTLE_SETTLING": "战斗结算中",
        "BATTLE_FINISHED": "战斗结束",
        "RECOVERING": "恢复中",
        "FAILED": "失败",
    }.get(value, value)


def _action_label(value: str) -> str:
    return {
        "CLICK_UI_BUTTON": "点击界面按钮",
        "CAST_SKILL": "施放技能",
        "USE_ITEM": "使用道具",
        "SELECT_TARGET": "选择目标",
        "CONFIRM_ACTION": "确认动作",
        "RECOVER": "恢复",
        "NO_OP": "空操作",
    }.get(value, value)


def _step_label(value: str) -> str:
    return {
        "FOCUS_WINDOW": "聚焦窗口",
        "CLICK": "点击",
        "PRESS_KEY": "按键",
        "WAIT": "等待",
    }.get(value, value)


def _feedback_label(value: str) -> str:
    return {
        "semantic_catalog_unavailable": "未加载语义规则，默认通过",
        "semantic_rule_missing": "缺少语义规则，默认通过",
        "no_verifiable_click_ui_button": "没有可验证的按钮动作",
        "battle_scene_switched_after_action": "战斗场景已切换，战斗结束",
        "round_number_changed_after_action": "已识别到下一回合",
        "round_timer_visible_before_click": "回合指令区可见，按即时指令处理",
        "round_timer_disappeared_after_action": "回合计时标识已消失，本回合已结束",
        "next_round_prompt_reappeared_after_multi_action_plan": "多动作回合执行后已进入下一回合",
        "action_feedback_confirmed": "动作反馈确认成功",
        "action_feedback_missing": "动作反馈缺失",
    }.get(value, value or "无")


def _scene_label(observation: BattleObservation) -> str:
    if observation.battle_ui_visible:
        return "战斗场景"
    return "非战斗场景"


def _command_label(button_ref: str | None) -> str:
    mapping = {
        "battle_command_bar.spell": "法术",
        "battle_command_bar.item": "道具",
        "battle_command_bar.defend": "防御",
        "battle_command_bar.protect": "保护",
        "battle_command_bar.summon": "召唤",
        "battle_command_bar.recall": "召还",
        "battle_command_bar.catch": "捕捉",
        "battle_command_bar.escape": "逃跑",
        "character_battle_command_bar.spell": "法术",
        "character_battle_command_bar.item": "道具",
        "character_battle_command_bar.defend": "防御",
        "character_battle_command_bar.protect": "保护",
        "character_battle_command_bar.summon": "召唤",
        "character_battle_command_bar.recall": "召还",
        "character_battle_command_bar.catch": "捕捉",
        "character_battle_command_bar.escape": "逃跑",
        "pet_battle_command_bar.spell": "法术",
        "pet_battle_command_bar.item": "道具",
        "pet_battle_command_bar.defend": "防御",
        "pet_battle_command_bar.protect": "保护",
    }
    return mapping.get(button_ref or "", button_ref or "无")


def _planned_command_summary(actions: tuple[AutomationAction, ...]) -> tuple[str, str]:
    character_command = "无"
    pet_command = "无"
    for action in actions:
        if action.action_type.value != "CLICK_UI_BUTTON":
            continue
        button_ref = str(action.parameters.get("button_ref", ""))
        if button_ref.startswith("pet_battle_command_bar."):
            pet_command = _command_label(button_ref)
            continue
        if button_ref.startswith("battle_command_bar.") or button_ref.startswith("character_battle_command_bar."):
            character_command = _command_label(button_ref)
    return character_command, pet_command


def _recognition_status_label(result: RecognitionModuleResult | None) -> str:
    if result is None:
        return "待检测"
    return "已识别" if result.detected else "未识别"


def format_auto_battle_tick_lines(report: AutoBattleTickReport) -> list[str]:
    lines = [f"当前场景：{_scene_label(report.observation)}"]
    if not report.observation.battle_ui_visible:
        return lines

    round_number = report.round_index if report.round_index > 0 else 1
    recognition = (
        "战斗识别："
        f"回合数={report.observation.round_number_text or '未识别'}，"
        f"回合计时={_display_bool(report.observation.round_timer_visible)}，"
        f"指令提示={_display_bool(report.observation.action_prompt_visible)}，"
        f"技能栏={_display_bool(report.observation.skill_panel_visible)}，"
        f"状态={_state_label(report.state)}"
    )
    lines.append(recognition)
    lines.append(f"战斗回合：第 {report.observation.round_number_text or round_number} 回合")
    character_command, pet_command = _planned_command_summary(report.planned_actions)
    lines.append(f"人物指令：{character_command}")
    lines.append(f"宠物指令：{pet_command}")
    return lines
