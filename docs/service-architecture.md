# 《大话西游2》自动化服务架构图

## 1. 文档目的

本文档从“服务协作”视角描述 `dhxy2-automation` 当前架构。

这份图不替代模块拆解图，重点回答三个问题：

- 系统从哪个入口启动
- 核心服务之间如何协作
- 外部依赖和运行期支撑挂在哪一层

## 2. 服务架构总图

```mermaid
flowchart LR
    subgraph Entry["入口层"]
        Scripts["scripts/*\n命令行入口"]
        Gui["src/gui/*\n桌面工具与工作台"]
    end

    subgraph App["应用编排层"]
        Bootstrap["app/bootstrap.py\n依赖装配与启动"]
        AppService["app/service.py\nBattleAutomationApp"]
        Feedback["app/action_feedback.py\nActionFeedbackVerifier"]
    end

    subgraph Core["核心业务层"]
        Observe["app/observation_provider.py\nDefaultObservationProvider"]
        State["state_machine/*\nBattleStateMachine"]
        Policy["policy/*\nFixedRulePolicy / Planner"]
        Exec["executor/*\nActionExecutor"]
    end

    subgraph Perception["感知层"]
        Match["perception/*\n模板识别 / 区域识别 / 回合识别"]
        OCR["ocr-service\n外部 OCR 服务"]
    end

    subgraph Platform["平台接入层"]
        Window["platform/*\nWindowSession / Finder / Gateway"]
        Input["executor/InputGateway\nWin32 输入注入"]
        Client["Windows 游戏客户端\n《大话西游2》"]
    end

    subgraph Runtime["运行期支撑层"]
        RuntimeSession["runtime/session_runtime.py\nRuntimeSession"]
        Artifact["runtime/artifacts.py\nArtifactWriter"]
        Logger["runtime/logger.py\nRuntimeLogger"]
        Runs["runs/artifacts\n证据与日志归档"]
    end

    subgraph Config["配置与资源层"]
        Configs["configs/*\n账号 / 场景 / UI / 知识配置"]
        Resources["resources/*\n模板 / 图标 / 识别资源"]
    end

    Scripts --> Bootstrap
    Gui --> Bootstrap

    Bootstrap --> Configs
    Bootstrap --> Resources
    Bootstrap --> Window
    Bootstrap --> Observe
    Bootstrap --> State
    Bootstrap --> Policy
    Bootstrap --> Exec
    Bootstrap --> RuntimeSession
    Bootstrap --> AppService

    AppService --> Observe
    AppService --> State
    AppService --> Policy
    AppService --> Exec
    AppService --> Feedback
    AppService --> RuntimeSession

    Observe --> Match
    Observe --> Window
    Match -. 可选 OCR 调用 .-> OCR

    Exec --> Input
    Input --> Window
    Window --> Client
    Observe --> Client

    RuntimeSession --> Artifact
    RuntimeSession --> Logger
    Artifact --> Runs
    Logger --> Runs
```

## 3. 单次 Tick 服务链路

```mermaid
sequenceDiagram
    participant Entry as 入口脚本 / GUI
    participant Boot as Bootstrap
    participant App as BattleAutomationApp
    participant Obs as ObservationProvider
    participant Win as WindowSession
    participant SM as BattleStateMachine
    participant Pol as Policy
    participant Exe as ActionExecutor
    participant FB as ActionFeedbackVerifier
    participant RT as RuntimeSession

    Entry->>Boot: 启动并装配依赖
    Boot->>App: 创建应用实例
    Entry->>App: run_once()

    App->>Obs: observe(window_session)
    Obs->>Win: snapshot() + capture_client()
    Obs-->>App: BattleObservation
    App->>RT: record_observation()

    App->>SM: tick(observation, context)
    SM-->>App: TransitionResult
    App->>RT: record_transition()

    App->>Pol: build_plan(observation, context)
    Pol-->>App: ActionPlan

    alt 有动作
        App->>SM: begin_action(plan, context)
        App->>RT: record_transition()
        loop 对每个动作
            App->>RT: record_action()
            App->>Exe: execute(action)
            Exe->>Win: click / press / wait
        end
        App->>Obs: observe(window_session)
        Obs-->>App: feedback observation
        App->>RT: record_observation()
        App->>FB: verify_plan(before, after)
        FB-->>App: accepted / rejected
        App->>SM: complete_action(accepted_by_ui)
        App->>RT: record_transition()
    else 无动作
        App-->>Entry: 返回空计划结果
    end
```

## 4. 服务职责摘要

| 服务 | 位置 | 职责 |
| --- | --- | --- |
| Bootstrap | `src/app/bootstrap.py` | 装配窗口会话、配置、识别器、状态机、策略、执行器和运行期对象 |
| BattleAutomationApp | `src/app/service.py` | 单次 tick 编排中心，驱动观察、状态迁移、动作执行和反馈闭环 |
| DefaultObservationProvider | `src/app/observation_provider.py` | 把窗口截图、命名区域、模板匹配结果汇总成 `BattleObservation` |
| BattleStateMachine | `src/state_machine/*` | 根据观察结果维护当前战斗状态并控制迁移 |
| FixedRulePolicy / Planner | `src/policy/*` | 根据角色配置和观察结果生成动作计划 |
| ActionExecutor | `src/executor/*` | 将领域动作翻译为输入序列并执行 |
| RuntimeSession | `src/runtime/*` | 记录 observation、transition、action，并写入证据和日志 |
| OCR Service | 外部独立仓库 | 提供可选 OCR 能力，不与主项目运行时强耦合 |

## 5. 当前图的使用原则

- 模块拆解图用于看“功能范围”和完成度
- 本文服务架构图用于看“运行时协作关系”
- 后续如果增加调度器、多开管理器、OCRClient 或任务流引擎，应优先在本图中补充服务位置，再落代码实现
