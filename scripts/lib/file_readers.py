"""
File Reading Utilities

This module provides utilities for reading edit instructions from CSV and JSON files,
handling different formats and structures.
"""

import csv
import json
from pathlib import Path
from typing import Iterator, Dict, Any


class EditFileReader:
    """
    Reads edit instructions from CSV or JSON files.
    """
    
    @staticmethod
    def read_edits(file_path: str) -> Iterator[Dict[str, str]]:
        """
        Load edits from either CSV or JSON format.
        
        Args:
            file_path: Path to the CSV or JSON file
            
        Yields:
            Dictionary containing edit instructions with standardized keys
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.json':
            yield from EditFileReader._read_json_edits(file_path)
        else:
            yield from EditFileReader._read_csv_edits(file_path)
    
    @staticmethod
    def _read_json_edits(file_path: str) -> Iterator[Dict[str, str]]:
        """
        Load edits from JSON operations format.
        
        Args:
            file_path: Path to the JSON file
            
        Yields:
            Dictionary containing edit instructions
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        operations = data.get('instructions', {}).get('operations', [])
        
        for op in operations:
            action = op.get('action', 'replace')
            target_text = op.get('target_text', '')
            replacement = op.get('replacement', '')
            comment = op.get('comment', '')
            author = op.get('comment_author', 'AI Assistant')
            
            # Handle comment-only operations in main loop, not here
            if action == 'comment':
                continue
                
            # Handle delete operations (empty replacement)
            if action == 'delete':
                replacement = ''
            
            yield {
                "Find": target_text,
                "Replace": replacement,
                "MatchCase": "",  # Default to False
                "WholeWord": "",  # Default to False  
                "Wildcards": "",  # Default to False
                "Comment": comment,
                "Author": author,
            }
    
    @staticmethod
    def _read_csv_edits(file_path: str) -> Iterator[Dict[str, str]]:
        """
        Load edits from CSV format with flexible column handling.
        
        Args:
            file_path: Path to the CSV file
            
        Yields:
            Dictionary containing edit instructions
        """
        with open(file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            
            if not reader.fieldnames or len(reader.fieldnames) < 2:
                # No header: assume simple CSV
                f.seek(0)
                reader2 = csv.reader(f)
                for row in reader2:
                    if not row:
                        continue
                    yield {
                        "Find": row[0],
                        "Replace": row[1] if len(row) > 1 else "",
                        "MatchCase": row[2] if len(row) > 2 else "",
                        "WholeWord": row[3] if len(row) > 3 else "",
                        "Wildcards": row[4] if len(row) > 4 else "",
                        "Comment": row[5] if len(row) > 5 else "",
                        "Author": row[6] if len(row) > 6 else "AI Assistant",
                    }
            else:
                # Has header: use DictReader with flexible column names
                for rec in reader:
                    yield {
                        "Find": EditFileReader._get_column_value(rec, ["Find", "find", "FIND"]).strip(),
                        "Replace": EditFileReader._get_column_value(rec, ["Replace", "replace", "REPLACE"]),
                        "MatchCase": EditFileReader._get_column_value(rec, ["MatchCase", "matchcase", "MATCHCASE"]),
                        "WholeWord": EditFileReader._get_column_value(rec, ["WholeWord", "wholeword", "WHOLEWORD"]),
                        "Wildcards": EditFileReader._get_column_value(rec, ["Wildcards", "wildcards", "WILDCARDS"]),
                        "Comment": EditFileReader._get_column_value(rec, ["Comment", "comment", "COMMENT"]),
                        "Author": EditFileReader._get_column_value(rec, ["Author", "author", "AUTHOR"]) or "AI Assistant",
                    }
    
    @staticmethod
    def _get_column_value(record: Dict[str, str], possible_keys: list) -> str:
        """
        Get column value with case-insensitive key matching.
        
        Args:
            record: CSV record dictionary
            possible_keys: List of possible column names to try
            
        Returns:
            Column value or empty string if not found
        """
        for key in possible_keys:
            value = record.get(key)
            if value is not None:
                return value
        return ""


class OperationExtractor:
    """
    Extracts specific operation types from JSON data.
    """
    
    @staticmethod
    def get_operations_by_type(file_path: str, operation_type: str) -> list:
        """
        Extract operations of a specific type from JSON file.
        
        Args:
            file_path: Path to the JSON file
            operation_type: Type of operation to extract (e.g., 'replace_with_logo', 'comment')
            
        Returns:
            List of operations matching the specified type
        """
        if not file_path.endswith('.json'):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            operations = data.get('instructions', {}).get('operations', [])
            return [op for op in operations if op.get('action') == operation_type]
            
        except Exception as e:
            print(f"Error reading operations from {file_path}: {e}")
            return []
    
    @staticmethod
    def get_metadata(file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Metadata dictionary
        """
        if not file_path.endswith('.json'):
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data.get('metadata', {})
            
        except Exception as e:
            print(f"Error reading metadata from {file_path}: {e}")
            return {}
    
    @staticmethod
    def get_all_operations(file_path: str) -> list:
        """
        Get all operations from JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            List of all operations
        """
        if not file_path.endswith('.json'):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data.get('instructions', {}).get('operations', [])
            
        except Exception as e:
            print(f"Error reading operations from {file_path}: {e}")
            return []
