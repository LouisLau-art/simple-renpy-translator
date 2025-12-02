# RenPy翻译工具重构计划书

## 项目背景分析

### 现有项目问题诊断

#### 1. 技术债务严重
- **依赖过重**：requirements_full.txt包含125个依赖包，weights超过500MB
- **版本兼容性差**：主要针对Python 3.8-3.11，在Python 3.13下存在严重兼容性问题
- **平台适配性差**：Windows优先，Linux支持不完善
- **核心功能故障**：RenPy注入系统无法在Python 3.13下工作，导致核心功能卡住

#### 2. 设计复杂度高
- **功能过度混合**：集成了AI翻译、Web翻译、UI界面等多种复杂功能
- **架构复杂**：注入系统、数据库、GUI、翻译引擎等多个子系统
- **命令体系庞大**：30+个命令，学习曲线陡峭
- **配置复杂**：config.yaml超过200行配置项

#### 3. 用户体验问题
- **安装困难**：需要处理复杂的依赖兼容性
- **运行卡住**：核心import功能在现代环境下无法正常工作
- **功能冗余**：很多高级功能普通用户用不到

## 项目重构方案

### 核心理念

**简约而不简单** - 提供RenPy游戏翻译的核心功能，去除不必要的复杂度

### 目标用户
- 游戏汉化组/翻译团队
- 个人游戏汉化爱好者
- 需要简单易用翻译工具的用户

### 核心功能
1. **游戏项目创建**：指定游戏目录创建翻译项目
2. **文本导出**：将未翻译文本导出为HTML/Excel格式
3. **翻译管理**：手动翻译导入，支持增量更新
4. **翻译生成**：将翻译结果生成RenPy翻译文件

## 技术架构设计

### 技术栈选择（AI友好）

#### 1. 核心技术
- **Python 3.13+**：使用最新稳定版本，向后兼容
- **标准库优先**：仅使用必要的第三方库
- **单文件架构**：避免复杂的模块依赖

#### 2. 依赖管理（最小化）
```python
# 基础依赖
openpyxl>=3.1.0          # Excel文件处理
beautifulsoup4>=4.12.0   # HTML解析
PyYAML>=6.0.0           # 配置文件
click>=8.1.0            # 命令行界面
colorama>=0.4.6         # 终端彩色输出
tqdm>=4.66.0            # 进度条
regex>=2023.8.0         # 正则表达式
```

**总计约10个依赖包，比原项目减少90%**

#### 3. 架构模式
```
simple_renpy_translator/
├── main.py              # 主程序入口
├── translator/          # 核心翻译模块
│   ├── __init__.py
│   ├── project.py       # 项目管理
│   ├── extractor.py     # 文本提取器
│   ├── exporter.py      # 导出器
│   ├── importer.py      # 导入器
│   └── generator.py     # RenPy文件生成器
├── utils/               # 工具模块
│   ├── __init__.py
│   ├── file_utils.py    # 文件操作
│   ├── renpy_utils.py   # RenPy相关工具
│   └── config.py        # 配置管理
└── requirements.txt     # 依赖文件
### 核心功能设计

#### 1. 项目管理系统
```python
class Project:
    def __init__(self, game_path: str):
        self.game_path = game_path
        self.name = self._extract_project_name()
        self.source_dir = os.path.join(game_path, 'game')
        self.tl_dir = os.path.join(game_path, 'game', 'tl')
    
    def scan_texts(self, lang: str) -> List[TextBlock]:
        """扫描指定语言的文本内容"""
        pass
    
    def get_untranslated_texts(self, lang: str) -> List[TextBlock]:
        """获取未翻译文本"""
        pass
```

#### 2. 文本提取器
```python
class TextExtractor:
    def extract_from_rpy(self, file_path: str) -> List[TextBlock]:
        """从RPY文件提取文本"""
        pass
    
    def extract_from_rpyc(self, file_path: str) -> List[TextBlock]:
        """从RPYC文件提取文本（如果存在）"""
        pass
    
    def parse_dialogue_text(self, content: str) -> List[TextBlock]:
        """解析对话文本"""
        pass
```

#### 3. 导出系统
```python
class Exporter:
    def export_to_html(self, texts: List[TextBlock], output_path: str):
        """导出为HTML格式"""
        pass
    
    def export_to_excel(self, texts: List[TextBlock], output_path: str):
        """导出为Excel格式"""
        pass
```

#### 4. 导入系统
```python
class Importer:
    def import_from_html(self, file_path: str) -> List[Translation]:
        """从HTML文件导入翻译"""
        pass
    
    def import_from_excel(self, file_path: str) -> List[Translation]:
        """从Excel文件导入翻译"""
        pass
```

#### 5. 生成系统
```python
class Generator:
    def generate_rpy_files(self, translations: List[Translation], lang: str):
        """生成RenPy翻译文件"""
        pass
    
    def merge_existing_translations(self, lang: str, new_translations: List[Translation]):
        """合并现有翻译"""
        pass
```

### 命令行界面设计

#### 1. 核心命令（简化）
```
# 项目管理
rt-init <game_path>           # 初始化项目
rt-list                       # 列出项目

