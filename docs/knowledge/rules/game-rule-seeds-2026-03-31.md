# 项目规则草案（2026-03-31）

## 目的

本文把百科摘要进一步压缩成项目可直接消费的字段和候选规则，作为 `dhxy2-automation` 的第一版知识规则层。

## 建议的知识模型

### 1. 页面索引对象

```json
{
  "source": "dh2.baike.163.com",
  "category": "新手入门",
  "title": "基本操作",
  "url": "https://dh2.baike.163.com/ziliao/465.html",
  "updated_at": "2015-10-22 16:06:39"
}
```

### 2. 规则对象

```json
{
  "rule_id": "ui.basic.left_click_move",
  "domain": "ui_control",
  "source_page": "基本操作",
  "preconditions": [],
  "action": "left_click_ground",
  "result": "character_walk",
  "confidence": "official_summary"
}
```

## 当前建议优先沉淀的规则域

- `ui_control`：移动、面板打开、战斗按钮、快捷键。
- `character_system`：属性、抗性、转生、种族/门派。
- `pet_system`：召唤兽数值、携带限制、养成字段。
- `equipment_system`：装备入口、打造、强化、点化、套装、仙器。
- `activity_system`：副本、日常玩法、开放条件、奖励入口。

## 第一批候选规则

### UI 与基础操作

- `ui.basic.left_click_move`
  来源：`基本操作`
  规则：左键点击地面使角色行走。

- `ui.basic.right_click_run`
  来源：`基本操作`
  规则：右键点击地面使角色跑动。

- `battle.basic.left_click_attack`
  来源：`基本操作`
  规则：战斗中左键点击目标执行物理攻击。

- `battle.basic.use_spell`
  来源：`基本操作`
  规则：先点“法术”再选目标，执行法术攻击。

- `ui.shortcut.nonbattle_panels`
  来源：`快捷键`
  规则：非战斗状态存在一组功能面板快捷键，例如 `Alt+I` 物品、`Alt+T` 组队、`Alt+F` 好友、`Alt+P` 宠物。

- `ui.layout.main_interface_regions`
  来源：`游戏界面`
  规则：主界面可分为顶部功能入口、右侧状态/社交入口、底部工具栏三组区域，适合作为 UI 命名基线。

### 角色系统

- `character.base_attributes`
  来源：`人物属性`
  字段：`根骨`、`灵性`、`力量`、`敏捷`。

- `character.derived_attributes`
  来源：`人物属性`
  字段：`HP`、`MP`、`AP`、`SP`。

- `character.resistance_caps`
  来源：`抗性和抗性上限`
  规则：不同种族对人法/遗忘存在不同上限；自动化配置需要允许按种族读取抗性阈值。

- `character.rebirth_benefits`
  来源：`转生系统`
  规则：转生影响技能熟练度上限、保留熟练度、赠送等级和属性点兑换上限。

### 召唤兽系统

- `pet.base_formula`
  来源：`召唤兽系统`
  规则：召唤兽最终能力与初值、等级、成长率、属性点有关，不能只按名字判断强弱。

- `pet.carry_limit`
  来源：`召唤兽携带限制`
  规则：召唤兽携带受角色等级和转生阶段约束，页面明确给出了查看入口、交易限制和最大携带数量。

- `pet.key_growth_fields`
  来源：`召唤兽系统`
  字段：`初值`、`成长率`、`等级`、`属性点`、`技能`、`亲密`、`龙骨`、`内丹`。

### 装备系统

- `equipment.blacksmith_entry`
  来源：`装备系统`
  规则：装备合成、重铸、升级通过铁匠完成，存在固定 NPC 入口。

- `equipment.xianqi_progression`
  来源：`仙器系统`
  规则：仙器分阶，可强化、炼化、升阶；材料链条与 `八荒遗风` 相关。

- `equipment.suit_system`
  来源：`套装系统`
  规则：套装由装备与套装玉符合成，多部件同时使用可触发套装技能。

### 系统玩法

- `mount.obtain_and_types`
  来源：`坐骑系统`
  规则：坐骑通过灵兽蛋孵化获得，按种族区分，每个种族有多只坐骑。

## 已补齐的缺口

- `游戏界面` 已确认是图片标注页，可直接抽成主界面区域和功能入口命名。
- `召唤兽携带限制` 已确认是规则图，已提取查看入口、交易限制和最大携带数量。

## 当前缺口

- 玩法页很多仍是说明型文本，尚未抽成统一字段模型，例如 `开放时间`、`参与条件`、`次数限制`、`奖励类型`。

## 重复标题去重策略

- 策略文档：[title-dedup-strategy-2026-03-31.md](/D:/Codex/dhxy2-automation/docs/knowledge/rules/title-dedup-strategy-2026-03-31.md)
- 映射样例：[title-dedup-map.example.json](/D:/Codex/dhxy2-automation/docs/knowledge/rules/examples/title-dedup-map.example.json)
- 当前规则：优先保留内容更完整的页面；完整度接近时保留更新时间更晚的页面；规则层只从 `canonical` 主页抽字段。

## 下一步建议

1. 先把 `基本操作`、`快捷键`、`人物属性`、`召唤兽系统`、`装备系统` 做成正式 JSON 配置样例。
2. 把 `游戏界面` 的主界面区域命名进一步映射到现有 `button-calibration` 和 UI 模板配置。
3. 为 `系统玩法` 设计统一字段：`entry`、`schedule`、`requirements`、`rewards`、`combat_related`。

## JSON 样例

- 目录说明：[README.md](/D:/Codex/dhxy2-automation/docs/knowledge/rules/examples/README.md)
- `基本操作`：[ui-basic-actions.example.json](/D:/Codex/dhxy2-automation/docs/knowledge/rules/examples/ui-basic-actions.example.json)
- `游戏界面`：[ui-main-interface.example.json](/D:/Codex/dhxy2-automation/docs/knowledge/rules/examples/ui-main-interface.example.json)
- `快捷键`：[ui-shortcuts.example.json](/D:/Codex/dhxy2-automation/docs/knowledge/rules/examples/ui-shortcuts.example.json)
- `人物属性/抗性/转生`：[character-attributes.example.json](/D:/Codex/dhxy2-automation/docs/knowledge/rules/examples/character-attributes.example.json)
- `召唤兽系统`：[pet-system.example.json](/D:/Codex/dhxy2-automation/docs/knowledge/rules/examples/pet-system.example.json)
- `装备系统`：[equipment-system.example.json](/D:/Codex/dhxy2-automation/docs/knowledge/rules/examples/equipment-system.example.json)

## 与现有 UI 配置的对齐

- 现有运行期点击配置仍以 [button-calibration.json](/D:/Codex/dhxy2-automation/configs/ui/button-calibration.json) 为准。
- `游戏界面` 的区域命名和按钮映射草案已落到 [interface-layout.example.json](/D:/Codex/dhxy2-automation/configs/ui/interface-layout.example.json)。
- 当前原则：不改动运行期配置格式，只新增对齐草案，等字段稳定后再决定是否并入正式 UI 配置。
