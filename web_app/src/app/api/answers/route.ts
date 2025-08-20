import { QuestionnaireAnswer } from '@/types';
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // Handle JSON with base64 file uploads
    const body = await request.json();
    const answers: Record<string, QuestionnaireAnswer> = body.answers;

    console.log('📝 Receiving questionnaire answers:', Object.keys(answers).length, 'answers');
    console.log('✨ Using Direct API approach - no complex file storage needed!');

    if (!answers || Object.keys(answers).length === 0) {
      return NextResponse.json({ error: 'No answers provided' }, { status: 400 });
    }

    // With Direct API approach, we only need to acknowledge receipt
    // The answers are already in localStorage and will be sent directly to automation
    console.log('📊 Answers received successfully, ready for direct automation');

    return NextResponse.json({
      success: true,
      message: 'Answers received - ready for direct automation',
      answerCount: Object.keys(answers).length,
      method: 'direct_api',
      timestamp: Date.now(),
      note: 'Answers are processed directly via API - no file storage needed!',
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