# 文本处理
rt-scan <project> -l <lang>   # 扫描文本
rt-export <project> -l <lang> [-f html|excel]  # 导出文本
rt-import <project> -l <lang> [-f html|excel]  # 导入翻译
rt-generate <project> -l <lang> # 生成翻译文件

# 辅助命令
rt-status <project> -l <lang> # 查看翻译状态
rt-help                       # 显示帮助
```

#### 2. 配置管理
```yaml
# config.yaml
project:
  default_export_format: html  # 默认导出格式
  output_dir: ./exports        # 输出目录

translation:
  keep_formatting: true        # 保持文本格式
  skip_empty: true            # 跳过空文本
  backup_original: true       # 备份原文

excel:
  max_rows_per_sheet: 1000    # Excel最大行数
  include_comments: true      # 包含注释

html:
  template: default           # HTML模板
  auto_translate: false      # 自动翻译标记
```
## 实现策略

### 阶段一：核心功能开发（优先级：极高）
1. **项目扫描功能**
   - 解析游戏目录结构
   - 扫描RPY/RPYC文件
   - 提取可翻译文本

2. **导出功能**
   - HTML格式导出（简单易用）
   - Excel格式导出（适合批量处理）
   - 支持增量导出

3. **基础导入功能**
   - 从HTML文件导入翻译
   - 从Excel文件导入翻译
   - 基本的验证机制

### 阶段二：高级功能（优先级：高）
1. **翻译生成**
   - 生成标准RenPy翻译文件
   - 合并现有翻译
   - 备份机制

2. **项目管理**
   - 项目状态管理
   - 翻译进度跟踪
   - 增量更新支持

### 阶段三：优化功能（优先级：中）
1. **用户体验**
   - 彩色输出
   - 进度条
   - 错误处理优化

2. **扩展功能**
   - 自定义模板
   - 批量处理
   - 翻译缓存

## 开发重点

### 1. 兼容性优先
- **Python 3.13+完全兼容**
- **跨平台支持**（Windows/Linux/macOS）
- **RenPy版本兼容**（支持主流RenPy版本）

### 2. 简单易用
- **零配置启动**：开箱即用
- **清晰文档**：详细使用说明
- **错误友好**：清晰的错误提示和解决建议

### 3. 稳定可靠
- **数据安全**：自动备份机制
- **错误恢复**：支持中断恢复
- **数据验证**：导入时验证翻译完整性

### 4. 性能优化
- **内存效率**：大文件处理优化
- **处理速度**：批量操作优化
- **存储效率**：项目文件压缩

## 开发里程碑

### Milestone 1: 基础框架（预计1-2天）
- [ ] 项目结构搭建
- [ ] 命令行界面实现
- [ ] 配置文件系统
- [ ] 基础文件操作

### Milestone 2: 文本处理（预计2-3天）
- [ ] RPY文件解析器
- [ ] 文本提取算法
- [ ] 文本分类和标记
- [ ] 增量扫描功能

### Milestone 3: 导出导入（预计2-3天）
- [ ] HTML导出器
- [ ] Excel导出器
- [ ] HTML导入器
- [ ] Excel导入器

### Milestone 4: 翻译生成（预计1-2天）
- [ ] RenPy文件生成器
- [ ] 翻译合并算法
- [ ] 备份系统

### Milestone 5: 优化测试（预计1-2天）
- [ ] 错误处理完善
- [ ] 用户体验优化
- [ ] 跨平台测试
- [ ] 性能优化

**总计开发时间：7-12天**

## 风险评估与应对

### 风险1：RenPy文件格式兼容性
**问题**：不同版本的RenPy生成的文件格式可能存在差异
**应对**：
- 广泛的测试覆盖
- 版本检测和适配机制
- 详细的错误报告

### 风险2：大文件处理性能
**问题**：大型游戏的文本文件可能很大
**应对**：
- 流式处理机制
- 内存使用优化
- 进度显示

### 风险3：数据完整性
**问题**：翻译过程中可能出现数据丢失
**应对**：
- 自动备份机制
- 事务性操作
- 数据验证

## 项目收益

### 1. 技术收益
- **现代化技术栈**：Python 3.13+完全支持
- **简化架构**：从125个依赖减少到10个
- **跨平台兼容**：真正支持Linux/Windows/macOS

### 2. 用户收益
- **即装即用**：解决依赖问题
- **功能聚焦**：专注核心翻译需求
- **学习成本低**：简单直观的命令

### 3. 维护收益
- **代码简洁**：便于AI维护和扩展
- **依赖简单**：减少兼容性问题
- **架构清晰**：便于理解和修改

## 总结

通过重构现有项目，我们能够：
1. **解决Python 3.13兼容性问题**
2. **简化用户使用流程**
3. **提高系统稳定性**
4. **便于AI开发维护**

新项目将专注于RenPy游戏翻译的核心需求，去除不必要的复杂度，提供一个真正简单易用、稳定可靠的翻译工具。

---

**项目名称建议**：`simple-renpy-translator` 或 `easy-renpy-translator`  
**开发方式**：推荐使用AI助手进行开发，遵循本计划书的架构设计和实现策略  
**开源协议**：建议使用MIT或Apache 2.0协议，便于社区贡献和维护