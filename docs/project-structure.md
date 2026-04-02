# 《大话西游2》自动化项目目录结构说明

## 1. 文档目的

本文档定义 `D:\Codex\dhxy2-automation` 的首版项目目录骨架，作为后续实现、协作和评审的统一结构基线。

本目录骨架面向整个《大话西游2》自动化项目，不只服务战斗能力，还为后续任务流、界面识别、账号管理、调度、测试与证据留存预留空间。

## 2. 推荐目录结构

```text
D:\Codex\dhxy2-automation
├─ .venv
├─ docs
│  └─ knowledge
├─ src
│  ├─ platform
│  ├─ perception
│  ├─ domain
│  ├─ state_machine
│  ├─ policy
│  ├─ executor
│  ├─ runtime
│  └─ app
├─ configs
│  ├─ env
│  ├─ accounts
│  ├─ characters
│  ├─ scenarios
│  ├─ ui
│  └─ logging
├─ resources
│  ├─ templates
│  │  ├─ common
│  │  ├─ battle
│  │  ├─ skills
│  │  └─ states
│  ├─ ocr
│  │  └─ profiles
│  └─ resolutions
├─ tests
│  ├─ smoke
│  ├─ regression
│  ├─ stability
│  └─ fixtures
├─ runs
│  └─ artifacts
└─ scripts
```

## 3. 目录职责

### `.venv`

项目专用虚拟环境。

要求：

- 仅用于本项目依赖隔离
- 不提交运行产物和临时脚本
- 通过项目根目录统一引用

### `docs`

存放架构、规范、状态机、资源组织和实施计划等文档。

其中 `docs/knowledge` 专门承载游戏知识资料，按三层结构组织：

- 页面索引层：定位原始资料页面
- 逐页摘要层：沉淀页面核心信息
- 项目规则层：抽取代码和配置可直接消费的规则

要求：

- 文档先行，代码跟随
- 架构变更优先更新文档基线
- 其他线程优先读取这里的文档继续协作
- 游戏知识文档优先沉淀到 `docs/knowledge`

### `src`

存放正式源码，是项目的唯一主代码目录。

子目录职责：

- `platform`：窗口、句柄、输入、截图、坐标换算
- `perception`：模板匹配、区域识别、OCR、预处理
- `domain`：领域模型、状态对象、动作对象、异常定义
- `state_machine`：状态解析、迁移规则、恢复入口
- `policy`：角色策略、技能策略、目标选择规则
- `executor`：动作执行序列、点击流程、确认流程
- `runtime`：主循环、超时、重试、证据采集、会话管理
- `app`：入口、任务编排、运行配置装配

### `configs`

存放可配置数据，不在业务代码中散落硬编码。

子目录职责：

- `env`：环境配置
- `accounts`：账号和窗口实例配置
- `characters`：角色与技能配置
- `scenarios`：场景或玩法策略配置
- `ui`：按钮校准和界面定位配置
- `logging`：日志输出规则配置

### `resources`

存放运行依赖资源。

子目录职责：

- `templates`：模板图片
- `ocr/profiles`：OCR 场景参数配置
- `resolutions`：分辨率或窗口尺寸适配配置

### `tests`

存放测试代码和测试样本。

子目录职责：

- `smoke`：最小闭环测试
- `regression`：回归场景测试
- `stability`：长稳场景测试
- `fixtures`：测试输入样本和固定截图

### `runs`

存放运行过程产物。

要求：

- 不与源码混放
- 每次运行按实例和会话隔离
- 作为日志、截图、识别结果、动作结果的统一归档目录

### `scripts`

存放辅助脚本。

要求：

- 仅放辅助工具、初始化工具、检查脚本
- 不把正式业务逻辑堆进脚本目录

## 4. 结构约束

必须遵守以下规则：

1. 正式业务代码只放在 `src`
2. 配置不混入源码目录
3. 资源不混入测试目录
4. 运行产物不混入代码目录
5. 临时脚本不替代正式模块
6. 新增一级目录必须有明确职责说明

## 5. 当前阶段建议

当前阶段先以这套骨架作为实现基线。

后续若增加新的自动化能力，例如任务流、巡检、背包管理、交易流程或多开调度，应优先在现有骨架内扩展，而不是重新平铺目录。
