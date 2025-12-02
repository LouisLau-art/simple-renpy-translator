# Simple RenPy Translator - JSON版本使用说明

## 项目概述

Simple RenPy Translator 的 JSON 版本是一个 RenPy 游戏本地化工具，包含两个主要组件：

- **extractor.py** (提取器): 从 RenPy 脚本中提取可翻译的文本
- **injector.py** (注入器): 将翻译后的文本注入到 RenPy 翻译文件中

## 工作流程

```
RenPy 脚本 (game/*.rpy) 
    ↓ 
extractor.py 
    ↓ 
translation_work.json (包含原文)
    ↓ 
翻译器 (豆包 API) 
    ↓ 
translation_work.json (包含译文)
    ↓ 
injector.py 
    ↓ 
game/tl/schinese/*.rpy (RenPy 翻译文件)
```

## 文件说明

### 1. extractor.py (提取器)

**功能**: 扫描 game 目录下的所有 .rpy 文件，提取可翻译的文本

**使用方法**:
```bash
python extractor.py
```

**输出**: 
- `translation_work.json`: 包含提取的原文，translated 字段初始为 null

### 2. injector.py (注入器)

**功能**: 读取包含译文的 JSON 文件，生成 RenPy 翻译文件

**使用方法**:
```bash
python injector.py
```

**输入**: 
- `translation_work.json`: 包含翻译后的文本

**输出**:
- `game/tl/schinese/*.rpy`: RenPy 标准翻译文件

## JSON 数据结构

```json
[
  {
    "id": "script_20_a1b2c3d4",          // 唯一标识符
    "file": "game/script.rpy",           // 原始文件路径
    "line": 20,                          // 行号
    "type": "dialogue",                  // 类型: dialogue 或 string
    "original": "Hello, world!",         // 原文
    "translated": "你好，世界！",         // 译文
    "context": "eileen happy"            // 上下文信息（可选）
  }
]
```

## 实际使用步骤

### 步骤1: 提取原文
```bash
# 确保项目中有 game 目录和 .rpy 文件
python extractor.py
```

### 步骤2: 翻译文本
1. 打开生成的 `translation_work.json` 文件
2. 在每个条目的 `translated` 字段中填入翻译
3. 保持 `original` 字段不变

**示例**:
```json
{
  "id": "script_20_a1b2c3d4",
  "file": "game/script.rpy",
  "line": 20,
  "type": "dialogue",
  "original": "Hello, world!",
  "translated": "你好，世界！",  // 这里填入翻译
  "context": "eileen happy"
}
```

### 步骤3: 生成翻译文件
```bash
python injector.py
```

## 输出格式示例

生成的翻译文件 (`game/tl/schinese/script.rpy`)：

```python
# RenPy 翻译文件 - Simple RenPy Translator
# 语言: schinese
# 生成时间: 2025-12-02 13:32:24
...

# game/script.rpy:20
translate schinese script_20_a1b2c3d4:
    "你好，世界！"
```

## 特性说明

### 智能文本过滤
- ✅ 提取对话文本: `"Hello, world!"`
- ✅ 提取变量字符串: `title = "My Game"`
- ❌ 排除代码关键字: `label`, `jump`, `call`
- ❌ 排除文件路径: `"images/logo.png"`
- ❌ 排除短文本: 单个字母或数字

### 支持的文本类型
- **对话**: 角色名后跟的文本
- **字符串**: 变量赋值中的文本

### 特殊字符处理
- 自动转义换行符: `\n` → `\\n`
- 智能引号处理: 自动选择单引号或双引号
- 保持 Unicode 字符完整性

## 目录结构

```
项目目录/
├── game/                    # RenPy 游戏目录
│   ├── script.rpy          # 原始脚本文件
│   └── ...
├── tl/schinese/            # 生成的翻译文件目录
│   ├── script.rpy          # 中文翻译文件
│   └── ...
├── translation_work.json   # 翻译工作文件
├── extractor.py            # 提取器脚本
└── injector.py             # 注入器脚本
```

## 依赖要求

- Python 3.13+
- 无需额外依赖库

## 注意事项

1. **备份原文件**: 建议在首次使用前备份重要文件
2. **编码格式**: 所有文件使用 UTF-8 编码
3. **路径要求**: 项目根目录必须包含 `game/` 目录
4. **翻译文件**: 生成的翻译文件将覆盖同名文件

## 错误排查

### 常见问题
1. **找不到 game 目录**: 确保在 RenPy 项目根目录下运行
2. **没有提取到文本**: 检查 .rpy 文件格式是否正确
3. **翻译文件为空**: 确认 JSON 文件中 translated 字段已填写

### 调试信息
- 脚本会输出详细的处理日志
- 使用 `--verbose` 参数可获得更多调试信息（如果实现）

## 版本信息

- 版本: v1.0.0 (JSON版本)
- 适用环境: Python 3.13
- 支持语言: 中文简体（schinese）
- 创建时间: 2025-12-02

---

**注意**: 这是纯 JSON 版本的实现，不包含 HTML 翻译界面。所有翻译工作需要手动编辑 JSON 文件或通过外部翻译工具完成。