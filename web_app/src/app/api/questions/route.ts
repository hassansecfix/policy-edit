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

    // Read and parse the CSV file
    const csvContent = fs.readFileSync(questionsPath, 'utf-8');
    const lines = csvContent.trim().split('\n');

    // Skip header row
    const dataLines = lines.slice(1);

    const questions: Question[] = dataLines.map((line) => {
      const [questionNumber, questionText, field, responseType] = line.split(';');

      return {
        questionNumber: parseInt(questionNumber),
        questionText: questionText,
        field: field,
        responseType: responseType as Question['responseType'],
      };
    });

    return NextResponse.json(questions);
  } catch (error) {
    console.error('Error loading questions:', error);
    return NextResponse.json({ error: 'Failed to load questions' }, { status: 500 });
  }
}
