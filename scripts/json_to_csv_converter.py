#!/usr/bin/env python3
"""
JSON to CSV Converter for Policy Automation

Converts JSON instructions format to CSV format for GitHub Actions compatibility.

Usage:
    python3 json_to_csv_converter.py input.json output.csv
"""

import json
import csv
import sys
import argparse
from pathlib import Path

def convert_json_to_csv(json_path, csv_path):
    """Convert JSON instructions to CSV format."""
    
    # Load JSON
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load JSON file: {e}")
    
    # Validate JSON structure
    if 'instructions' not in data or 'operations' not in data['instructions']:
        raise Exception("Invalid JSON structure: missing instructions.operations")
    
    operations = data['instructions']['operations']
    if not operations:
        raise Exception("No operations found in JSON")
    
    # Convert to CSV format
    csv_rows = []
    
    # Add header
    csv_rows.append([
        'Find', 'Replace', 'MatchCase', 'WholeWord', 'Wildcards', 'Description', 'Rule'
    ])
    
    # Convert each operation
    for i, operation in enumerate(operations):
        try:
            # Extract fields
            target_text = operation['target_text']
            action = operation['action']
            replacement = operation.get('replacement', '')
            comment = operation.get('comment', '')
            
            # Handle different action types
            if action == 'replace':
                find_text = target_text
                replace_text = replacement
            elif action == 'delete':
                find_text = target_text
                replace_text = ''  # Empty for deletion
            elif action == 'comment':
                # For comment-only operations, we'll add a special marker
                find_text = target_text
                replace_text = target_text  # Keep same text but add comment
            else:
                print(f"⚠️  Warning: Unknown action '{action}' in operation {i+1}")
                continue
            
            # Default CSV settings
            match_case = 'FALSE'
            whole_word = 'TRUE'  # Usually want whole word matching for placeholders
            wildcards = 'FALSE'
            
            # Create description from comment
            # Remove \\n\\n and replace with spaces for CSV
            description = comment.replace('\\n\\n', ' ').replace('\\n', ' ').strip()
            if len(description) > 100:
                description = description[:97] + '...'
            
            # Generate rule ID based on operation index
            rule_id = f"RULE_{i+1:02d}"
            
            # Add CSV row
            csv_rows.append([
                find_text,
                replace_text,
                match_case,
                whole_word,
                wildcards,
                description,
                rule_id
            ])
            
        except KeyError as e:
            print(f"⚠️  Warning: Missing field {e} in operation {i+1}, skipping")
            continue
        except Exception as e:
            print(f"⚠️  Warning: Error processing operation {i+1}: {e}")
            continue
    
    # Write CSV file
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_rows)
    except Exception as e:
        raise Exception(f"Failed to write CSV file: {e}")
    
    return len(csv_rows) - 1  # Subtract header row

def main():
    parser = argparse.ArgumentParser(description='Convert JSON instructions to CSV format')
    parser.add_argument('json_file', help='Path to input JSON file')
    parser.add_argument('csv_file', help='Path to output CSV file')
    
    args = parser.parse_args()
    
    print("🔄 JSON to CSV Converter Starting...")
    print(f"📥 Input JSON: {args.json_file}")
    print(f"📤 Output CSV: {args.csv_file}")
    
    try:
        # Validate input file exists
        if not Path(args.json_file).exists():
            print(f"❌ Error: JSON file not found: {args.json_file}")
            sys.exit(1)
        
        # Convert
        operations_count = convert_json_to_csv(args.json_file, args.csv_file)
        
        print(f"\n✅ Conversion successful!")
        print(f"📊 Converted {operations_count} operations")
        print(f"📁 CSV saved to: {args.csv_file}")
        
        # Show preview
        print("\n📋 CSV Preview:")
        with open(args.csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:4]):
                print(f"   {line.strip()}")
            if len(lines) > 4:
                print(f"   ... and {len(lines)-4} more rows")
        
        print(f"\n🚀 Ready for GitHub Actions automation!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
