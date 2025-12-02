#!/usr/bin/env python3
"""
RenPy 文本提取器 (Extractor)
递归扫描 game/ 目录下的 .rpy 文件，提取可翻译的文本
"""

import hashlib
import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys


class RenPyExtractor:
    """RenPy 文件文本提取器"""
    
    # 关键字模式，需要排除的行
    IGNORE_PATTERNS = [
        re.compile(r'^\s*label\s+', re.MULTILINE),          # 标签定义
        re.compile(r'^\s*jump\s+', re.MULTILINE),          # 跳转语句
        re.compile(r'^\s*call\s+', re.MULTILINE),          # 调用语句
        re.compile(r'^\s*scene\s+', re.MULTILINE),         # 场景切换
        re.compile(r'^\s*show\s+', re.MULTILINE),          # 显示图像
        re.compile(r'^\s*hide\s+', re.MULTILINE),          # 隐藏图像
        re.compile(r'^\s*play\s+', re.MULTILINE),          # 播放音频
        re.compile(r'^\s*stop\s+', re.MULTILINE),          # 停止音频
        re.compile(r'^\s*with\s+', re.MULTILINE),          # 转换效果
        re.compile(r'^\s*init\s*:', re.MULTILINE),         # 初始化块
        re.compile(r'^\s*python\s*:', re.MULTILINE),       # Python 块
        re.compile(r'^\s*#.*$', re.MULTILINE),             # 注释行
        re.compile(r'^\s*$', re.MULTILINE),                # 空行
    ]
    
    # 文件扩展名模式，用于排除文件路径
    FILE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.ogg', '.mp3', '.wav', '.mp4', '.webm', '.ttf', '.otf', '.pyc'}
    
    # 目录黑名单：这些目录不应该被扫描
    DIRECTORY_BLACKLIST = ['tl', 'renpy', 'cache', 'saved']
    
    # 文件名黑名单：这些文件不应该被扫描
    FILE_PREFIX_BLACKLIST = ['00', 'gui.', 'gui_']
    
    def __init__(self):
        """初始化提取器"""
        self.extracted_texts: List[Dict[str, Any]] = []
        self.skipped_files = []
        self.total_files = 0
    
    def should_skip_file(self, file_path: Path, game_dir: Path) -> bool:
        """
        检查是否应该跳过该文件
        
        Args:
            file_path: 文件路径
            game_dir: 游戏根目录
            
        Returns:
            True 表示应该跳过
        """
        # 检查文件名前缀黑名单
        for prefix in self.FILE_PREFIX_BLACKLIST:
            if file_path.name.startswith(prefix):
                return True
        
        # 检查文件是否在黑名单目录中
        relative_path = file_path.relative_to(game_dir)
        
        # 检查路径中的每个部分是否在黑名单中
        for part in relative_path.parts:
            if part in self.DIRECTORY_BLACKLIST:
                return True
        
        return False
    
    def extract_from_game_directory(self, game_dir: Path = Path("game")) -> List[Dict[str, Any]]:
        """
        从 game 目录提取所有可翻译文本
        
        Args:
            game_dir: game 目录路径，默认为当前目录下的 game
            
        Returns:
            提取的文本列表
        """
        print(f"🔍 开始扫描 game 目录: {game_dir.absolute()}")
        
        if not game_dir.exists():
            print(f"❌ 错误: 找不到 game 目录: {game_dir}")
            return []
        
        # 递归查找所有 .rpy 文件
        all_rpy_files = list(game_dir.rglob("*.rpy"))
        
        # 过滤掉不需要的文件
        rpy_files = []
        for rpy_file in all_rpy_files:
            if self.should_skip_file(rpy_file, game_dir):
                continue
            rpy_files.append(rpy_file)
        
        print(f"📁 总共找到 {len(all_rpy_files)} 个 .rpy 文件，过滤后剩下 {len(rpy_files)} 个文件")
        
        # 统计跳过的文件
        skipped_count = len(all_rpy_files) - len(rpy_files)
        if skipped_count > 0:
            print(f"⚠️ 跳过了 {skipped_count} 个文件 (包括翻译文件、引擎文件等)")
        
        # 提取每个文件中的文本
        for rpy_file in rpy_files:
            self._extract_from_file(rpy_file)
        
        print(f"✅ 提取完成，共找到 {len(self.extracted_texts)} 个可翻译文本")
        return self.extracted_texts
    
    def _extract_from_file(self, file_path: Path) -> None:
        """
        从单个 .rpy 文件中提取文本
        
        Args:
            file_path: .rpy 文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"⚠️ 警告: 无法读取文件 {file_path}: {e}")
            return
        
        for line_num, line in enumerate(lines, 1):
            # 检查是否应该跳过这一行
            if self._should_ignore_line(line):
                continue
            
            # 提取双引号内的文本
            self._extract_quoted_texts(line, file_path, line_num)
    
    def _should_ignore_line(self, line: str) -> bool:
        """
        检查是否应该忽略这一行
        
        Args:
            line: 文本行
            
        Returns:
            True 表示应该忽略，False 表示需要处理
        """
        stripped_line = line.strip()
        
        # 检查是否符合忽略模式
        for pattern in self.IGNORE_PATTERNS:
            if pattern.match(line):
                return True
        
        return False
    
    def _extract_quoted_texts(self, line: str, file_path: Path, line_num: int) -> None:
        """
        提取一行中的所有引号文本
        
        Args:
            line: 文本行
            file_path: 文件路径
            line_num: 行号
        """
        # 匹配双引号内的内容
        pattern = r'"([^"]*)"'
        matches = re.finditer(pattern, line)
        
        for match in matches:
            text = match.group(1).strip()
            
            # 检查文本是否需要翻译
            if self._is_translatable_text(text):
                # 生成唯一 ID
                text_id = self._generate_id(file_path, line_num, text)
                
                # 判断文本类型
                text_type = self._classify_text_type(line, text)
                
                # 创建文本条目
                text_entry = {
                    "id": text_id,
                    "file": str(file_path.relative_to(file_path.parent.parent)),  # 相对于项目根目录
                    "line": line_num,
                    "type": text_type,
                    "original": text,
                    "translated": None,  # 初始为 null，等待翻译器填充
                    "context": self._extract_context(line, text)
                }
                
                self.extracted_texts.append(text_entry)
    
    def _is_translatable_text(self, text: str) -> bool:
        """
        判断文本是否需要翻译
        
        Args:
            text: 要检查的文本
            
        Returns:
            True 表示需要翻译，False 表示不需要
        """
        # 清理文本
        cleaned_text = text.strip().strip('"\'')
        
        # 跳过很短的文本
        if len(cleaned_text) < 2:
            return False
        
        # 1. 过滤颜色代码 (十六进制格式)
        if self._is_color_code(cleaned_text):
            return False
        
        # 2. 过滤系统指令
        if self._is_system_instruction(cleaned_text):
            return False
        
        # 3. 过滤纯代码/标识符
        if self._is_code_identifier(cleaned_text):
            return False
        
        # 4. 跳过看起来像代码或变量的文本
        if cleaned_text.startswith(('$', '{', '[')) or '{' in cleaned_text:
            return False
        
        # 5. 跳过文件路径
        if self._is_file_path(cleaned_text):
            return False
        
        # 6. 跳过看起来像标识符的单词
        if len(cleaned_text.split()) == 1 and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', cleaned_text):
            return False
        
        # 7. 跳过全数字或全特殊字符
        letters = sum(1 for c in cleaned_text if c.isalpha())
        if letters == 0:
            return False
        
        return True
    
    def _is_color_code(self, text: str) -> bool:
        """检查是否是颜色代码"""
        # 十六进制颜色格式 (#fff, #ffffff, #123456)
        hex_pattern = re.compile(r'^#[0-9a-fA-F]{3,6}$')
        if hex_pattern.match(text):
            return True
        
        # 常见的颜色值模式
        color_patterns = [
            r'rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)',  # rgb(255, 0, 0)
            r'rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)',  # rgba(255, 0, 0, 0.5)
        ]
        
        for pattern in color_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def _is_system_instruction(self, text: str) -> bool:
        """检查是否是系统指令"""
        # 检查是否以常见系统指令开头
        system_patterns = [
            r'^auto\s+voice:',           # auto voice: [_voice.auto_file!sq]
            r'^auto:',                   # auto: text
            r'^\{[^}]*\}[^}]*\{[^}]*\}', # 复杂格式文本 {color=#fff}text{/color}
        ]
        
        for pattern in system_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _is_code_identifier(self, text: str) -> bool:
        """检查是否是纯代码/标识符"""
        # 检查是否全是大写字母和数字（通常是小工具或标识符）
        if text.isupper() and any(c.isalpha() for c in text) and any(c.isdigit() for c in text):
            # 如果包含字母且没有空格，可能是标识符
            if ' ' not in text and len(text) <= 20:
                return True
        
        # 检查是否是常见的代码模式
        code_patterns = [
            r'^[a-zA-Z_][a-zA-Z0-9_]*[-_][a-zA-Z0-9_]*$',  # identifier_like_this
            r'^[A-Z]{2,}[0-9]+$',                           # CONSTANTS123
            r'^[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+$',           # class.method
        ]
        
        for pattern in code_patterns:
            if re.match(pattern, text):
                return True
        
        # 检查是否包含常见的后缀（通常表示非自然语言文本）
        code_suffixes = ['.py', '.rpy', '.txt', '.json', '.xml']
        for suffix in code_suffixes:
            if text.endswith(suffix):
                return True
        
        return False
    
    def _is_file_path(self, text: str) -> bool:
        """
        判断文本是否像文件路径
        
        Args:
            text: 要检查的文本
            
        Returns:
            True 表示像文件路径
        """
        # 检查是否包含文件扩展名
        for ext in self.FILE_EXTENSIONS:
            if ext in text.lower():
                return True
        
        # 检查是否包含路径分隔符
        if '/' in text or '\\' in text:
            return True
        
        # 检查是否像 RenPy 资源路径
        if text.startswith(('images/', 'audio/', 'game/', 'gui/')):
            return True
        
        return False
    
    def _generate_id(self, file_path: Path, line_num: int, text: str) -> str:
        """
        生成唯一标识符
        
        Args:
            file_path: 文件路径
            line_num: 行号
            text: 文本内容
            
        Returns:
            8位哈希 ID
        """
        # 使用文件路径、行号和文本内容生成 MD5 哈希
        content = f"{file_path.name}_{line_num}_{text[:20]}"
        hash_obj = hashlib.md5(content.encode('utf-8'))
        return f"{file_path.stem}_{line_num}_{hash_obj.hexdigest()[:8]}"
    
    def _classify_text_type(self, line: str, text: str) -> str:
        """
        分类文本类型
        
        Args:
            line: 原始行
            text: 提取的文本
            
        Returns:
            'dialogue' 或 'string'
        """
        stripped_line = line.strip()
        
        # 检查是否像对话（角色名 + 文本）
        dialogue_patterns = [
            r'^[a-zA-Z_][a-zA-Z0-9_]*\s+"',  # character_name "text"
            r'^[a-zA-Z_][a-zA-Z0-9_]*\s+"{',  # character_name "{text"
        ]
        
        for pattern in dialogue_patterns:
            if re.match(pattern, stripped_line):
                return 'dialogue'
        
        # 检查是否是直接对话（只有引号）
        if stripped_line.startswith('"') or stripped_line.endswith('"'):
            return 'dialogue'
        
        # 其他情况默认为字符串
        return 'string'
    
    def _extract_context(self, line: str, text: str) -> Optional[str]:
        """
        提取上下文信息
        
        Args:
            line: 原始行
            text: 提取的文本
            
        Returns:
            上下文字符串或 None
        """
        context_parts = []
        
        # 提取角色名
        character_match = re.match(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)', line)
        if character_match:
            character = character_match.group(1)
            if not character.lower() in ['if', 'else', 'while', 'for', 'with', 'scene', 'show', 'hide']:
                context_parts.append(character)
        
        # 如果是字符串变量，可能有更多信息
        if '=' in line and '"' in line:
            var_match = re.match(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=', line)
            if var_match:
                var_name = var_match.group(1)
                if not var_name.lower() in ['version', 'save_name', 'config', 'gui']:
                    context_parts.append(f"var:{var_name}")
        
        return ' '.join(context_parts) if context_parts else None
    
    def save_to_json(self, output_file: Path = Path("translation_work.json")) -> bool:
        """
        保存提取的文本到 JSON 文件
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            保存是否成功
        """
        try:
            # 确保输出目录存在
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.extracted_texts, f, ensure_ascii=False, indent=2)
            
            print(f"💾 提取结果已保存到: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="RenPy 文本提取器 - 提取 RenPy 游戏中的可翻译文本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python extractor.py                                    # 提取当前目录下的 game/
  python extractor.py -g /path/to/game/dir              # 指定游戏目录
  python extractor.py -o output.json                    # 指定输出文件
  python extractor.py --game-dir /path --output result.json  # 指定目录和输出文件
        """
    )
    
    parser.add_argument(
        '-g', '--game-dir',
        type=str,
        help='游戏目录路径 (默认: 当前目录下的 game/)',
        default=None
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='输出 JSON 文件路径 (默认: translation_work.json)',
        default='translation_work.json'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    args = parser.parse_args()
    
    print("🎮 RenPy 文本提取器 (Extractor)")
    print("=" * 50)
    
    # 解析游戏目录路径
    if args.game_dir:
        game_dir = Path(args.game_dir)
        print(f"🎯 指定游戏目录: {game_dir.absolute()}")
    else:
        game_dir = Path("game")
        print(f"🎯 使用默认目录: {game_dir.absolute()}")
    
    # 解析输出文件路径
    output_file = Path(args.output)
    print(f"💾 输出文件: {output_file.absolute()}")
    print()
    
    # 创建提取器实例
    extractor = RenPyExtractor()
    
    # 提取文本
    extracted_texts = extractor.extract_from_game_directory(game_dir)
    
    if not extracted_texts:
        print("⚠️ 没有找到可翻译的文本")
        return
    
    # 保存到 JSON 文件
    if extractor.save_to_json(output_file):
        # 显示统计信息
        print("\n📊 提取统计:")
        dialogue_count = sum(1 for item in extracted_texts if item['type'] == 'dialogue')
        string_count = sum(1 for item in extracted_texts if item['type'] == 'string')
        
        print(f"   对话文本: {dialogue_count}")
        print(f"   字符串: {string_count}")
        print(f"   总计: {len(extracted_texts)}")
        
        print(f"\n🎯 提取完成！现在可以将 {output_file} 提交给翻译器。")
    else:
        print("❌ 提取失败")


if __name__ == "__main__":
    main()