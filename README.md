# Simple RenPy Translator

一个专为RenPy游戏设计的文本翻译提取与注入工具，支持从RenPy项目中提取可翻译文本并生成结构化的翻译文件。

## 功能特性

- **智能文本提取**：自动识别和提取RenPy项目中的可翻译文本
- **ID生成系统**：为每个文本块生成唯一标识符，避免翻译冲突
- **多编码支持**：自动检测文件编码（UTF-8、GBK、Shift-JIS等）
- **翻译文件注入**：将翻译后的文本自动注入到RenPy翻译目录
- **黑名单过滤**：智能过滤不需要翻译的内容（代码、文件名等）

## 安装要求

- Python 3.13+
- 依赖包（见requirements.txt）

### 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 提取文本

从RenPy游戏的`game`目录中提取所有可翻译的文本：

```bash
python renpy_tool.py extract -g game -o translation_work.json
```

参数说明：
- `-g, --game-dir`：RenPy游戏目录（默认：game）
- `-o, --output`：输出JSON文件（默认：translation_work.json）

### 2. 翻译文本

使用任何文本编辑器或翻译工具编辑生成的JSON文件，为`translated`字段填入翻译内容：

```json
{
  "id": "script_001_a1b2c3d4",
  "file": "script.rpy",
  "line": 15,
  "original": "Hello, world!",
  "translated": "你好，世界！"
}
```

### 3. 注入翻译

将翻译后的文本注入到RenPy翻译目录：

```bash
python renpy_tool.py inject -i translation_work.json -g game -l schinese
```

参数说明：
- `-i, --input`：包含翻译数据的JSON文件
- `-g, --game-dir`：RenPy游戏目录
- `-l, --language`：目标语言代码（如：schinese、english等）

## 生成的文件结构

```
your_renpy_game/
├── game/
│   ├── script.rpy         # 原始脚本文件
│   └── ...
└── tl/
    └── schinese/          # 翻译语言目录
        └── script.rpy     # 生成的翻译文件
```

## 输出格式

提取的JSON文件包含以下字段：

```json
{
  "id": "文本唯一标识符",
  "file": "源文件路径", 
  "line": "行号",
  "original": "原始文本",
  "translated": "翻译文本（留空待填写）"
}
```

## 智能过滤

工具会自动过滤以下内容：

- RenPy关键字（label, jump, call等）
- 文件路径和资源引用
- 颜色代码和样式属性
- 变量名和代码片段
- 文件扩展名和路径

## 高级功能

### 自定义游戏目录

```bash
python renpy_tool.py extract -g /path/to/your/game -o my_translations.json
```

### 自定义语言代码

```bash
python renpy_tool.py inject -i translated.json -g game -l japanese
```

## 注意事项

1. 备份原始文件：使用前请备份您的RenPy项目
2. 编码问题：工具支持多种编码，但建议使用UTF-8编码的文件
3. 翻译质量：工具只负责提取和注入，翻译质量取决于人工翻译或外部翻译工具
4. 重复运行：可以多次运行提取和注入命令，工具会智能处理已存在的数据

## 项目结构

```
simple-renpy-translator/
├── renpy_tool.py          # 主程序文件
├── requirements.txt       # Python依赖
├── README.md             # 项目说明
└── (生成的翻译文件)
```

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request来改进这个工具！

## 支持

如果您遇到问题或有功能建议，请在GitHub上创建Issue。