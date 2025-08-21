import { QuestionnaireAnswer } from '@/types';
import fs from 'fs';
import { NextRequest, NextResponse } from 'next/server';
import path from 'path';

export async function POST(request: NextRequest) {
  try {
    // Handle JSON with base64 file uploads
    const body = await request.json();
    const answers: Record<string, QuestionnaireAnswer> = body.answers;

    console.log('📝 Receiving questionnaire answers:', Object.keys(answers).length, 'answers');
    console.log('✨ Using Direct API approach - processing logo and preparing for automation');

    if (!answers || Object.keys(answers).length === 0) {
      return NextResponse.json({ error: 'No answers provided' }, { status: 400 });
    }

    // Extract and save company logo if provided
    let logoProcessed = false;
    try {
      const logoAnswer = answers['onboarding.company_logo'];
      if (
        logoAnswer &&
        typeof logoAnswer.value === 'object' &&
        logoAnswer.value &&
        'data' in logoAnswer.value
      ) {
        const logoData = logoAnswer.value as any;
        if (logoData.data && logoData.type?.startsWith('image/')) {
          console.log('🖼️ Processing uploaded company logo:', logoData.name);

          // Extract base64 data (remove data URL prefix if present)
          let base64Data = logoData.data;
          if (base64Data.includes(',')) {
            base64Data = base64Data.split(',')[1];
          }

          // Convert base64 to buffer
          const imageBuffer = Buffer.from(base64Data, 'base64');

          // Get project root directory (parent of web_app)
          const projectRoot = path.join(process.cwd(), '..');
          const logoPath = path.join(projectRoot, 'data', 'company_logo.png');

          // Ensure data directory exists
          const dataDir = path.dirname(logoPath);
          if (!fs.existsSync(dataDir)) {
            fs.mkdirSync(dataDir, { recursive: true });
          }

          // Save the logo file
          fs.writeFileSync(logoPath, imageBuffer);
          logoProcessed = true;

          console.log('✅ Company logo saved to:', logoPath);
          console.log('📏 Logo size:', Math.round(imageBuffer.length / 1024), 'KB');
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
      method: 'direct_api',
      timestamp: Date.now(),
      note: logoProcessed
        ? 'Answers processed and company logo extracted successfully!'
        : 'Answers processed - no logo upload detected',
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
