# 大话西游2 自动化运行流程

## 总体调用链

```mermaid
flowchart LR
    A["scripts/run_battle_app.py"] --> B["app.bootstrap.build_app_from_configs"]
    B --> C["platform.WindowFinder / WindowSession"]
    B --> D["app.BattleAutomationApp"]

    D --> E["app.DefaultObservationProvider.observe"]
    E --> F["platform.WindowSession.capture_client"]
    E --> G["perception.TemplateMatcher / OCRReader"]
    G --> H["perception.ObservationBuilder -> BattleObservation"]

    D --> I["state_machine.BattleStateMachine.tick"]
    D --> J["policy.FixedRulePolicy.build_plan"]
    D --> K["executor.ActionExecutor.execute"]
    K --> L["executor.ActionTranslator"]
    K --> M["executor.InputGateway"]

    D --> N["runtime.RuntimeSession.record_*"]
```

## `run_once()` 时序

```mermaid
sequenceDiagram
    participant App as BattleAutomationApp
    participant Obs as ObservationProvider
    participant SM as StateMachine
    participant Policy as Policy
    participant Exec as Executor
    participant Runtime as RuntimeSession

    App->>Obs: observe(window_session)
    Obs-->>App: BattleObservation
    App->>Runtime: record_observation()

    App->>SM: tick(observation, context)
    SM-->>App: TransitionResult
    App->>Runtime: record_transition()

    App->>Policy: build_plan(observation, context)
    Policy-->>App: ActionPlan

    alt plan 为空
        App-->>App: 返回本轮结果（无动作）
    else plan 非空
        App->>SM: begin_action(plan, context)
        App->>Runtime: record_transition()
        loop actions
            App->>Runtime: record_action()
            App->>Exec: execute(action, window_session, input_gateway)
            Exec-->>App: ExecutionResult
        end
        App->>SM: complete_action(context, accepted_by_ui=True)
        App->>Runtime: record_transition()
    end
```

## 模板识别链路

```mermaid
flowchart LR
    A["resources/templates/battle/*.png"] --> B["catalog.json"]
    B --> C["perception.TemplateCatalog"]
    C --> D["perception.OpenCvTemplateMatcher"]
    D --> E["MatchResult(confidence, bounds)"]
    E --> F["ObservationBuilder"]
    F --> G["BattleObservation"]
    G --> H["StateMachine / Policy"]
```

## 真实点击执行约束（当前阶段）

1. 涉及真实点击时，默认使用提权环境执行。
2. 游戏窗口需前台可聚焦，执行前先 `focus_window`。
3. 非战斗底栏优先使用网格化坐标：`start_x=870, step_x=40, y=792`。
4. 按钮命中优先走 `button_ref`（来自 `configs/ui/button-calibration.json`），避免硬编码散落坐标。

## 关键入口文件

- [run_battle_app.py](/D:/Codex/dhxy2-automation/scripts/run_battle_app.py)
- [bootstrap.py](/D:/Codex/dhxy2-automation/src/app/bootstrap.py)
- [service.py](/D:/Codex/dhxy2-automation/src/app/service.py)
- [observation_provider.py](/D:/Codex/dhxy2-automation/src/app/observation_provider.py)
- [translator.py](/D:/Codex/dhxy2-automation/src/executor/translator.py)
- [button_calibration.json](/D:/Codex/dhxy2-automation/configs/ui/button-calibration.json)
