
"""
File Organizer Script
Organizes files in a directory by their extensions into categorized subfolders.
"""

import os
import shutil
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys


class FileOrganizer:
    """Main class for organizing files."""
    
    # Default categorization rules (RUSSIAN NAMES)
    DEFAULT_CATEGORIES = {
     '🖼️ Изображения': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.tiff', '.webp'],
    '📄 Документы': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx', '.csv', '.md', '.epub'],
    '📦 Архивы': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.tgz'],
    '🎵 Музыка': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
    '🎬 Видео': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
    '💻 Программы': ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.app', '.jar'],
    '👨‍💻 Код': ['.py', '.js', '.html', '.css', '.cpp', '.c', '.java', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.ts', '.jsx', '.tsx', '.json', '.xml'],
    '🔤 Шрифты': ['.ttf', '.otf', '.woff', '.woff2', '.eot'],
    '🗄️ Базы данных': ['.db', '.sqlite', '.sql', '.mdb', '.accdb'],
    '💾 Резервные копии': ['.bak', '.old', '.tmp', '.temp'],
    '📊 Таблицы': ['.xls', '.xlsx', '.ods'],
    '📽️ Презентации': ['.ppt', '.pptx', '.odp'],
    '📁 Прочее': []
    }
    
    def __init__(self, target_dir: str, config_file: Optional[str] = None, 
                 dry_run: bool = False, log_file: Optional[str] = None):
        """
        Initialize the FileOrganizer.
        
        Args:
            target_dir: Directory to organize
            config_file: Path to JSON config file (optional)
            dry_run: If True, only simulate operations
            log_file: Path to log file (optional)
        """
        self.target_dir = Path(target_dir).resolve()
        self.dry_run = dry_run
        self.categories = self._load_categories(config_file)
        self.moved_files = []
        self.errors = []
        
        # Setup logging
        self._setup_logging(log_file)
        
    def _load_categories(self, config_file: Optional[str]) -> Dict[str, List[str]]:
        """Load categories from config file or use defaults."""
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    categories = config.get('categories', self.DEFAULT_CATEGORIES)
                    logging.info(f"Loaded custom categories from {config_file}")
                    return categories
            except Exception as e:
                logging.warning(f"Could not load config file: {e}. Using defaults.")
                return self.DEFAULT_CATEGORIES
        return self.DEFAULT_CATEGORIES
    
    def _setup_logging(self, log_file: Optional[str] = None):
        """Setup logging configuration."""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # Create logger
        self.logger = logging.getLogger('FileOrganizer')
        self.logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            try:
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setFormatter(logging.Formatter(log_format, date_format))
                self.logger.addHandler(file_handler)
                self.logger.info(f"Logging to file: {log_file}")
            except Exception as e:
                self.logger.warning(f"Could not create log file: {e}")
    
    def get_category_for_file(self, file_path: Path) -> str:
        """
        Determine the category for a file based on its extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Category name
        """
        extension = file_path.suffix.lower()
        
        for category, extensions in self.categories.items():
            if extension in extensions:
                return category
        
        # Check for files without extension
        if not extension:
            # Check if filename has no extension
            if '.' not in file_path.name:
                return 'Miscellaneous'
        
        return 'Others'
    
    def organize(self) -> Dict[str, any]:
        """
        Organize files in the target directory.
        
        Returns:
            Dictionary with statistics about the operation
        """
        if not self.target_dir.exists():
            self.logger.error(f"Directory does not exist: {self.target_dir}")
            return {'success': False, 'error': 'Directory does not exist'}
        
        if not self.target_dir.is_dir():
            self.logger.error(f"Path is not a directory: {self.target_dir}")
            return {'success': False, 'error': 'Path is not a directory'}
        
        self.logger.info(f"Starting organization of: {self.target_dir}")
        self.logger.info(f"Mode: {'DRY RUN (simulation)' if self.dry_run else 'ACTUAL'}")
        
        # Get all files in the directory (excluding directories)
        files = [f for f in self.target_dir.iterdir() if f.is_file()]
        
        if not files:
            self.logger.info("No files found to organize.")
            return {
                'success': True,
                'files_moved': 0,
                'categories': {},
                'dry_run': self.dry_run
            }
        
        self.logger.info(f"Found {len(files)} files to organize")
        
        # Group files by category
        files_by_category = {}
        for file_path in files:
            category = self.get_category_for_file(file_path)
            if category not in files_by_category:
                files_by_category[category] = []
            files_by_category[category].append(file_path)
        
        # Create category directories and move files
        stats = {'files_moved': 0, 'categories': {}, 'errors': []}
        
        for category, file_list in files_by_category.items():
            # Skip empty lists
            if not file_list:
                continue
                
            # Create category directory
            category_dir = self.target_dir / category
            if not self.dry_run:
                try:
                    category_dir.mkdir(exist_ok=True)
                    self.logger.debug(f"Created/verified directory: {category_dir}")
                except Exception as e:
                    self.logger.error(f"Failed to create directory {category_dir}: {e}")
                    stats['errors'].append(f"Failed to create directory {category_dir}: {e}")
                    continue
            
            # Move each file
            for file_path in file_list:
                try:
                    # Handle duplicate filenames
                    destination = category_dir / file_path.name
                    counter = 1
                    original_name = file_path.stem
                    extension = file_path.suffix
                    
                    while destination.exists():
                        new_name = f"{original_name}_{counter}{extension}"
                        destination = category_dir / new_name
                        counter += 1
                    
                    if self.dry_run:
                        self.logger.info(f"[DRY RUN] Would move: {file_path.name} -> {category}/")
                        stats['files_moved'] += 1
                    else:
                        shutil.move(str(file_path), str(destination))
                        self.logger.info(f"Moved: {file_path.name} -> {category}/")
                        stats['files_moved'] += 1
                        self.moved_files.append((file_path.name, category, str(destination)))
                        
                except Exception as e:
                    error_msg = f"Failed to move {file_path.name}: {e}"
                    self.logger.error(error_msg)
                    stats['errors'].append(error_msg)
                    self.errors.append(error_msg)
            
            # Update category stats
            stats['categories'][category] = len(file_list)
        
        # Log summary
        self.logger.info("=" * 50)
        self.logger.info("ORGANIZATION SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Files processed: {stats['files_moved']}")
        for category, count in stats['categories'].items():
            self.logger.info(f"  {category}: {count} files")
        if stats['errors']:
            self.logger.warning(f"Errors encountered: {len(stats['errors'])}")
        if self.dry_run:
            self.logger.info("DRY RUN COMPLETED - No files were actually moved")
        else:
            self.logger.info("Organization completed successfully!")
        
        stats['success'] = len(stats['errors']) == 0
        stats['dry_run'] = self.dry_run
        
        return stats
    
    def generate_report(self) -> str:
        """
        Generate a detailed report of the operation.
        
        Returns:
            String containing the report
        """
        report = []
        report.append("=" * 60)
        report.append("FILE ORGANIZER REPORT")
        report.append("=" * 60)
        report.append(f"Directory: {self.target_dir}")
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Mode: {'DRY RUN' if self.dry_run else 'ACTUAL'}")
        report.append("")
        
        if self.moved_files:
            report.append("MOVED FILES:")
            report.append("-" * 40)
            for filename, category, dest in self.moved_files:
                report.append(f"  {filename} -> {category}/")
        else:
            report.append("No files were moved.")
        
        if self.errors:
            report.append("")
            report.append("ERRORS:")
            report.append("-" * 40)
            for error in self.errors:
                report.append(f"  {error}")
        
        return "\n".join(report)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Organize files in a directory by category.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Organize current directory
  python file_organizer.py
  
  # Organize Downloads folder
  python file_organizer.py -d ~/Downloads
  
  # Dry run (preview changes)
  python file_organizer.py -d ~/Downloads --dry-run
  
  # Use custom config and save log
  python file_organizer.py -d ~/Downloads -c config.json -l organize.log
        """
    )
    
    parser.add_argument(
        '-d', '--directory',
        type=str,
        default=os.getcwd(),
        help='Target directory to organize (default: current directory)'
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        help='Path to JSON configuration file with custom categories'
    )
    
    parser.add_argument(
        '-l', '--log',
        type=str,
        default='file_organizer.log',
        help='Path to log file (default: file_organizer.log)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate organization without actually moving files'
    )
    
    parser.add_argument(
        '--no-log',
        action='store_true',
        help='Disable logging to file'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output (more detailed logging)'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate and save a detailed report'
    )
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create organizer instance
    organizer = FileOrganizer(
        target_dir=args.directory,
        config_file=args.config if args.config else None,
        dry_run=args.dry_run,
        log_file=args.log if not args.no_log else None
    )
    
    # Run organization
    try:
        stats = organizer.organize()
        
        # Generate report if requested
        if args.report and stats['success']:
            report = organizer.generate_report()
            report_file = Path(args.directory) / 'organization_report.txt'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logging.info(f"Report saved to: {report_file}")
        
        # Exit with appropriate code
        sys.exit(0 if stats['success'] else 1)
        
    except KeyboardInterrupt:
        logging.info("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    # Если переданы аргументы командной строки - используем их
    if len(sys.argv) > 1:
        main()
    else:
        # Если аргументов нет - используем вашу папку по умолчанию
        sys.argv = ['file_organizer.py', '-d', r'D:\Загрузки']
        main()