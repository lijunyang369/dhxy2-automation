# 回合识别重构方案

## 1. 背景与结论

当前“回合识别”虽然在代码中以 `OCRReader` 命名，但实际实现并不是通用 OCR，而是：

1. 对战斗区域做固定颜色阈值筛选
2. 从固定比例区间裁出数字带
3. 用数字模板做整段匹配
4. 返回模板匹配分数作为“置信度”

这条链路对单一截图样本可以工作，但对真实运行场景不够稳。问题核心不在于“人眼看不清”，而在于当前方案对布局、缩放、抗锯齿、颜色波动和多位数字都过于敏感。

结论：

- 当前不稳定以“方案问题”为主，不是简单的参数使用问题
- 回合识别不应继续挂在通用 OCR 抽象下
- 应重构为独立的“回合识别模块”，采用专用区域、专用预处理、逐位识别和时序约束

## 2. 当前方案的主要问题

### 2.1 识别模型与命名不一致

当前实现名为 `BattleRoundOCRReader`，但本质是模板匹配，不是通用 OCR。  
这会带来两个问题：

- 置信度被误解为 OCR 置信度，实际只是模板相似度
- 后续设计容易继续往“调 OCR 参数”方向误投精力

### 2.2 位置假设过强

当前逻辑默认数字出现在 `battle_main` 内的固定比例区间。  
一旦截图区域有轻微偏移、缩放、UI 漂移或字体边缘变化，匹配分数就会明显下降。

### 2.3 目前只适合单数字

当前实现更接近“整段里找一个最像的数字”，而不是“识别完整回合数”。  
这对 `1-9` 勉强可用，但对 `10+`、多位数、数字粘连和笔画断裂都不稳。

### 2.4 战斗主区域过大

当前直接复用 `battle_main`。  
这个区域噪声太多，包含背景、人物、特效和其它 UI 变化，不适合作为回合数字的专用输入。

### 2.5 缺少时序约束

回合数是一个强时序信号。  
当前实现没有利用“上一回合是什么、下一回合最多应该是什么”的约束，因此单帧误识别会直接污染状态机判断。

## 3. 重构目标

重构后的回合识别需要满足：

1. 可独立测试，不依赖整条战斗链路
2. 专门面向“回合数字”这个问题，而不是复用通用 OCR
3. 支持多位数字
4. 输出结构化识别结果，而不是只返回一行文本
5. 引入时序约束，降低单帧误识别风险
6. 保持模块化，后续可以替换内部实现而不影响上层状态机

## 4. 目标模块划分

建议新增并拆分为以下模块：

### 4.1 `RoundRegionLocator`

职责：

- 从窗口截图中定位回合数字专用区域
- 输出稳定的 `round_number_region`

输入：

- `FrameCapture`
- `WindowInfo`
- 可选锚点区域配置

输出：

- `Rect`
- `locator_confidence`

设计要求：

- 不再直接复用 `battle_main`
- 优先基于锚点区域和相对偏移定位
- 一期允许先走固定专用区域，二期再引入锚点校准

### 4.2 `RoundImagePreprocessor`

职责：

- 对回合数字区域做专用预处理

处理建议：

- 放大
- 颜色空间转换
- 黄字/描边分离
- 去噪
- 二值化
- 形态学修复

输出：

- 原始 ROI
- 二值图
- 预处理质量指标

### 4.3 `RoundDigitSegmenter`

职责：

- 从预处理结果中分割出一个或多个数字 ROI

设计要求：

- 输出逐位数字块，而不是整段只给一个结果
- 每位数字要有边界框、面积、宽高比等特征
- 若无法稳定分割，要显式返回失败原因

### 4.4 `RoundDigitClassifier`

职责：

- 对每个数字 ROI 做分类

一期建议：

- 继续使用模板分类，但按“逐位数字”分类，不再做整段最佳匹配

二期建议：

- 可替换为更稳的轻量分类器

输出：

- `digit`
- `digit_confidence`
- `candidate_scores`

### 4.5 `RoundNumberAssembler`

职责：

- 将逐位数字组合成完整回合数

输出：

- `round_number`
- `digit_count`
- `assembly_confidence`

### 4.6 `RoundSequenceTracker`

职责：

- 基于上下文约束识别结果

约束规则建议：

- 回合数通常单调递增
- 单次跳变不应过大
- 若当前帧与上一帧冲突，可降级为“不确认”
- 可利用战斗状态和动作反馈判断是否应进入下一回合

输出：

