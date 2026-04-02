# 当前提交审查总结（2026-03-31）

## 审查范围

本次审查面向 `dhxy2-automation` 当前工作区改动，重点覆盖：

- 运行入口
- 配置变更
- 新增知识加载能力
- 测试补充
- 文档与目录一致性
- 工作区提交卫生

## 结论

当前改动整体方向是正确的，尤其是：

- 分层没有明显失控
- `run_battle_app.py` 已从演示入口提升为真实运行入口
- `WindowFinder` 的 handle 匹配逻辑更稳健
- 新增的知识配置体系开始形成结构化入口
- smoke 测试在项目根目录下可通过

但当前提交仍有 3 个需要优先整改的问题，建议在后续提交前处理。

## 问题 1：工作区临时文件混入提交候选范围

现象：

- `D:\Codex` 根目录存在多个 `_tmp_*` 文件
- 这些文件当前会出现在 Git 状态里

涉及文件示例：

- `D:\Codex\_tmp_464.html`
- `D:\Codex\_tmp_464.png`
- `D:\Codex\_tmp_483.html`
- `D:\Codex\_tmp_483.png`
- `D:\Codex\_tmp_dh2_baike_summaries.json`

影响：

- 破坏工作区提交卫生
- 容易把临时调研产物误提交进仓库
- 会干扰其它线程判断哪些内容属于正式项目资产

建议：

1. 将这些 `_tmp_*` 文件迁移到 `archive` 或项目内专门的临时资料目录
2. 在根级 `.gitignore` 中补充 `_tmp_*`
3. 将“临时抓取文件不得留在工作区根目录”写入工作区规则

## 问题 2：知识配置加载缺少路径边界校验

涉及文件：

- `src/app/profile_loader.py`

关键位置：

- `CharacterProfileLoader._load_json()`

当前实现：

- 使用 `(base_path.parent / relative_ref).resolve()` 直接拼装并读取引用文件

风险：

- 配置中的相对路径如果被误写或被滥用，可以跳出预期目录
- 当前没有限制 `knowledge_refs` 只能指向项目内允许的知识配置目录
- 这会削弱配置驱动体系的边界安全性

建议：

1. 明确允许引用的根目录，例如 `configs/knowledge`
2. 在解析后校验目标路径必须落在允许目录内
3. 发现越界路径时抛出明确异常，而不是直接读取

## 问题 3：新增测试仍然硬编码工作区绝对路径

涉及文件：

- `tests/smoke/test_profile_loader.py`
- `tests/smoke/test_bootstrap.py`
- `tests/smoke/test_window_binding.py`

现象：

- 测试中直接写死 `D:/Codex/dhxy2-automation`

影响：

- 测试可移植性差
- 换工作区、换机器、换目录后会直接失效
- 其它线程复制测试模式时会继续扩散绝对路径依赖

建议：

1. 统一通过 `Path(__file__).resolve()` 反推项目根目录
2. 测试禁止写死工作区绝对路径
3. 后续测试样例都按同一规则修正

## 已验证项

已使用以下命令在项目根目录验证 smoke 测试：

```powershell
D:\Codex\dhxy2-automation\.venv\Scripts\python.exe -m unittest discover -s tests/smoke -t .
```

结果：

- `Ran 31 tests`
- `OK`

## 后续整改顺序建议

1. 先清理 `_tmp_*` 文件并补 `.gitignore`
2. 再给 `profile_loader.py` 增加路径边界校验
3. 最后统一修正测试中的绝对路径写法

## 给其它线程的协作要求

后续线程在继续修改本项目时，应遵守以下约束：

1. 不提交工作区根目录的临时文件
2. 配置引用路径必须有边界校验
3. 测试不得写死 `D:/Codex/...` 绝对路径
4. 提交前至少跑一轮 smoke 测试
