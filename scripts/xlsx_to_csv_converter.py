#!/usr/bin/env python3
"""
Convert XLSX questionnaire responses to CSV format for AI processing.
This makes it easier for AI to read the customer data.
"""
import pandas as pd
import sys
import os

def convert_xlsx_to_csv(xlsx_path, csv_path):
    """Convert XLSX to CSV format."""
    try:
        # Read the Excel file
        df = pd.read_excel(xlsx_path)
        
        # Save as CSV
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        print(f"✅ Converted {xlsx_path} to {csv_path}")
        print(f"📊 Data shape: {df.shape[0]} rows, {df.shape[1]} columns")
        
        # Show preview
        print(f"\n📋 Column names:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. {col}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error converting file: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 xlsx_to_csv_converter.py input.xlsx output.csv")
        print("Example: python3 xlsx_to_csv_converter.py data/questionnaire.xlsx data/questionnaire.csv")
        sys.exit(1)
    
    xlsx_path = sys.argv[1]
    csv_path = sys.argv[2]
    
    if not os.path.exists(xlsx_path):
        print(f"❌ Input file not found: {xlsx_path}")
        sys.exit(1)
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    print(f"🔄 Converting {xlsx_path} to {csv_path}...")
    
    if convert_xlsx_to_csv(xlsx_path, csv_path):
        print(f"\n🎉 Success! CSV file ready for AI processing.")
        print(f"📁 Output: {csv_path}")
    else:
        print(f"\n❌ Conversion failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