- `accepted_round_number`
- `sequence_reason`
- `sequence_confidence`

### 4.7 `RoundRecognitionService`

职责：

- 编排整个回合识别流程

调用链建议：

`locator -> preprocessor -> segmenter -> classifier -> assembler -> tracker`

输出统一对象：

- `RoundRecognitionResult`

## 5. 统一输出模型

建议新增标准结果对象：

```python
@dataclass(frozen=True)
class RoundRecognitionResult:
    detected: bool
    round_number: int | None
    region: tuple[int, int, int, int] | None
    locator_confidence: float
    image_quality_confidence: float
    digit_confidences: tuple[float, ...]
    overall_confidence: float
    sequence_confidence: float
    reason: str
    digits: tuple[str, ...] = ()
```

关键约束：

- `overall_confidence` 不再等同于模板分数
- 必须区分定位置信度、逐位分类置信度、时序置信度
- 必须输出失败原因，方便诊断

## 6. 推荐识别策略

### 6.1 一期策略

一期不建议先接通用 OCR 引擎，而建议先做“专用回合数字识别”：

1. 单独配置 `round_number_region`
2. 对 ROI 做专用预处理
3. 做逐位分割
4. 用逐位模板分类
5. 用时序约束过滤异常结果

原因：

- 目标文本形式高度受限
- 数字样式相对固定
- 比直接上通用 OCR 更容易稳定和调试
- 中间证据更清晰，便于问题定位

### 6.2 二期策略

二期再考虑混合方案：

- 专用数字识别作为主路径
- PaddleOCR 作为旁路校验或兜底
- 当两路结果冲突时，交给 `RoundSequenceTracker` 统一裁决

## 7. 区域设计要求

建议在场景配置中单独增加：

```json
{
  "name": "round_number_region",
  "rect": [x1, y1, x2, y2],
  "use_template_match": false,
  "use_ocr": false
}
```

说明：

- 回合数字区域不再复用 `battle_main`
- `battle_main` 保留给战斗主场景观测
- 回合识别走专门的识别模块，不再混在通用 OCR 区域扫描里

## 8. 与现有状态机的集成方式

状态机层不应该自己解析 OCR 文本。  
建议由感知层直接给出结构化信号：

- `round_number`
- `round_indicator_visible`
- `round_recognition_reason`
- `round_recognition_confidence`

状态机只消费结构化结果，不关心内部是模板识别、OCR 还是混合方案。

## 9. 测试设计

### 9.1 单元测试

覆盖：

- 区域定位
- 预处理输出
- 单数字分类
- 多位数组装
- 时序约束

### 9.2 样本测试

建议建立回合数字样本集：

- 不同回合数
- 不同亮度
- 不同 UI 状态
- 不同特效干扰
- 不同截图批次

### 9.3 回归测试

每次修改都应验证：

- `1-9` 基础识别
- `10+` 多位识别
- 回合跳变约束
- 与战斗状态机的耦合回归

### 9.4 证据要求

每次识别至少保存：

- 原始 ROI
- 预处理图
- 分割后的逐位数字图
- 分类候选分数
- 最终输出结果

## 10. 分阶段落地建议

### Phase 1：专用区域与逐位识别

输出：

- `round_number_region`
- `RoundImagePreprocessor`
- `RoundDigitSegmenter`
- `RoundDigitClassifier`
- `RoundNumberAssembler`

目标：

- 先把单帧识别做稳

### Phase 2：时序约束与结果标准化

输出：

- `RoundSequenceTracker`
- `RoundRecognitionResult`
- 结构化状态信号接入

目标：

- 降低单帧误识别对状态机的影响

### Phase 3：双路径识别

输出：

- 专用数字识别主路径
- PaddleOCR 旁路校验
- 冲突裁决逻辑

目标：

- 提升复杂场景下的鲁棒性

## 11. 当前明确不建议继续做的事情

以下做法不建议继续扩大投入：

1. 继续在 `battle_main` 大区域上微调颜色阈值
2. 继续把整段数字带当成一个模板整体匹配
3. 继续把模板匹配分数理解为 OCR 置信度
4. 在没有时序约束的前提下直接用单帧结果驱动回合状态

## 12. 最终建议

回合识别应从“伪 OCR”改成“专用数字识别模块”。  
正确方向不是继续调当前阈值，而是把它重构为：

- 专用区域
- 专用预处理
- 逐位分割
- 逐位分类
- 多位数组装
- 时序校验

这条路线更符合本项目的模块化设计要求，也更符合“单独可测、变更更安全”的工程目标。
