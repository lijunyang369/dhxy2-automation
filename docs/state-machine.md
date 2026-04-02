# 《大话西游2》战斗状态机设计

## 1. 文档目的

本文档定义战斗自动化的首版状态机模型，用于统一“当前处于什么状态”“下一步应该做什么”“异常时如何恢复”的判断逻辑。

状态机是当前架构中的核心模块。所有战斗行为都应由状态机驱动，不允许多个模块各自独立判断战斗流程。

## 2. 设计原则

- 同一时刻只有一个主状态
- 状态判断集中管理
- 感知层只提供观察结果，不负责状态迁移
- 策略层只在允许动作的状态下输出决策
- 执行层不决定业务状态，只执行动作
- 任意状态出现异常时可进入恢复状态

## 3. 一级状态定义

### `OUT_OF_BATTLE`

含义：

- 当前未识别到战斗界面
- 系统处于战斗外空闲或待进入状态

### `BATTLE_ENTERING`

含义：

- 已出现战斗切换迹象
- 但战斗 UI 尚未稳定

### `BATTLE_READY`

含义：

- 已稳定进入战斗界面
- 可以继续判断是否进入可操作回合

### `ROUND_ACTIONABLE`

含义：

- 当前角色可进行回合操作
- 可以生成并执行动作计划

### `ACTION_EXECUTING`

含义：

- 当前正在执行一个领域动作
- 尚未确认动作结果反馈

### `ROUND_WAITING`

含义：

- 当前回合已提交动作
- 等待动画、服务端反馈或下一轮状态变化

### `BATTLE_SETTLING`

含义：

- 已出现战斗结算或结束提示
- 正在等待结算界面稳定

### `BATTLE_FINISHED`

含义：

- 战斗已确认结束
- 可回收会话状态并退出战斗流程

### `RECOVERING`

含义：

- 当前进入异常恢复流程
- 正在尝试重新聚焦、重新识别或重新同步状态

### `FAILED`

含义：

- 恢复失败或达到终止条件
- 本次战斗自动化流程失败退出

## 4. 状态输入模型

状态机不直接依赖底层识别细节，而是基于聚合观察对象 `BattleObservation` 做判断。

建议字段：

- `battle_ui_visible`
- `action_prompt_visible`
- `skill_panel_visible`
- `target_select_visible`
- `settlement_visible`
- `window_alive`
- `window_focused`
- `ocr_texts`
- `matches`
- `frame_timestamp`
- `frame_hash`

建议同时附加：

- `confidence_summary`
- `named_regions`
- `last_action_feedback`

## 5. 主要状态迁移

### 主链路

1. `OUT_OF_BATTLE -> BATTLE_ENTERING`
条件：检测到战斗切换迹象或战斗 UI 部分出现

2. `BATTLE_ENTERING -> BATTLE_READY`
条件：战斗核心界面稳定出现，连续多帧识别一致

3. `BATTLE_READY -> ROUND_ACTIONABLE`
条件：检测到当前回合可操作标识

4. `ROUND_ACTIONABLE -> ACTION_EXECUTING`
条件：策略层成功生成动作计划且执行器开始执行

5. `ACTION_EXECUTING -> ROUND_WAITING`
条件：动作提交成功，界面进入等待态

6. `ROUND_WAITING -> ROUND_ACTIONABLE`
条件：新一轮可操作标识出现

7. `ROUND_WAITING -> BATTLE_SETTLING`
条件：检测到战斗结算提示或结束界面

8. `BATTLE_SETTLING -> BATTLE_FINISHED`
条件：结算状态稳定，确认战斗结束

9. `BATTLE_FINISHED -> OUT_OF_BATTLE`
条件：会话收尾完成，回到战斗外状态

### 异常链路

- 任意状态 -> `RECOVERING`
条件：窗口失活、识别漂移、动作无反馈、状态超时、卡死检测命中

- `RECOVERING -> 上一稳定状态`
条件：恢复成功并完成重新同步

- `RECOVERING -> FAILED`
条件：恢复次数超限或恢复超时

## 6. 状态判定建议

### 6.1 不要依赖单一信号

每个状态都应由多个信号组合判定，避免因单模板误识别造成误迁移。

示例：

- `ROUND_ACTIONABLE` 不应只依赖一个按钮模板
- 可组合“回合按钮 + 技能栏可见 + 目标未锁定 + OCR 提示文本”综合判断

### 6.2 引入稳定帧策略

对关键状态建议要求连续 N 帧满足条件后才确认迁移，降低动画过渡期误判。

推荐首版参数：

- `BATTLE_ENTERING -> BATTLE_READY`：连续 2 到 3 帧稳定
- `BATTLE_SETTLING -> BATTLE_FINISHED`：连续 2 帧稳定

### 6.3 所有迁移要有原因

状态机日志必须记录：

- 旧状态
- 新状态
- 触发条件摘要
- 关键识别结果
- 时间戳

## 7. 恢复策略

`RECOVERING` 不应是空状态，而应有明确恢复动作。

建议恢复步骤：

1. 校验窗口句柄是否仍有效
2. 若窗口失焦，尝试重新聚焦
3. 重新采集全窗口截图
4. 重新执行关键区域识别
5. 根据识别结果重建 `BattleObservation`
6. 判断能否回到最近稳定状态

恢复动作清单建议：

- `RefocusWindow`
- `RecaptureFrame`
- `RebuildObservation`
- `ReDetectBattleUI`
- `AbortCurrentAction`

恢复终止条件建议：

- 单次恢复超过指定秒数
- 连续恢复次数超过上限
- 连续多帧仍无法确认窗口和状态

## 8. 超时设计

建议按状态设置独立超时，而不是只设全局超时。

建议监控项：

- 进入战斗超时
- 可操作状态等待超时
- 动作执行反馈超时
- 战斗结算超时
- 恢复流程超时
- 单场战斗总超时

超时命中后动作：

- 记录状态超时事件
- 保存当前截图和最近动作信息
- 进入 `RECOVERING`

## 9. 事件与日志

建议定义标准事件：

- `state_entered`
- `state_exited`
- `transition_applied`
- `transition_rejected`
- `action_started`
- `action_finished`
- `action_timeout`
- `recovery_started`
- `recovery_finished`
- `recovery_failed`

日志最少应包含：

- `instance_id`
- `battle_session_id`
- `round_index`
- `state`
- `event_type`
- `timestamp`

## 10. 建议接口

建议接口划分如下：

- `StateResolver.resolve(observation, context) -> BattleState`
- `TransitionGuard.can_transit(from_state, to_state, observation, context) -> bool`
- `BattleStateMachine.tick(observation, context) -> TransitionResult`
- `RecoveryManager.recover(context, observation) -> RecoveryDecision`

## 11. 当前实施建议

一期先做最小状态集即可：

- `OUT_OF_BATTLE`
- `BATTLE_ENTERING`
- `ROUND_ACTIONABLE`
- `ACTION_EXECUTING`
- `ROUND_WAITING`
- `BATTLE_FINISHED`
- `RECOVERING`
- `FAILED`

待最小闭环稳定后，再补充 `BATTLE_READY` 和 `BATTLE_SETTLING` 的细化判定。

## 12. 验收标准

首版状态机设计完成后，应满足以下验收标准：

1. 任意时刻可明确输出当前唯一主状态
2. 每次状态迁移都有日志和触发依据
3. 动作执行前必须处于 `ROUND_ACTIONABLE`
4. 动作执行失败可进入恢复流程
5. 异常退出时可保留完整证据
