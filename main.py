#!/usr/bin/env python3
"""
Simple RenPy Translator - Main Entry Point
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# Add the package to Python path
sys.path.insert(0, str(Path(__file__).parent))

from simple_renpy_translator import __version__, __description__
from simple_renpy_translator.project import get_project_manager
from simple_renpy_translator.scanner import get_scanner
from simple_renpy_translator.exporter import HTMLExporter
from simple_renpy_translator.importer import HTMLImporter
from simple_renpy_translator.generator import get_generator
from simple_renpy_translator.utils.logger import get_logger


def create_argument_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog='rt',
        description=__description__,
        epilog='Simple RenPy Translator - Making translation easier'
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version=f'%(prog)s {__version__}'
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # init command
    init_parser = subparsers.add_parser('init', help='Initialize a new translation project')
    init_parser.add_argument('game_path', help='Path to the RenPy game directory')
    init_parser.add_argument('-n', '--name', help='Project name (optional)')
    
    # list command
    list_parser = subparsers.add_parser('list', help='List existing projects')
    
    # scan command
    scan_parser = subparsers.add_parser('scan', help='Scan project for translatable text')
    scan_parser.add_argument('project', help='Project name or path')
    scan_parser.add_argument('-l', '--lang', required=True, help='Target language code (e.g., zh, en, ja)')
    
    # export command
    export_parser = subparsers.add_parser('export', help='Export text for translation')
    export_parser.add_argument('project', help='Project name or path')
    export_parser.add_argument('-l', '--lang', required=True, help='Target language code')
    export_parser.add_argument('-f', '--format', choices=['html', 'json'], default='html', help='Export format')
    export_parser.add_argument('-o', '--output', help='Output file path')
    
    # import command
    import_parser = subparsers.add_parser('import', help='Import translated text')
    import_parser.add_argument('project', help='Project name or path')
    import_parser.add_argument('-l', '--lang', required=True, help='Target language code')
    import_parser.add_argument('-f', '--format', choices=['html'], default='html', help='Import format')
    import_parser.add_argument('file', help='Path to the translation file')
    
    # generate command
    generate_parser = subparsers.add_parser('generate', help='Generate RenPy translation files')
    generate_parser.add_argument('project', help='Project name or path')
    generate_parser.add_argument('-l', '--lang', required=True, help='Target language code')
    
    # status command
    status_parser = subparsers.add_parser('status', help='Show translation status')
    status_parser.add_argument('project', help='Project name or path')
    status_parser.add_argument('-l', '--lang', help='Target language code (optional, shows all if not specified)')
    
    return parser


def main():
    """Main entry point for the application."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    logger = get_logger()
    logger.info(f"Simple RenPy Translator v{__version__}")
    logger.info(f"Command: {args.command}")
    
    try:
        if args.command == 'init':
            return cmd_init(args)
        elif args.command == 'list':
            return cmd_list(args)
        elif args.command == 'scan':
            return cmd_scan(args)
        elif args.command == 'export':
            return cmd_export(args)
        elif args.command == 'import':
            return cmd_import(args)
        elif args.command == 'generate':
            return cmd_generate(args)
        elif args.command == 'status':
            return cmd_status(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


def cmd_init(args):
    """Handle init command."""
    logger = get_logger()
    
    try:
        game_path = Path(args.game_path).resolve()
        if not game_path.exists():
            logger.error(f"Game directory not found: {game_path}")
            return 1
        
        # Create project
        project_manager = get_project_manager()
        project = project_manager.create_project(str(game_path), args.name)
        
        print(f"✅ Project '{project.name}' created successfully!")
        print(f"   Game path: {project.game_path}")
        print(f"   Languages: {', '.join(project.get_available_languages()) if project.get_available_languages() else 'None'}")
        
        return 0
        
    except ValueError as e:
        logger.error(f"Invalid project: {e}")
        return 1
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        return 1


def cmd_list(args):
    """Handle list command."""
    logger = get_logger()
    
    try:
        project_manager = get_project_manager()
        projects = project_manager.list_projects()
        
        if not projects:
            print("No projects found. Create one with 'rt init <game_path>'")
            return 0
        
        print(f"Found {len(projects)} project(s):\n")
        for i, project in enumerate(projects, 1):
            languages = project.get_available_languages()
            print(f"{i}. {project.name}")
            print(f"   Path: {project.game_path}")
            print(f"   Languages: {', '.join(languages) if languages else 'None'}")
            print(f"   Created: {project.created_at.strftime('%Y-%m-%d %H:%M')}")
            print()
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        return 1


def cmd_scan(args):
    """Handle scan command."""
    logger = get_logger()
    logger.info(f"Scan command - Project: {args.project}, Language: {args.lang}")
    
    try:
        # Get project
        project_manager = get_project_manager()
        project = project_manager.get_project(args.project)
        if not project:
            logger.error(f"Project '{args.project}' not found")
            return 1
        
        # Scan project
        scanner = get_scanner()
        results = scanner.scan_project(project, args.lang)
        
        stats = results["statistics"]
        print(f"✅ Scan completed for project '{project.name}'")
        print(f"   Language: {args.lang}")
        print(f"   Total texts: {stats['total']}")
        print(f"   Dialogue: {stats['dialogue']}")
        print(f"   Strings: {stats['string']}")
        print(f"   Files processed: {results['files_processed']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to scan project: {e}")
        return 1


def cmd_export(args):
    """Handle export command."""
    logger = get_logger()
    logger.info(f"Export command - Project: {args.project}, Language: {args.lang}, Format: {args.format}")
    
    try:
        # Get project
        project_manager = get_project_manager()
        project = project_manager.get_project(args.project)
        if not project:
            logger.error(f"Project '{args.project}' not found")
            return 1
        
        # Check if scan exists
        scanner = get_scanner()
        scan_results = scanner.get_scan_results(project, args.lang)
        if not scan_results:
            logger.error(f"No scan results found for language '{args.lang}'. Run 'rt scan' first.")
            return 1
        
        # Determine output file
        output_path = None
        if args.output:
            output_path = Path(args.output)
        
        # Export based on format
        if args.format == 'html':
            exporter = HTMLExporter()
            success = exporter.export_project(project, args.lang, output_path)
            if success:
                print(f"📤 Export completed successfully!")
                return 0
            else:
                print("❌ Export failed!")
                return 1
        else:
            logger.error(f"Unsupported format: {args.format}")
            return 1
        
    except Exception as e:
        logger.error(f"Failed to export project: {e}")
        return 1


def cmd_import(args):
    """Handle import command."""
    logger = get_logger()
    logger.info(f"Import command - Project: {args.project}, Language: {args.lang}, Format: {args.format}")
    
    try:
        # Get project
        project_manager = get_project_manager()
        project = project_manager.get_project(args.project)
        if not project:
            logger.error(f"Project '{args.project}' not found")
            return 1
        
        # Check if scan exists
        scanner = get_scanner()
        scan_results = scanner.get_scan_results(project, args.lang)
        if not scan_results:
            logger.error(f"No scan results found for language '{args.lang}'. Run 'rt scan' first.")
            return 1
        
        # Validate import file
        import_file = Path(args.file)
        
        # Import based on format
        if args.format == 'html':
            importer = HTMLImporter()
            
            # Validate file first
            validation = importer.validate_translation_file(import_file)
            if not validation['valid']:
                logger.error(f"Invalid translation file: {validation['error']}")
                return 1
            
            if validation['translation_count'] == 0:
                logger.warning("No translations found in the file")
                print("⚠️  No translations found in the file")
                return 0
            
            print(f"📋 Found {validation['translation_count']} translations to import")
            
            success = importer.import_project(project, args.lang, import_file)
            if success:
                print("📥 Import completed successfully!")
                return 0
            else:
                print("❌ Import failed!")
                return 1
        else:
            logger.error(f"Unsupported format: {args.format}")
            return 1
        
    except Exception as e:
        logger.error(f"Failed to import translations: {e}")
        return 1


def cmd_generate(args):
    """Handle generate command."""
    logger = get_logger()
    logger.info(f"Generate command - Project: {args.project}, Language: {args.lang}")
    
    try:
        # Get project
        project_manager = get_project_manager()
        project = project_manager.get_project(args.project)
        if not project:
            logger.error(f"Project '{args.project}' not found")
            return 1
        
        # Check if scan exists
        scanner = get_scanner()
        scan_results = scanner.get_scan_results(project, args.lang)
        if not scan_results:
            logger.error(f"No scan results found for language '{args.lang}'. Run 'rt scan' first.")
            return 1
        
        # Generate translation files
        generator = get_generator()
        success = generator.generate_translation_files(project, args.lang)
        
        if success:
            print("🔄 Translation files generated successfully!")
            
            # Validate generated files
            validation = generator.validate_translation_files(project, args.lang)
            if validation['valid']:
                print(f"✅ Generated {validation['files_found']} translation files")
                for file_info in validation['files']:
                    if file_info['valid']:
                        print(f"   - {file_info['file']} ({file_info['translation_count']} translations)")
            else:
                print(f"⚠️  Generated files but validation found issues:")
                for error in validation['errors']:
                    print(f"   - {error}")
            
            return 0
        else:
            print("❌ Failed to generate translation files!")
            return 1
        
    except Exception as e:
        logger.error(f"Failed to generate translation files: {e}")
        return 1


def cmd_status(args):
    """Handle status command."""
    logger = get_logger()
    logger.info(f"Status command - Project: {args.project}")
    
    try:
        # Get project
        project_manager = get_project_manager()
        project = project_manager.get_project(args.project)
        if not project:
            logger.error(f"Project '{args.project}' not found")
            return 1
        
        # Get scanner
        scanner = get_scanner()
        
        # Show status for all languages or specific language
        if args.lang:
            # Show status for specific language
            stats = scanner.get_translation_statistics(project, args.lang)
            print_status_for_language(project.name, args.lang, stats)
        else:
            # Show status for all languages
            languages = project.get_available_languages()
            if not languages:
                print(f"No languages found for project '{project.name}'")
                return 0
            
            print(f"Translation Status for Project: {project.name}\n")
            
            for lang in languages:
                stats = scanner.get_translation_statistics(project, lang)
                print_status_for_language(project.name, lang, stats)
                print()
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to get project status: {e}")
        return 1


def print_status_for_language(project_name: str, language: str, stats: Dict[str, Any]):
    """Print status information for a specific language."""
    total = stats['total']
    translated = stats['translated']
    untranslated = stats['untranslated']
    completion_rate = stats['completion_rate']
    
    print(f"🌐 {language.upper()}:")
    print(f"   Total texts: {total}")
    print(f"   Translated: {translated}")
    print(f"   Untranslated: {untranslated}")
    print(f"   Completion: {completion_rate:.1f}%")
    
    if total > 0:
        # Progress bar
        bar_length = 20
        filled_length = int(bar_length * translated / total)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        print(f"   Progress: |{bar}| {completion_rate:.1f}%")
    
    if stats.get('dialogue_count'):
        print(f"   Dialogue: {stats['dialogue_count']}")
    if stats.get('string_count'):
        print(f"   Strings: {stats['string_count']}")
    if stats.get('files_count'):
        print(f"   Files: {stats['files_count']}")
    
    if stats.get('last_scan'):
        print(f"   Last scan: {stats['last_scan'][:19]}")  # Remove microseconds


if __name__ == '__main__':
    sys.exit(main())