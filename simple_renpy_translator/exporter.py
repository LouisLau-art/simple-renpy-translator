"""
HTML Export functionality for Simple RenPy Translator
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import html

from .parser import TextBlock
from .project import Project
from .scanner import get_scanner
from .utils.file_utils import write_text_file, ensure_directory
from .utils.logger import get_logger


class HTMLExporter:
    """Exports translatable text to HTML format."""
    
    def __init__(self):
        """Initialize HTML exporter."""
        self.logger = get_logger()
    
    def export_project(self, project: Project, language: str, output_file: Optional[Path] = None) -> bool:
        """
        Export project text to HTML file.
        
        Args:
            project: The RenPy project to export
            language: Target language code
            output_file: Output file path (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get scan results
        scanner = get_scanner()
        scan_results = scanner.get_scan_results(project, language)
        if not scan_results:
            self.logger.error(f"No scan results found for project '{project.name}' and language '{language}'")
            return False
        
        # Convert text blocks back to objects for processing
        text_blocks = [TextBlock.from_dict(block_data) for block_data in scan_results["text_blocks"]]
        
        # Generate HTML content
        html_content = self._generate_html_content(text_blocks, project, language, scan_results)
        
        # Determine output file
        if output_file is None:
            output_file = project.project_dir / f"export_{language}.html"
        
        # Ensure output directory exists
        ensure_directory(output_file.parent)
        
        # Write HTML file
        success = write_text_file(output_file, html_content)
        if success:
            self.logger.info(f"Exported HTML file: {output_file}")
            print(f"✅ Exported to: {output_file}")
            print(f"   Text blocks: {len(text_blocks)}")
            print(f"   Language: {language}")
            print(f"   Project: {project.name}")
        else:
            self.logger.error(f"Failed to write HTML file: {output_file}")
        
        return success
    
    def _generate_html_content(self, text_blocks: List[TextBlock], project: Project, 
                              language: str, scan_results: Dict[str, Any]) -> str:
        """Generate HTML content for export."""
        
        # Build HTML
        html_parts = []
        
        # HTML header
        html_parts.append(self._get_html_header(project, language, scan_results))
        
        # HTML body
        html_parts.append("<body>")
        
        # Project info header
        html_parts.append(self._get_project_info_header(project, language, scan_results))
        
        # Table header
        html_parts.append("<table class='translation-table'>")
        html_parts.append("<thead>")
        html_parts.append("<tr>")
        html_parts.append("<th>#</th>")
        html_parts.append("<th>Type</th>")
        html_parts.append("<th>Original Text</th>")
        html_parts.append("<th>Translation</th>")
        html_parts.append("<th>Speaker</th>")
        html_parts.append("<th>File</th>")
        html_parts.append("<th>Line</th>")
        html_parts.append("<th>Status</th>")
        html_parts.append("</tr>")
        html_parts.append("</thead>")
        html_parts.append("<tbody>")
        
        # Add text blocks
        for i, text_block in enumerate(text_blocks, 1):
            html_parts.append(self._generate_table_row(text_block, i))
        
        html_parts.append("</tbody>")
        html_parts.append("</table>")
        
        # Footer
        html_parts.append(self._get_html_footer())
        
        return "\n".join(html_parts)
    
    def _get_html_header(self, project: Project, language: str, scan_results: Dict[str, Any]) -> str:
        """Generate HTML header."""
        export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Translation Export - {project.name} ({language})</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .project-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }}
        .info-item {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            border-left: 4px solid #007bff;
        }}
        .translation-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .translation-table th {{
            background: #007bff;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }}
        .translation-table td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
            vertical-align: top;
        }}
        .translation-table tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        .translation-table tr:hover {{
            background: #e3f2fd;
        }}
        .text-cell {{
            max-width: 300px;
            word-wrap: break-word;
        }}
        .translation-cell {{
            min-width: 200px;
            border: 2px dashed #ccc;
            background: #fafafa;
            min-height: 60px;
        }}
        .type-badge {{
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .type-dialogue {{
            background: #e3f2fd;
            color: #1976d2;
        }}
        .type-string {{
            background: #f3e5f5;
            color: #7b1fa2;
        }}
        .status-pending {{
            background: #fff3cd;
            color: #856404;
        }}
        .file-info {{
            font-family: monospace;
            font-size: 0.9em;
            color: #666;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        .highlight {{
            background: yellow;
            font-weight: bold;
        }}
    </style>
</head>"""
    
    def _get_project_info_header(self, project: Project, language: str, scan_results: Dict[str, Any]) -> str:
        """Generate project info header."""
        stats = scan_results.get("statistics", {})
        export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""<div class="header">
        <h1>Translation Export</h1>
        <h2>{project.name} - {language.upper()}</h2>
        
        <div class="project-info">
            <div class="info-item">
                <strong>Project Name:</strong><br>
                {project.name}
            </div>
            <div class="info-item">
                <strong>Language:</strong><br>
                {language.upper()}
            </div>
            <div class="info-item">
                <strong>Game Path:</strong><br>
                {project.game_path}
            </div>
            <div class="info-item">
                <strong>Total Texts:</strong><br>
                {stats.get('total', 0)}
            </div>
            <div class="info-item">
                <strong>Dialogue:</strong><br>
                {stats.get('dialogue', 0)}
            </div>
            <div class="info-item">
                <strong>Strings:</strong><br>
                {stats.get('string', 0)}
            </div>
            <div class="info-item">
                <strong>Export Time:</strong><br>
                {export_time}
            </div>
            <div class="info-item">
                <strong>Files Processed:</strong><br>
                {scan_results.get('files_processed', 0)}
            </div>
        </div>
        
        <p><strong>Instructions:</strong> Fill in the Translation column with your translations. 
        Leave unchanged for texts that don't need translation.</p>
    </div>"""
    
    def _generate_table_row(self, text_block: TextBlock, index: int) -> str:
        """Generate HTML table row for a text block."""
        
        # Escape HTML characters
        original_text = html.escape(text_block.original_text)
        translation_placeholder = f"<em>Fill in translation for '{original_text[:30]}{'...' if len(original_text) > 30 else ''}</em>"
        
        # File info
        file_info = str(text_block.file_path.relative_to(text_block.file_path.parent.parent))
        
        # Status
        status = "Pending" if not text_block.is_translated else "Translated"
        status_class = "status-pending"
        
        return f"""<tr>
        <td>{index}</td>
        <td><span class="type-badge type-{text_block.text_type}">{text_block.text_type.upper()}</span></td>
        <td class="text-cell">{original_text}</td>
        <td class="translation-cell">{translation_placeholder}</td>
        <td>{text_block.character or '-'}</td>
        <td class="file-info">{file_info}</td>
        <td>{text_block.line_number}</td>
        <td><span class="{status_class}">{status}</span></td>
    </tr>"""
    
    def _get_html_footer(self) -> str:
        """Generate HTML footer."""
        export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
    <div class="footer">
        <p>Generated by Simple RenPy Translator on {export_time}</p>
        <p>Import this file back using: rt import [project] -l [language] -f html [filename]</p>
    </div>
    
    </body>
    </html>"""