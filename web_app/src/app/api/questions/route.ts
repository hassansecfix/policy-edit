import { Question } from '@/types';
import fs from 'fs';
import { NextResponse } from 'next/server';
import path from 'path';

export async function GET() {
  try {
    // Try multiple possible paths for the data directory
    const possibleQuestionsPaths = [
      path.join(process.cwd(), '../data/questions.csv'), // Original path
      path.join(process.cwd(), '../../data/questions.csv'), // One more level up
      path.join(process.cwd(), 'data/questions.csv'), // Same level
      path.join(process.cwd(), './data/questions.csv'), // Explicit same level
    ];

    let questionsPath = '';
    for (const testPath of possibleQuestionsPaths) {
      console.log('🔍 Checking questions path:', testPath);
      if (fs.existsSync(testPath)) {
        questionsPath = testPath;
        console.log('✅ Found questions file at:', questionsPath);
        break;
      }
    }

    if (!questionsPath) {
      console.error('❌ Questions file not found at any of these paths:', possibleQuestionsPaths);
      return NextResponse.json(
        {
          error: 'Questions file not found',
          searchedPaths: possibleQuestionsPaths,
          cwd: process.cwd(),
        },
        { status: 404 },
      );
    }

    // Read and parse the original CSV file with proper multiline handling
    const csvContent = fs.readFileSync(questionsPath, 'utf-8');

    // Custom CSV parser to handle multiline quoted fields
    function parseCSV(content: string): string[][] {
      const result: string[][] = [];
      const lines = content.split('\n');
      let currentRow: string[] = [];
      let currentField = '';
      let insideQuotes = false;
      let i = 0;

      while (i < lines.length) {
        const line = lines[i];
        let j = 0;

        while (j < line.length) {
          const char = line[j];

          if (char === '"') {
            if (insideQuotes && j + 1 < line.length && line[j + 1] === '"') {
              // Escaped quote
              currentField += '"';
              j += 2;
            } else {
              // Toggle quote state
              insideQuotes = !insideQuotes;
              j++;
            }
          } else if (char === ',' && !insideQuotes) {
            // End of field
            currentRow.push(currentField.trim());
            currentField = '';
            j++;
          } else {
            currentField += char;
            j++;
          }
        }

        if (insideQuotes) {
          // Continue to next line if we're inside quotes
          currentField += '\n';
          i++;
        } else {
          // End of row
          currentRow.push(currentField.trim());
          if (currentRow.some((field) => field.length > 0)) {
            result.push(currentRow);
          }
          currentRow = [];
          currentField = '';
          i++;
        }
      }

      // Add the last row if it exists
      if (currentRow.length > 0 || currentField.length > 0) {
        currentRow.push(currentField.trim());
        if (currentRow.some((field) => field.length > 0)) {
          result.push(currentRow);
        }
      }

      return result;
    }

    const rows = parseCSV(csvContent);
    const dataRows = rows.slice(1); // Skip header

    const questions: Question[] = dataRows
      .map((columns, index): Question | null => {
        if (columns.length < 6) {
          console.log(`Row ${index + 2}: Not enough columns (${columns.length})`);
          return null;
        }

        const [
          questionNumber,
          questionText,
          questionDescription,
          field,
          responseType,
          responseOptions,
        ] = columns;

        // Parse response options if they exist
        let options: string[] | undefined = undefined;
        if (responseOptions && responseOptions !== '-') {
          let rawOptions: string[] = [];

          // Handle options separated by newlines, pipes, commas, or slashes
          if (responseOptions.includes('\n')) {
            // Multiline options (like the review frequency)
            rawOptions = responseOptions.split('\n');
          } else if (responseOptions.includes('|')) {
            // Pipe-separated options (like Yes|No)
            rawOptions = responseOptions.split('|');
          } else if (responseOptions.includes('/')) {
            // Slash-separated options
            rawOptions = responseOptions.split('/');
          } else if (responseOptions.includes(',')) {
            // Comma-separated options
            rawOptions = responseOptions.split(',');
          } else {
            // Single option
            rawOptions = [responseOptions];
          }

          // Clean up each option
          const cleanedOptions = rawOptions
            .map((opt) => opt.trim())
            .filter((opt) => opt.length > 0)
            .map((opt) => opt.replace(/^[-•–—]\s*/, '')) // Remove bullet points
            .map((opt) => opt.replace(/^"/, '').replace(/"$/, '')) // Remove quotes
            .filter((opt) => opt.length > 0); // Filter again after cleaning

          options = cleanedOptions.length > 0 ? cleanedOptions : undefined;
        }

        const parsedQuestionNumber =
          parseInt(questionNumber.replace(/^\d+\s+/, '')) || parseInt(questionNumber);

        // Validate required fields
        if (!parsedQuestionNumber || !questionText || !field || !responseType) {
          return null;
        }

        return {
          questionNumber: parsedQuestionNumber,
          questionText: questionText,
          field: field,
          responseType: responseType as Question['responseType'],
          options: options,
        };
      })
      .filter((q): q is Question => q !== null);

    return NextResponse.json(questions);
  } catch (error) {
    console.error('Error loading questions:', error);
    return NextResponse.json({ error: 'Failed to load questions' }, { status: 500 });
  }
}
