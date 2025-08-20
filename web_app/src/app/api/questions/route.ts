import { Question } from '@/types';
import fs from 'fs';
import { NextResponse } from 'next/server';
import path from 'path';

export async function GET() {
  try {
    // Path to the questions.csv file
    const questionsPath = path.join(process.cwd(), '../data/questions.csv');

    // Check if file exists
    if (!fs.existsSync(questionsPath)) {
      return NextResponse.json({ error: 'Questions file not found' }, { status: 404 });
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
