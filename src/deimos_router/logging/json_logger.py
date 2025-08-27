"""JSON file logger implementation with daily rotation."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from .base import LoggerBackend, LogEntry


class JSONFileLogger(LoggerBackend):
    """JSON file logger with daily rotation."""
    
    def __init__(self, log_directory: str = "./logs", filename_prefix: str = "deimos-logs"):
        """Initialize the JSON file logger.
        
        Args:
            log_directory: Directory to store log files
            filename_prefix: Prefix for log filenames
        """
        self.log_directory = Path(log_directory)
        self.filename_prefix = filename_prefix
        self._current_file = None
        self._current_date = None
        
        # Create log directory if it doesn't exist
        self.log_directory.mkdir(parents=True, exist_ok=True)
    
    def _get_log_filename(self, date: datetime) -> Path:
        """Get the log filename for a given date.
        
        Args:
            date: The date for the log file
            
        Returns:
            Path to the log file
        """
        date_str = date.strftime("%Y-%m-%d")
        filename = f"{self.filename_prefix}-{date_str}.jsonl"
        return self.log_directory / filename
    
    def _ensure_file_open(self, entry_date: datetime) -> None:
        """Ensure the correct log file is open for the given date.
        
        Args:
            entry_date: The date of the log entry
        """
        entry_date_str = entry_date.strftime("%Y-%m-%d")
        
        # Check if we need to rotate to a new file
        if self._current_date != entry_date_str:
            # Close current file if open
            if self._current_file:
                self._current_file.close()
            
            # Open new file
            log_file_path = self._get_log_filename(entry_date)
            self._current_file = open(log_file_path, 'a', encoding='utf-8')
            self._current_date = entry_date_str
    
    def log_entry(self, entry: LogEntry) -> None:
        """Log a complete entry to the JSON file.
        
        Args:
            entry: The log entry to write
        """
        try:
            # Ensure correct file is open
            self._ensure_file_open(entry.timestamp)
            
            # Convert entry to JSON and write
            json_line = json.dumps(entry.to_dict(), ensure_ascii=False, separators=(',', ':'))
            self._current_file.write(json_line + '\n')
            self._current_file.flush()  # Ensure data is written immediately
            
        except Exception as e:
            # In case of logging errors, we don't want to crash the main application
            # Could potentially log to stderr or a fallback location
            print(f"Error writing to log file: {e}", file=__import__('sys').stderr)
    
    def close(self) -> None:
        """Close the current log file."""
        if self._current_file:
            self._current_file.close()
            self._current_file = None
            self._current_date = None
    
    def get_log_files(self) -> list[Path]:
        """Get a list of all log files in the log directory.
        
        Returns:
            List of log file paths
        """
        pattern = f"{self.filename_prefix}-*.jsonl"
        return sorted(self.log_directory.glob(pattern))
    
    def read_log_entries(self, date: Optional[datetime] = None) -> list[dict]:
        """Read log entries from a specific date or all dates.
        
        Args:
            date: Specific date to read (None for all dates)
            
        Returns:
            List of log entry dictionaries
        """
        entries = []
        
        if date:
            # Read from specific date file
            log_file = self._get_log_filename(date)
            if log_file.exists():
                entries.extend(self._read_jsonl_file(log_file))
        else:
            # Read from all log files
            for log_file in self.get_log_files():
                entries.extend(self._read_jsonl_file(log_file))
        
        return entries
    
    def _read_jsonl_file(self, file_path: Path) -> list[dict]:
        """Read entries from a JSONL file.
        
        Args:
            file_path: Path to the JSONL file
            
        Returns:
            List of parsed JSON objects
        """
        entries = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            print(f"Error parsing JSON line in {file_path}: {e}", file=__import__('sys').stderr)
        except FileNotFoundError:
            pass  # File doesn't exist yet
        except Exception as e:
            print(f"Error reading log file {file_path}: {e}", file=__import__('sys').stderr)
        
        return entries
