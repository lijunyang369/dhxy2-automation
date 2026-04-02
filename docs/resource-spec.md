# 《大话西游2》战斗自动化资源与配置规范

## 1. 文档目的

本文档定义项目在模板图片、区域坐标、分辨率适配、角色配置、策略配置和运行产物方面的首版组织规范，避免资源散乱、命名无序和后期难以维护。

## 2. 目录建议

建议目录结构如下：

```text
D:\Codex\dhxy2-automation
├─ src
├─ resources
│  ├─ templates
│  │  ├─ common
│  │  ├─ battle
│  │  ├─ skills
│  │  └─ states
│  ├─ ocr
│  │  └─ profiles
│  └─ resolutions
│     ├─ 1280x720
│     ├─ 1600x900
│     └─ 1920x1080
├─ configs
│  ├─ env
│  ├─ accounts
│  ├─ characters
│  ├─ battles
│  └─ logging
├─ tests
├─ runs
│  └─ artifacts
└─ docs
```

## 3. 模板图片管理规范

### 3.1 命名原则

模板名称必须体现业务语义，不允许使用无意义截图时间戳作为主命名。

推荐命名格式：

`<模块>_<语义>_<状态或变体>.png`

示例：

- `battle_action_prompt.png`
- `battle_auto_button_on.png`
- `skill_dragon_attack_lv1.png`
- `state_battle_settlement.png`

### 3.2 模板元信息

每个模板应有对应的元信息配置，建议使用 YAML 或 JSON 保存。

建议字段：

- `id`
- `file`
- `scene`
- `region`
- `threshold`
- `resolution`
- `anchor`
- `note`

目标：

- 明确模板用途
- 明确建议阈值
- 明确适用分辨率和区域

### 3.3 模板分类

建议按业务语义分类：

- `common`：通用按钮、确认框、关闭按钮
- `battle`：回合、目标、结算、战斗提示
- `skills`：技能图标、法术图标、物品图标
- `states`：异常提示、卡死界面、特殊状态标志

## 4. 区域配置规范

### 4.1 禁止业务层直接写死坐标

业务代码必须通过命名区域访问截图和点击位置，区域坐标统一通过配置文件管理。

### 4.2 区域命名建议

建议统一使用逻辑区域名：

- `battle_main`
- `battle_prompt`
- `skill_bar`
- `target_panel`
- `settlement_panel`
- `character_status`
- `pet_status`

### 4.3 区域配置字段建议

- `name`
- `x`
- `y`
- `width`
- `height`
- `anchor`
- `resolution`
- `enabled`

### 4.4 锚点优先

对于关键控件区域，优先采用“锚点 + 偏移”方式，减少纯固定坐标的脆弱性。

## 5. 分辨率适配规范

### 5.1 一期策略

一期建议只支持一个固定分辨率或固定窗口尺寸，避免过早引入复杂适配逻辑。

### 5.2 二期策略

在固定方案稳定后，再支持少量白名单分辨率，通过配置切换区域和模板。

### 5.3 三期策略

再引入比例缩放和锚点定位结合的适配机制。

### 5.4 适配原则

- 不承诺任意分辨率自适应
- 以白名单分辨率为主
- 优先保证稳定性而非通用性

## 6. 角色与策略配置规范

建议将账号、角色和战斗策略拆分管理。

### 6.1 账号配置

建议内容：

- `account_id`
- `window_hint`
- `character_id`
- `enabled`

### 6.2 角色配置

建议内容：

- `character_id`
- `role_type`
- `skill_set`
- `default_target_rule`
- `hp_thresholds`
- `mp_thresholds`

### 6.3 战斗策略配置

建议内容：

- `policy_id`
- `round_rules`
- `skill_priority`
- `fallback_action`
- `target_rules`
- `recover_rules`

目标是让策略迭代以配置调整为主，而不是频繁改业务代码。

## 7. OCR 配置规范

OCR 应按场景配置不同 profile，而不是一个统一参数跑所有区域。

建议 profile 示例：

- `battle_prompt`
- `skill_name`
- `target_name`
- `settlement_text`

建议字段：

- `lang`
- `preprocess`
- `whitelist`
- `threshold`
- `resize_scale`

## 8. 运行产物规范

建议所有运行产物落在 `runs/artifacts` 下，并按实例和会话隔离。

推荐结构：

```text
runs/artifacts
└─ <instance_id>
   └─ <battle_session_id>
      ├─ screenshots
      ├─ annotated
      ├─ logs
      ├─ observations
      └─ actions
```

## 9. 日志与证据文件规范

建议日志类型：

- `runtime.log`
- `state_machine.log`
- `action.log`
- `vision.log`

关键文件输出建议：

- `observation_<timestamp>.json`
- `action_<timestamp>.json`
- `exception_<timestamp>.json`
- `frame_<timestamp>.png`

要求：

- 文件名可排序
- 同一会话内时间线可追踪
- 异常发生时能快速反查上下文

## 10. 测试资源规范

测试样本与运行资源分离，避免运行产物污染测试输入。

建议：

- 测试输入样本放在 `tests/fixtures`
- 识别样本按场景分类
- 回归样本固定版本
- 异常样本单独归档

## 11. 首版实施建议

当前阶段建议先落地以下最小资源集：

1. 一套固定分辨率配置
2. 一组战斗入口、可操作、目标选择、结束结算模板
3. 一份角色策略配置样例
4. 一份区域配置样例
5. 一套运行产物目录约束

## 12. 强制规范

首版资源管理必须遵守以下规则：

1. 模板按业务语义命名
2. 区域通过配置定义，不写死在业务逻辑中
3. 分辨率适配按白名单管理
4. 策略参数优先配置化
5. 运行产物必须按实例和会话隔离

