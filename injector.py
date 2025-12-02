#!/usr/bin/env python3
"""
RenPy 翻译文件注入器 (Injector)
读取 translation_work.json，将翻译内容注入到 RenPy 标准翻译文件中
"""

import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys


class RenPyInjector:
    """RenPy 翻译文件注入器"""
    
    def __init__(self):
        """初始化注入器"""
        self.translations: List[Dict[str, Any]] = []
        self.translations_by_file: Dict[str, List[Dict[str, Any]]] = {}
    
    def load_translation_data(self, json_file: Path = Path("translation_work.json")) -> bool:
        """
        加载翻译数据
        
        Args:
            json_file: 包含翻译数据的 JSON 文件
            
        Returns:
            加载是否成功
        """
        print(f"📂 加载翻译数据: {json_file}")
        
        if not json_file.exists():
            print(f"❌ 错误: 找不到翻译数据文件 {json_file}")
            return False
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            
            if not self.translations:
                print(f"⚠️ 警告: 翻译数据文件为空")
                return False
            
            print(f"✅ 成功加载 {len(self.translations)} 个翻译条目")
            
            # 按文件分组
            self._group_by_file()
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            return False
    
    def _group_by_file(self) -> None:
        """将翻译数据按文件分组"""
        self.translations_by_file.clear()
        
        for translation in self.translations:
            # 提取文件路径（移除 game/ 前缀）
            file_path = translation.get('file', '')
            
            # 按文件分组
            if file_path not in self.translations_by_file:
                self.translations_by_file[file_path] = []
            
            self.translations_by_file[file_path].append(translation)
    
    def inject_translations(self, language: str = "schinese", game_dir: Path = Path("game")) -> bool:
        """
        注入翻译文件
        
        Args:
            language: 目标语言（默认为中文简体）
            game_dir: game 目录路径
            
        Returns:
            注入是否成功
        """
        print(f"🚀 开始注入翻译文件 (语言: {language})")
        
        # 过滤掉没有翻译的条目
        translated_entries = [t for t in self.translations if t.get('translated') and t['translated'].strip()]
        
        if not translated_entries:
            print(f"⚠️ 警告: 没有找到已翻译的内容")
            return False
        
        print(f"📝 找到 {len(translated_entries)} 个已翻译的条目")
        
        # 生成翻译目录
        tl_dir = game_dir / "tl" / language
        tl_dir.mkdir(parents=True, exist_ok=True)
        
        # 统计信息
        generated_files = 0
        total_translations = 0
        
        # 按原文件路径生成翻译文件
        for source_file, file_translations in self.translations_by_file.items():
            # 只处理有翻译的条目
            translated_file_entries = [t for t in file_translations if t.get('translated') and t['translated'].strip()]
            
            if not translated_file_entries:
                continue
            
            # 生成翻译文件路径
            if source_file.startswith("game/"):
                # 移除 game/ 前缀，保持相对路径
                relative_path = source_file[5:]
            else:
                relative_path = source_file
            
            # 创建翻译文件
            translation_file_path = tl_dir / relative_path
            
            if self._generate_translation_file(translation_file_path, translated_file_entries, language):
                generated_files += 1
                total_translations += len(translated_file_entries)
        
        if generated_files > 0:
            print(f"✅ 注入完成！")
            print(f"   📁 生成翻译文件: {generated_files}")
            print(f"   📝 翻译条目: {total_translations}")
            print(f"   📂 输出目录: {tl_dir}")
            return True
        else:
            print(f"❌ 没有生成任何翻译文件")
            return False
    
    def _generate_translation_file(self, file_path: Path, translations: List[Dict[str, Any]], language: str) -> bool:
        """
        生成单个翻译文件
        
        Args:
            file_path: 翻译文件路径
            translations: 该文件的翻译条目
            language: 目标语言
            
        Returns:
            生成是否成功
        """
        try:
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 生成文件内容
            content = self._generate_file_content(translations, language)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 生成翻译文件: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ 生成翻译文件失败 {file_path}: {e}")
            return False
    
    def _generate_file_content(self, translations: List[Dict[str, Any]], language: str) -> str:
        """
        生成翻译文件内容
        
        Args:
            translations: 翻译条目列表
            language: 目标语言
            
        Returns:
            文件内容字符串
        """
        lines = []
        
        # 添加文件头部注释
        lines.append("# RenPy 翻译文件 - Simple RenPy Translator")
        lines.append(f"# 语言: {language}")
        lines.append(f"# 生成时间: {self._get_current_time()}")
        lines.append("")
        
        # 按原文文件位置排序
        translations = sorted(translations, key=lambda x: x.get('line', 0))
        
        # 生成翻译块
        for i, translation in enumerate(translations):
            # 添加原文位置注释
            original_file = translation.get('file', 'unknown')
            original_line = translation.get('line', 0)
            lines.append(f"# {original_file}:{original_line}")
            
            # 生成翻译块
            translation_id = translation.get('id', 'unknown')
            translated_text = translation.get('translated', '')
            
            # 添加翻译块
            lines.append(f"translate {language} {translation_id}:")
            
            # 处理特殊字符
            escaped_text = self._escape_renpy_text(translated_text)
            lines.append(f'    {escaped_text}')
            lines.append("")
        
        return "\n".join(lines)
    
    def _escape_renpy_text(self, text: str) -> str:
        """
        为 RenPy 转义文本
        
        Args:
            text: 原始文本
            
        Returns:
            转义后的文本
        """
        # 转义换行符
        text = text.replace('\n', '\\n')
        
        # 处理引号
        if '"' in text and "'" not in text:
            # 如果包含双引号但不包含单引号，使用单引号包围
            return f"'{text}'"
        else:
            # 使用双引号包围，并转义内部的双引号
            text = text.replace('"', '\\"')
            return f'"{text}"'
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def validate_injection(self, game_dir: Path = Path("game"), language: str = "schinese") -> Dict[str, Any]:
        """
        验证注入结果
        
        Args:
            game_dir: game 目录路径
            language: 目标语言
            
        Returns:
            验证结果统计
        """
        print(f"🔍 验证翻译文件注入结果")
        
        tl_dir = game_dir / "tl" / language
        result = {
            "valid": True,
            "files_found": 0,
            "translation_count": 0,
            "errors": []
        }
        
        if not tl_dir.exists():
            result["valid"] = False
            result["errors"].append(f"翻译目录不存在: {tl_dir}")
            return result
        
        # 查找所有翻译文件
        translation_files = list(tl_dir.rglob("*.rpy"))
        result["files_found"] = len(translation_files)
        
        for file_path in translation_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 统计翻译条目
                translation_blocks = re.findall(r'translate\s+\w+\s+\w+:', content)
                result["translation_count"] += len(translation_blocks)
                
            except Exception as e:
                result["valid"] = False
                result["errors"].append(f"读取文件失败 {file_path}: {e}")
        
        print(f"✅ 验证完成:")
        print(f"   📁 翻译文件: {result['files_found']}")
        print(f"   📝 翻译条目: {result['translation_count']}")
        if result["errors"]:
            print(f"   ⚠️ 错误: {len(result['errors'])}")
            for error in result["errors"]:
                print(f"     - {error}")
        
        return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="RenPy 翻译文件注入器 - 将翻译后的 JSON 数据注入到 RenPy 翻译文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python injector.py                                    # 使用默认的 translation_work.json
  python injector.py -i input.json                     # 指定输入 JSON 文件
  python injector.py -g /path/to/game/dir              # 指定游戏目录
  python injector.py -l japanese                       # 指定目标语言为日语
  python injector.py --input data.json --game-dir /path --lang french
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        type=str,
        help='输入 JSON 文件路径 (默认: translation_work.json)',
        default='translation_work.json'
    )
    
    parser.add_argument(
        '-g', '--game-dir',
        type=str,
        help='游戏目录路径 (默认: 当前目录下的 game/)',
        default=None
    )
    
    parser.add_argument(
        '-l', '--language',
        type=str,
        help='目标语言代码 (默认: schinese)',
        default='schinese'
    )
    
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='跳过验证步骤'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    args = parser.parse_args()
    
    print("🎮 RenPy 翻译文件注入器 (Injector)")
    print("=" * 50)
    
    # 解析输入文件路径
    input_file = Path(args.input)
    print(f"📂 输入文件: {input_file.absolute()}")
    
    # 解析游戏目录路径
    if args.game_dir:
        game_dir = Path(args.game_dir)
        print(f"🎯 指定游戏目录: {game_dir.absolute()}")
    else:
        game_dir = Path("game")
        print(f"🎯 使用默认目录: {game_dir.absolute()}")
    
    print(f"🌍 目标语言: {args.language}")
    print()
    
    # 创建注入器实例
    injector = RenPyInjector()
    
    # 加载翻译数据
    if not injector.load_translation_data(input_file):
        return
    
    # 注入翻译文件
    if injector.inject_translations(args.language, game_dir):
        print("\n🎉 翻译文件生成成功！")
        print("💡 提示: 现在可以启动 RenPy 项目查看翻译效果。")
        
        # 验证结果（可选）
        if not args.no_validate:
            print("\n" + "=" * 30)
            injector.validate_injection(game_dir, args.language)
    else:
        print("❌ 注入失败")


if __name__ == "__main__":
    main()