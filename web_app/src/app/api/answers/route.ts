import { QuestionnaireAnswer } from '@/types';
import { NextRequest, NextResponse } from 'next/server';

interface FileUploadValue {
  name: string;
  size: number;
  type: string;
  data: string;
}

// Generate a unique user session ID
function generateUserId(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 8);
  return `user_${timestamp}_${random}`;
}

export async function POST(request: NextRequest) {
  try {
    // Handle JSON with base64 file uploads
    const body = await request.json();
    const answers: Record<string, QuestionnaireAnswer> = body.answers;

    // Generate unique user ID for this session
    const userId = generateUserId();

    console.log('📝 Receiving questionnaire answers:', Object.keys(answers).length, 'answers');
    console.log('✨ Using Direct API approach - processing logo and preparing for automation');

    if (!answers || Object.keys(answers).length === 0) {
      return NextResponse.json({ error: 'No answers provided' }, { status: 400 });
    }

    // Process company logo by adding base64 data to questionnaire answers
    let logoProcessed = false;
    try {
      const logoAnswer = answers['onboarding.company_logo'];
      if (
        logoAnswer &&
        typeof logoAnswer.value === 'object' &&
        logoAnswer.value &&
        'data' in logoAnswer.value
      ) {
        const logoData = logoAnswer.value as FileUploadValue;
        if (logoData.data && logoData.type?.startsWith('image/')) {
          console.log('🖼️ Processing uploaded company logo:', logoData.name);

          // Add base64 logo data as a special entry for automation scripts
          // This follows the format automation scripts expect for logo processing
          answers['_logo_base64_data'] = {
            questionNumber: 99,
            field: '_logo_base64_data',
            value: logoData.data, // Keep full data URL (data:image/png;base64,...)
          };

          logoProcessed = true;

          // Calculate logo size for logging
          let base64Data = logoData.data;
          if (base64Data.includes(',')) {
            base64Data = base64Data.split(',')[1];
          }
          const sizeKB = Math.round((base64Data.length * 3) / 4 / 1024);

          console.log('✅ Company logo processed as base64 data (no file created)');
          console.log('📏 Logo size:', sizeKB, 'KB');
          console.log('🚀 Logo data will be passed directly to automation scripts');
        }
      }
    } catch (logoError) {
      console.error('⚠️ Error processing logo:', logoError);
      // Don't fail the entire request if logo processing fails
    }

    console.log('📊 Answers processed successfully, ready for automation');

    return NextResponse.json({
      success: true,
      message: 'Answers received - ready for direct automation',
      answerCount: Object.keys(answers).length,
      logoProcessed: logoProcessed,
      userId: userId, // Return user ID for automation system
      method: 'direct_api',
      timestamp: Date.now(),
      note: logoProcessed
        ? `Answers processed and company logo extracted successfully! (User: ${userId})`
        : `Answers processed - no logo upload detected (User: ${userId})`,
    });
  } catch (error) {
    console.error('Error processing answers:', error);
    return NextResponse.json({ error: 'Failed to process answers' }, { status: 500 });
  }
}

export async function GET() {
  try {
    // For the Direct API approach, we can provide a simple status
    console.log('📊 GET request - Direct API approach active');

    return NextResponse.json({
      exists: true,
      method: 'direct_api',
      message: 'Using Direct API - answers sent directly to automation',
      note: 'No file storage needed - answers are processed in real-time',
      timestamp: Date.now(),
    });
  } catch (error) {
    console.error('Error checking answers:', error);
    return NextResponse.json({ error: 'Failed to check answers' }, { status: 500 });
  }
}
