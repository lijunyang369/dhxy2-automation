# 大话西游2 自动化交接（2026-03-31）

## 说明

这是一份历史交接文档，记录 2026-03-31 阶段的上下文。
继续开发时，当前真实状态以 [current-task-2026-04-01.md](/D:/Codex/shared/context/current-task-2026-04-01.md) 为准。

## 当时主任务

把《大话西游2》自动化测试先打通真实点击输入能力，并把可用点击点位沉淀到配置与执行层。

## 当时阶段

阶段 2：真实输入与 UI 校准阶段（当时已完成一半）

当时已完成：

- 提权环境下的真实点击可驱动角色移动
- 非战斗底栏已建立网格化参数
- 部分按钮已确认命中并写入校准配置
- 执行层支持按 `button_ref` 解析点位，不再依赖裸坐标

当时未完成：

- 非战斗底栏剩余按钮确认
- 战斗栏按钮校准
- 真实输入网关完整接入主执行流程

## 当时确认的执行原则

1. 只要涉及真实点击，默认走提权环境
2. 遇到有规律的 UI，优先网格化 / 参数化，不优先逐点扫描

## 当时非战斗底栏网格

- `start_x = 870`
- `step_x = 40`
- `y = 792`

顺序：

- 千秋册：`[870, 792]`
- 宝宝：`[910, 792]`
- 道具：`[950, 792]`
- 组队：`[990, 792]`
- 攻击：`[1030, 792]`
- 元宝：`[1070, 792]`
- 商会：`[1110, 792]`
- 技能：`[1150, 792]`
- 坐骑：`[1190, 792]`
- 任务：`[1230, 792]`
- 好友：`[1270, 792]`
- 帮派：`[1310, 792]`
- 系统：`[1350, 792]`

## 当时已确认按钮

- `nonbattle_toolbar.pet_panel`
- `nonbattle_toolbar.bag_panel`
- `nonbattle_toolbar.team_panel`
- `nonbattle_toolbar.skill_panel`
- `nonbattle_toolbar.mount_panel`
- `nonbattle_toolbar.task_panel`
- `nonbattle_toolbar.system_panel`

## 关键文件

- [button-calibration.json](/D:/Codex/dhxy2-automation/configs/ui/button-calibration.json)
- [local.json](/D:/Codex/dhxy2-automation/configs/env/local.json)
- [button_calibration.py](/D:/Codex/dhxy2-automation/src/executor/button_calibration.py)
- [translator.py](/D:/Codex/dhxy2-automation/src/executor/translator.py)
- [bootstrap.py](/D:/Codex/dhxy2-automation/src/app/bootstrap.py)
- [click_probe.py](/D:/Codex/dhxy2-automation/scripts/click_probe.py)
- [scan_probe.py](/D:/Codex/dhxy2-automation/scripts/scan_probe.py)
- [run_button_scan.py](/D:/Codex/dhxy2-automation/scripts/run_button_scan.py)

## 当时建议起步命令

### 1. 运行测试

```powershell
$env:PYTHONPATH='D:\Codex\dhxy2-automation'
D:\Codex\dhxy2-automation\.venv\Scripts\python.exe -m unittest discover -s D:\Codex\dhxy2-automation\tests -p test_*.py
```

### 2. 按按钮名做热点扫描

```powershell
$env:PYTHONPATH='D:\Codex\dhxy2-automation'
D:\Codex\dhxy2-automation\.venv\Scripts\python.exe D:\Codex\dhxy2-automation\scripts\run_button_scan.py --group nonbattle_toolbar --button friend_panel --label toolbar-friend-scan --offsets '0:0,-10:0,10:0,0:-8,0:8' --delay 1.0
```

### 3. 按点位做单次点击验证

```powershell
$env:PYTHONPATH='D:\Codex\dhxy2-automation'
D:\Codex\dhxy2-automation\.venv\Scripts\python.exe D:\Codex\dhxy2-automation\scripts\click_probe.py --client-x 1270 --client-y 792 --label toolbar-friend-confirm --delay 1.0
```

## 当时后续待办

1. 完成非战斗底栏剩余按钮确认
2. 校准战斗栏按钮：`防御`、`道具`、`宝宝`
3. 在策略层增加 `CLICK_UI_BUTTON`
4. 把战斗场景中的裸坐标逐步替换成 `button_ref`

## 当前补充说明

这份文档只保留历史阶段信息。
后续继续开发时，先读：

1. [rules-index.md](/D:/Codex/shared/context/rules-index.md)
2. [current-task-2026-04-01.md](/D:/Codex/shared/context/current-task-2026-04-01.md)
3. [encoding-guardrails-2026-04-01.md](/D:/Codex/shared/context/encoding-guardrails-2026-04-01.md)
