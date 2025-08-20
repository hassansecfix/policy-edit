import { FileUpload, QuestionnaireAnswer } from '@/types';
import fs from 'fs';
import { NextRequest, NextResponse } from 'next/server';
import path from 'path';

export async function POST(request: NextRequest) {
  try {
    // Handle JSON with base64 file uploads
    const body = await request.json();
    const answers: Record<string, QuestionnaireAnswer> = body.answers;

    console.log('📝 Saving questionnaire answers:', Object.keys(answers).length, 'answers');
    console.log('🔧 Current working directory:', process.cwd());

    if (!answers || Object.keys(answers).length === 0) {
      return NextResponse.json({ error: 'No answers provided' }, { status: 400 });
    }

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

    const questionsContent = fs.readFileSync(questionsPath, 'utf-8');
    const questionLines = questionsContent.trim().split('\n').slice(1); // Skip header

    // Create a map of question data
    const questionsMap = new Map();
    questionLines.forEach((line) => {
      const [questionNumber, questionText, field, responseType] = line.split(';');
      questionsMap.set(field, {
        questionNumber: parseInt(questionNumber),
        questionText,
        responseType,
      });
    });

    // Create CSV content in the format expected by the automation system
    const csvLines = ['Question Number;Question Text;field;Response Type;User Response'];

    // Store logo base64 data for embedding in CSV
    let logoBase64Data = null;

    // Sort answers by question number to maintain order
    const sortedAnswers = Object.values(answers).sort(
      (a, b) => a.questionNumber - b.questionNumber,
    );

    sortedAnswers.forEach((answer) => {
      const questionData = questionsMap.get(answer.field);
      if (questionData) {
        // Handle different value types (File objects need special handling)
        let valueString = answer.value;
        if (answer.value instanceof File) {
          // File objects from JSON can't be processed directly
          // For logo files, we'll save them as company_logo.png
          if (answer.field === 'onboarding.company_logo') {
            // This shouldn't happen with the new base64 upload, but handle it gracefully
            valueString = 'data/company_logo.png';
          } else {
            valueString = answer.value.name;
          }
        } else if (
          typeof answer.value === 'object' &&
          answer.value !== null &&
          'data' in answer.value
        ) {
          // Handle base64 file uploads
          const fileData = answer.value as FileUpload;
          if (answer.field === 'onboarding.company_logo') {
            if (fileData.data === 'existing-file') {
              // Read existing logo file and convert to base64 for embedding
              const existingLogoPath = path.join(process.cwd(), '../data/company_logo.png');
              if (fs.existsSync(existingLogoPath)) {
                try {
                  const logoBuffer = fs.readFileSync(existingLogoPath);
                  const base64String = logoBuffer.toString('base64');
                  const mimeType = 'image/png'; // Assume PNG for existing files
                  logoBase64Data = `data:${mimeType};base64,${base64String}`;
                  valueString = 'data/company_logo.png';
                } catch (error) {
                  console.error('Error reading existing logo file:', error);
                  valueString = 'data/company_logo.png';
                }
              } else {
                valueString = 'data/company_logo.png';
              }
            } else if (fileData.data) {
              try {
                // Save the new base64 data as company_logo.png
                const base64Data = fileData.data.split(',')[1]; // Remove data:image/png;base64, prefix
                const logoBuffer = Buffer.from(base64Data, 'base64');
                const logoPath = path.join(process.cwd(), '../data/company_logo.png');
                fs.writeFileSync(logoPath, logoBuffer);
                valueString = 'data/company_logo.png';

                // Store base64 data for CSV embedding
                logoBase64Data = fileData.data;
              } catch (error) {
                console.error('Error saving logo file:', error);
                valueString = fileData.name || 'uploaded_file';
              }
            } else {
              valueString = 'data/company_logo.png'; // Fallback for logo field
            }
          } else {
            valueString = fileData.name || 'uploaded_file';
          }
        } else if (typeof answer.value === 'object') {
          valueString = JSON.stringify(answer.value);
        }

        const csvLine = `${questionData.questionNumber};${questionData.questionText};${answer.field};${questionData.responseType};${valueString}`;
        csvLines.push(csvLine);
      }
    });

    // Add logo base64 data as a special CSV entry if available
    if (logoBase64Data) {
      const logoMetaLine = `99;Logo Base64 Data;_logo_base64_data;File upload;${logoBase64Data}`;
      csvLines.push(logoMetaLine);
    }

    const csvContent = csvLines.join('\n');

    // Determine the data directory from the questions path
    const dataDir = path.dirname(questionsPath);
    const answersPath = path.join(dataDir, 'user_questionnaire_responses.csv');

    console.log('💾 Saving answers to:', answersPath);
    console.log('📊 CSV content preview:', csvContent.split('\n').slice(0, 3).join('\n'));

    try {
      fs.writeFileSync(answersPath, csvContent, 'utf-8');
      console.log('✅ Successfully saved answers to file');

      // Verify the file was written
      if (fs.existsSync(answersPath)) {
        const savedContent = fs.readFileSync(answersPath, 'utf-8');
        console.log(
          '✅ File verification: File exists and contains',
          savedContent.split('\n').length,
          'lines',
        );
      } else {
        console.error('❌ File verification failed: File does not exist after write');
      }
    } catch (writeError) {
      console.error('❌ Failed to write answers file:', writeError);
      return NextResponse.json(
        {
          error: 'Failed to write answers file',
          details: writeError instanceof Error ? writeError.message : String(writeError),
          path: answersPath,
        },
        { status: 500 },
      );
    }

    return NextResponse.json({
      success: true,
      message: 'Answers saved successfully',
      answerCount: Object.keys(answers).length,
      filePath: answersPath,
      dataDir: dataDir,
      answers: sortedAnswers.map((a) => ({ field: a.field, value: a.value })), // Include answers for debugging
    });
  } catch (error) {
    console.error('Error saving answers:', error);
    return NextResponse.json({ error: 'Failed to save answers' }, { status: 500 });
  }
}

export async function GET() {
  try {
    // Try multiple possible paths for the data directory
    const possibleAnswersPaths = [
      path.join(process.cwd(), '../data/user_questionnaire_responses.csv'), // Original path
      path.join(process.cwd(), '../../data/user_questionnaire_responses.csv'), // One more level up
      path.join(process.cwd(), 'data/user_questionnaire_responses.csv'), // Same level
      path.join(process.cwd(), './data/user_questionnaire_responses.csv'), // Explicit same level
    ];

    let answersPath = '';
    for (const testPath of possibleAnswersPaths) {
      if (fs.existsSync(testPath)) {
        answersPath = testPath;
        console.log('✅ Found answers file at:', answersPath);
        break;
      }
    }

    if (!answersPath) {
      console.log('📄 No answers file found at any of these paths:', possibleAnswersPaths);
      return NextResponse.json(
        {
          exists: false,
          message: 'No answers file found',
          searchedPaths: possibleAnswersPaths,
        },
        { status: 404 },
      );
    }

    const csvContent = fs.readFileSync(answersPath, 'utf-8');
    const lineCount = csvContent.split('\n').length;
    console.log('📊 Found answers file with', lineCount, 'lines');

    return NextResponse.json({
      exists: true,
      content: csvContent,
      message: 'Answers file found',
      filePath: answersPath,
      lineCount: lineCount,
    });
  } catch (error) {
    console.error('Error checking answers:', error);
    return NextResponse.json({ error: 'Failed to check answers' }, { status: 500 });
  }
}
