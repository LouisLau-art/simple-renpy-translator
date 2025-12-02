# Simple RenPy Translator

A lightweight and easy-to-use command line tool for translating RenPy games.

## Features

- **Simple**: Minimal dependencies, easy installation
- **Fast**: Quick text extraction and translation processing
- **Compatible**: Works with Python 3.13+ and all major platforms
- **Flexible**: Support for HTML and JSON export/import formats
- **Command Line**: Full command line interface with subcommands

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Using the Command Line Tool

1. Initialize a new translation project:
   ```bash
   python main.py init /path/to/renpy/game
   ```

2. Scan for translatable text:
   ```bash
   python main.py scan my_project -l zh
   ```

3. Export text for translation (HTML format):
   ```bash
   python main.py export my_project -l zh -f html
   ```

4. Import translated text (HTML format):
   ```bash
   python main.py import my_project -l zh -f html translation.html
   ```

5. Generate RenPy translation files:
   ```bash
   python main.py generate my_project -l zh
   ```

### Using JSON Format (Alternative Workflow)

1. Extract original text to JSON:
   ```bash
   python extractor.py
   ```

2. After translation, inject translations back:
   ```bash
   python injector.py -i translated.json
   ```

## Available Commands

- `init` - Initialize a new translation project
- `list` - List existing projects  
- `scan` - Scan project for translatable text
- `export` - Export text for translation
- `import` - Import translated text
- `generate` - Generate RenPy translation files
- `status` - Show translation status

## Requirements

- Python 3.13+
- See requirements.txt for additional dependencies

## License

MIT License