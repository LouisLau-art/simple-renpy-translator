#!/usr/bin/env python3
"""
RenPy 工具：单文件翻译提取与注入工具
支持 extract 和 inject 两个子命令
"""

import hashlib
import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys
import shutil
from datetime import datetime
import os

# ======================
# 内联工具函数
# ======================

def ensure_directory(path: Path) -> None:
    """确保目录存在，不存在则创建"""
    path.mkdir(parents=True, exist_ok=True)

def read_text_file(file_path: Path) -> Optional[str]:
    """带编码检测的文本文件读取"""
    encodings = ['utf-8', 'gbk', 'shift-jis', 'cp1252']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception:
            continue
    return None

def write_text_file(file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
    """写入文本文件"""
    try:
        ensure_directory(file_path.parent)
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False

def save_json_file(file_path: Path, data: Dict[str, Any]) -> bool:
    """保存JSON文件"""
    try:
        content = json.dumps(data, indent=2, ensure_ascii=False)
        return write_text_file(file_path, content)
    except Exception:
        return False

# ======================
# RenPyExtractor 类
# ======================

class RenPyExtractor:
    """RenPy 文本提取器（带源文件ID注入）"""
    
    IGNORE_PATTERNS = [
        re.compile(r'^\s*label\s+', re.MULTILINE),
        re.compile(r'^\s*jump\s+', re.MULTILINE),
        re.compile(r'^\s*call\s+', re.MULTILINE),
        re.compile(r'^\s*scene\s+', re.MULTILINE),
        re.compile(r'^\s*show\s+', re.MULTILINE),
        re.compile(r'^\s*hide\s+', re.MULTILINE),
        re.compile(r'^\s*play\s+', re.MULTILINE),
        re.compile(r'^\s*stop\s+', re.MULTILINE),
        re.compile(r'^\s*with\s+', re.MULTILINE),
        re.compile(r'^\s*init\s*:', re.MULTILINE),
        re.compile(r'^\s*python\s*:', re.MULTILINE),
        re.compile(r'^\s*#.*$', re.MULTILINE),
        re.compile(r'^\s*$', re.MULTILINE),
    ]
    
    DIRECTORY_BLACKLIST = ['tl', 'renpy', 'cache', 'saved']
    FILE_PREFIX_BLACKLIST = ['00', 'gui.', 'gui_']
    
    def __init__(self):
        self.extracted_texts: List[Dict[str, Any]] = []
        self.game_dir = None
    
    def should_skip_file(self, file_path: Path, game_dir: Path) -> bool:
        """检查是否跳过文件"""
        for prefix in self.FILE_PREFIX_BLACKLIST:
            if file_path.name.startswith(prefix):
                return True
        
        # 使用 os.walk 兼容的方法计算相对路径
        try:
            relative_path = file_path.relative_to(game_dir)
            for part in relative_path.parts:
                if part in self.DIRECTORY_BLACKLIST:
                    return True
    except ValueError:
        return True
    
    return False
    
    def extract_from_game_directory(self, game_dir: Path = Path("game")) -> List[Dict[str, Any]]:
        """从game目录提取文本并注入ID"""
        self.game_dir = game_dir
        if not game_dir.exists():
            print(f"❌ 错误: 找不到 game 目录: {game_dir}")
            return []
        
        extracted_texts = []
        
        # 使用 os.walk 进行遍历，确保正确的相对路径计算
        for root, dirs, files in os.walk(str(game_dir)):
            # 在遍历时跳过黑名单目录
            dirs[:] = [d for d in dirs if d not in self.DIRECTORY_BLACKLIST]
            dirs[:] = [d for d in dirs if not d.startswith('_') and not d.startswith('.')]
            
            for file in files:
                if not file.endswith('.rpy'):
                    continue
                
                file_path = Path(root) / file
                if self.should_skip_file(file_path, game_dir):
                    continue
                
                content = read_text_file(file_path)
                if not content:
                    continue
                
                lines = content.splitlines(keepends=True)
                modified_lines = lines.copy()
                modified = False
                
                for line_num, line in enumerate(lines, 1):
                    if self._should_ignore_line(line):
                        continue
                    
                    # 提取引号内文本
                    pattern = r'"([^"]*)"'
                    for match in re.finditer(pattern, line):
                        text = match.group(1).strip()
                        if self._is_translatable_text(text):
                            text_id = self._generate_id(file_path, line_num, text)
                            
                            # 检查并注入ID
                            if not self._has_id(line):
                                new_line = self._add_id_to_line(line, text_id)
                                if new_line != line:
                                    modified_lines[line_num-1] = new_line
                                modified = True
                            
                            # 计算正确的相对路径
                            relative_path = file_path.relative_to(game_dir).as_posix()
                            
                            # 创建文本条目
                            text_entry = {
                                "id": text_id,
                                "file": relative_path,
                                "line": line_num,
                                "original": text,
                                "translated": None
                            }
                            extracted_texts.append(text_entry)
                
                # 如果有修改，写回文件
                if modified:
                    write_text_file(file_path, ''.join(modified_lines))
        
        self.extracted_texts = extracted_texts
        print(f"✅ 提取完成，共找到 {len(self.extracted_texts)} 个可翻译文本")
        return self.extracted_texts
    
    def _extract_from_file(self, file_path: Path) -> None:
        """从单个文件提取文本并注入ID"""
        content = read_text_file(file_path)
        if not content:
            return
        
        lines = content.splitlines(keepends=True)
        modified_lines = lines.copy()
        modified = False
        
        for line_num, line in enumerate(lines, 1):
            if self._should_ignore_line(line):
                continue
            
            # 提取引号内文本
            pattern = r'"([^"]*)"'
            for match in re.finditer(pattern, line):
                text = match.group(1).strip()
                if self._is_translatable_text(text):
                    text_id = self._generate_id(file_path, line_num, text)
                    
                    # 检查并注入ID
                    if not self._has_id(line):
                        new_line = self._add_id_to_line(line, text_id)
                        if new_line != line:
                            modified_lines[line_num-1] = new_line
                        modified = True
                
                # 创建文本条目
                text_entry = {
                    "id": text_id,
                    "file": str(file_path.relative_to(self.game_dir)),
                    "line": line_num,
                    "original": text,
                    "translated": None
                }
                self.extracted_texts.append(text_entry)
        
        # 如果有修改，写回文件
        if modified:
            write_text_file(file_path, ''.join(modified_lines))
    
    def _should_ignore_line(self, line: str) -> bool:
        """检查是否忽略该行"""
        stripped_line = line.strip()
        for pattern in self.IGNORE_PATTERNS:
            if pattern.match(line):
                return True
        return False
    
    def _is_translatable_text(self, text: str) -> bool:
        """判断文本是否需要翻译"""
        cleaned_text = text.strip().strip('"\'')
        if len(cleaned_text) < 2:
            return False
        
        # 任务要求的过滤规则
        if '_' in cleaned_text:
            return False
        if '-' in cleaned_text and ' ' not in cleaned_text:
            return False
        if cleaned_text.isdigit() or (len(cleaned_text) > 2 and cleaned_text[0] == '0' and cleaned_text[1:].isdigit()):
            return False
        
        # 基本过滤
        if cleaned_text.startswith(('$', '{', '[')) or '{' in cleaned_text:
            return False
        if len(cleaned_text.split()) == 1 and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', cleaned_text):
            return False
        if not any(c.isalpha() for c in cleaned_text):
            return False
        
        return True
    
    def _generate_id(self, file_path: Path, line_num: int, text: str) -> str:
        """生成唯一ID"""
        content = f"{file_path.name}_{line_num}_{text[:20]}"
        return f"{file_path.stem}_{line_num}_{hashlib.md5(content.encode('utf-8')).hexdigest()[:8]}"
    
    def _has_id(self, line: str) -> bool:
        """检查行是否已有ID"""
        return 'id ' in line
    
    def _add_id_to_line(self, line: str, text_id: str) -> str:
        """为行添加ID"""
        stripped_line = line.rstrip()
        if re.search(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s+"', stripped_line):
            # 对话行
            return stripped_line + f' id {text_id}\n'
        elif re.search(r'^\s*show\s+', stripped_line):
            # show语句
            return stripped_line + f' id {text_id}\n'
        else:
            # 其他情况
            return stripped_line + f' # id {text_id}\n'

# ======================
# RenPyInjector 类
# ======================

class RenPyInjector:
    """RenPy 翻译注入器"""
    
    def __init__(self):
        self.translations: List[Dict[str, Any]] = []
        self.translations_by_file: Dict[str, List[Dict[str, Any]]] = {}
    
    def load_translation_data(self, json_file: Path) -> bool:
        """加载翻译数据"""
        if not json_file.exists():
            print(f"❌ 错误: 找不到翻译数据文件 {json_file}")
            return False
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            self._group_by_file()
            return True
        except Exception:
            return False
    
    def _group_by_file(self) -> None:
        """按文件分组翻译数据"""
        self.translations_by_file.clear()
        for translation in self.translations:
            file_path = translation.get('file', '')
            if file_path not in self.translations_by_file:
                self.translations_by_file[file_path] = []
            self.translations_by_file[file_path].append(translation)
    
    def inject_translations(self, language: str, game_dir: Path) -> bool:
        """注入翻译文件"""
        tl_dir = game_dir / "tl" / language
        tl_dir.mkdir(parents=True, exist_ok=True)
        
        # 确保不处理 tl 目录本身
        if str(tl_dir) in str(game_dir):
            print("❌ 错误: 不能在 tl 目录中操作")
            return False
        
        translated_entries = [t for t in self.translations
                            if t.get('translated') and t['translated'].strip()]
        
        if not translated_entries:
            print("⚠️ 警告: 没有找到已翻译的内容")
            return False
        
        generated_files = 0
        
        # 按文件分组翻译数据
        translations_by_file = {}
        for translation in translated_entries:
            file_path = translation.get('file', '')
            if file_path not in translations_by_file:
                translations_by_file[file_path] = []
            translations_by_file[file_path].append(translation)
        
        for source_file, file_translations in translations_by_file.items():
            if not file_translations:
                continue
            
            # 计算正确的目标路径 - 镜像原始目录结构
            # 确保 source_file 是相对于 game_dir 的路径
            source_file_path = Path(source_file)
            # 创建目标路径
            translation_file_path = tl_dir / source_file_path
            
            if self._generate_translation_file(translation_file_path, file_translations, language):
                generated_files += 1
        
        print(f"✅ 注入完成！生成 {generated_files} 个翻译文件")
        return generated_files > 0
    
    def _generate_translation_file(self, file_path: Path, translations: List[Dict[str, Any]], language: str) -> bool:
        """生成单个翻译文件"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            content = self._generate_file_content(translations, language)
            return write_text_file(file_path, content)
        except Exception:
            return False
    
    def _generate_file_content(self, translations: List[Dict[str, Any]], language: str) -> str:
        """生成翻译文件内容"""
        lines = [
            "# RenPy 翻译文件 - Simple RenPy Translator",
            f"# 语言: {language}",
            f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        for translation in sorted(translations, key=lambda x: x.get('line', 0)):
            original_file = translation.get('file', 'unknown')
            original_line = translation.get('line', 0)
            translation_id = translation.get('id', 'unknown')
            translated_text = translation.get('translated', '')
            
            lines.append(f"# {original_file}:{original_line}")
            lines.append(f"translate {language} {translation_id}:")
            lines.append(f'    "{translated_text}"')
            lines.append("")
        
        return "\n".join(lines)

# ======================
# 主函数
# ======================

def main():
    """主命令行入口"""
    parser = argparse.ArgumentParser(description="RenPy 工具：单文件翻译提取与注入")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # extract 命令
    extract_parser = subparsers.add_parser("extract", help="提取可翻译文本")
    extract_parser.add_argument("-g", "--game-dir", type=str, help="游戏目录", default="game")
    extract_parser.add_argument("-o", "--output", type=str, help="输出JSON文件", default="translation_work.json")
    
    # inject 命令
    inject_parser = subparsers.add_parser("inject", help="注入翻译文件")
    inject_parser.add_argument("-i", "--input", type=str, help="输入JSON文件", default="translation_work.json")
    inject_parser.add_argument("-g", "--game-dir", type=str, help="游戏目录", default="game")
    inject_parser.add_argument("-l", "--language", type=str, help="目标语言", default="schinese")
    
    args = parser.parse_args()
    
    if args.command == "extract":
        game_dir = Path(args.game_dir).resolve()
        extractor = RenPyExtractor()
        extracted = extractor.extract_from_game_directory(game_dir)
        if extracted and save_json_file(Path(args.output), extracted):
            print(f"💾 提取结果已保存至: {args.output}")
    
    elif args.command == "inject":
        game_dir = Path(args.game_dir).resolve()
        injector = RenPyInjector()
        if injector.load_translation_data(Path(args.input)):
            injector.inject_translations(args.language, game_dir)
        else:
            print("❌ 无法加载翻译数据")

if __name__ == "__main__":
    main()