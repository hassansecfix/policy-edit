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
    const originalDataDir = path.dirname(questionsPath);

    // In serverless environments, /var/task is read-only, so use /tmp for writing
    const isRender = process.cwd().includes('/var/task') || process.env.RENDER;
    const isServerless = isRender || process.env.VERCEL || process.env.LAMBDA_TASK_ROOT;
    let writableDir = isServerless ? '/tmp' : originalDataDir;

    console.log('🌐 Environment check:', {
      isRender: isRender,
      isServerless: isServerless,
      originalDataDir: originalDataDir,
      writableDir: writableDir,
      cwd: process.cwd(),
      platform: process.platform,
    });

    let answersPath = path.join(writableDir, 'user_questionnaire_responses.csv');

    // Generate a unique filename with timestamp to avoid conflicts
    const timestamp = Date.now();
    const userSpecificFilename = `user_questionnaire_responses_${timestamp}.csv`;
    let userSpecificPath = path.join(writableDir, userSpecificFilename);

    console.log('💾 Saving answers to main file:', answersPath);
    console.log('💾 Saving answers to user-specific file:', userSpecificPath);
    console.log('📊 CSV content preview:', csvContent.split('\n').slice(0, 3).join('\n'));
    console.log('📁 Data directory permissions check...');

        // Check directory permissions and existence
    console.log('🔍 Checking writable directory:', writableDir);
    
    try {
      // First check if directory exists
      if (!fs.existsSync(writableDir)) {
        console.log('📁 Directory does not exist, attempting to create:', writableDir);
        fs.mkdirSync(writableDir, { recursive: true });
        console.log('✅ Successfully created directory:', writableDir);
      }
      
      const dirStats = fs.statSync(writableDir);
      console.log('📁 Writable directory exists:', true);
      console.log('📁 Writable directory stats:', {
        path: writableDir,
        isDirectory: dirStats.isDirectory(),
        mode: dirStats.mode.toString(8),
        uid: dirStats.uid,
        gid: dirStats.gid,
      });

      // Get current process info
      console.log('🔍 Process info:', {
        uid: process.getuid ? process.getuid() : 'N/A',
        gid: process.getgid ? process.getgid() : 'N/A',
        groups: process.getgroups ? process.getgroups() : 'N/A',
      });

      // Test if we can create a temporary file in the directory
      const testFilePath = path.join(writableDir, `test_write_${timestamp}.tmp`);
      console.log('🧪 Testing write to:', testFilePath);
      fs.writeFileSync(testFilePath, 'test', 'utf-8');
      console.log('✅ Directory write test successful');
      
      // Verify the test file was created
      if (fs.existsSync(testFilePath)) {
        const testContent = fs.readFileSync(testFilePath, 'utf-8');
        console.log('✅ Test file verification passed, content:', testContent);
        fs.unlinkSync(testFilePath); // Clean up test file
        console.log('✅ Test file cleanup successful');
      } else {
        console.error('❌ Test file was not created despite no error');
      }
    } catch (dirError) {
      // Type assertion for Node.js filesystem errors
      const fsError = dirError as Error & {
        code?: string;
        errno?: number;
        path?: string;
        syscall?: string;
      };
      
      console.error('❌ Directory permission check failed:', {
        error: fsError.message,
        code: fsError.code,
        errno: fsError.errno,
        path: fsError.path,
        syscall: fsError.syscall,
      });
      
      // Try alternative approaches
      if (isServerless) {
        console.log('🔄 Trying alternative writable locations...');
        const alternativePaths = ['/tmp', '/var/tmp', './tmp', process.cwd() + '/tmp'];
        
        for (const altPath of alternativePaths) {
          try {
            console.log('🧪 Testing alternative path:', altPath);
            if (!fs.existsSync(altPath)) {
              fs.mkdirSync(altPath, { recursive: true });
            }
            const testFile = path.join(altPath, `test_${timestamp}.tmp`);
            fs.writeFileSync(testFile, 'test', 'utf-8');
            fs.unlinkSync(testFile);
            console.log('✅ Alternative path works:', altPath);
            // Update writableDir to the working alternative
            const originalWritableDir = writableDir;
            writableDir = altPath;
            
            // Update file paths with the new working directory
            answersPath = path.join(writableDir, 'user_questionnaire_responses.csv');
            userSpecificPath = path.join(writableDir, userSpecificFilename);
            
            console.log('🔄 Updated file paths:');
            console.log('   Main file:', answersPath);
            console.log('   Timestamped file:', userSpecificPath);
            console.log('   Original dir:', originalWritableDir, '→ Working dir:', writableDir);
            break;
          } catch (altError) {
            const errorMessage = altError instanceof Error ? altError.message : String(altError);
            console.log('❌ Alternative path failed:', altPath, errorMessage);
          }
        }
      }
    }

    let writeSuccess = false;
    let actualFilePath = '';

    // ALWAYS try to write to main file first (for automation compatibility), then timestamped backup
    const filesToTry = [
      { path: answersPath, type: 'main', required: true },
      { path: userSpecificPath, type: 'timestamped-backup', required: false },
    ];

    console.log('🔄 Starting file write attempts...');
    console.log('📋 Files to try:', filesToTry.map(f => ({ type: f.type, path: f.path })));

    for (const fileInfo of filesToTry) {
      try {
        console.log(`🔄 Attempting to write ${fileInfo.type} file:`, fileInfo.path);
        console.log(`📊 Content length: ${csvContent.length} characters`);

        // Check if file already exists and its current state
        if (fs.existsSync(fileInfo.path)) {
          const existingStats = fs.statSync(fileInfo.path);
          console.log(`📄 Existing ${fileInfo.type} file stats:`, {
            size: existingStats.size,
            mtime: existingStats.mtime,
            mode: existingStats.mode.toString(8),
          });
        }

        // Write the file
        fs.writeFileSync(fileInfo.path, csvContent, 'utf-8');
        console.log(`✅ Successfully wrote ${fileInfo.type} file`);

        // Immediate verification
        if (fs.existsSync(fileInfo.path)) {
          const savedContent = fs.readFileSync(fileInfo.path, 'utf-8');
          const lineCount = savedContent.split('\n').length;
          const fileSize = savedContent.length;

          console.log(
            `✅ ${
              fileInfo.type
            } file verification: exists=${true}, lines=${lineCount}, size=${fileSize}`,
          );

          // Verify content matches what we wrote
          if (savedContent === csvContent) {
            console.log(`✅ ${fileInfo.type} file content matches exactly`);

            // For main file, this is our primary success
            if (fileInfo.type === 'main') {
              writeSuccess = true;
              actualFilePath = fileInfo.path;
            }
            // For backup files, just log success but don't change primary status
            else {
              console.log(`✅ ${fileInfo.type} file written as backup`);
            }
          } else {
            console.log(`⚠️ ${fileInfo.type} file content differs from what we wrote`);
            console.log(
              'Expected length:',
              csvContent.length,
              'Actual length:',
              savedContent.length,
            );
          }
        } else {
          console.error(
            `❌ ${fileInfo.type} file verification failed: File does not exist after write`,
          );
        }

        // Additional check - read the file again after a small delay to test persistence
        setTimeout(() => {
          if (fs.existsSync(fileInfo.path)) {
            const delayedContent = fs.readFileSync(fileInfo.path, 'utf-8');
            if (delayedContent === csvContent) {
              console.log(`✅ ${fileInfo.type} file persisted correctly after delay`);
            } else {
              console.log(`❌ ${fileInfo.type} file content changed after delay!`);
            }
          } else {
            console.log(`❌ ${fileInfo.type} file disappeared after delay!`);
          }
        }, 100);
      } catch (writeError) {
        // Type assertion for Node.js filesystem errors which have these properties
        const fsError = writeError as Error & {
          code?: string;
          errno?: number;
          syscall?: string;
        };

        console.error(`❌ Failed to write ${fileInfo.type} file:`, {
          path: fileInfo.path,
          error: writeError instanceof Error ? writeError.message : String(writeError),
          code: fsError.code,
          errno: fsError.errno,
          syscall: fsError.syscall,
        });

        // If main file fails, this is a critical error
        if (fileInfo.type === 'main') {
          return NextResponse.json(
            {
              error: 'Failed to write main answers file',
              details: writeError instanceof Error ? writeError.message : String(writeError),
              path: fileInfo.path,
              isRender: isRender,
              isServerless: isServerless,
            },
            { status: 500 },
          );
        }
        // If backup file fails, continue (not critical)
      }
    }

    if (!writeSuccess) {
      return NextResponse.json(
        {
          error: 'Failed to write answers file to any location',
          attemptedPaths: filesToTry.map((f) => f.path),
          dataDir: writableDir,
          originalDataDir: originalDataDir,
          isServerless: isServerless,
          cwd: process.cwd(),
        },
        { status: 500 },
      );
    }

    return NextResponse.json({
      success: true,
      message: 'Answers saved successfully',
      answerCount: Object.keys(answers).length,
      filePath: actualFilePath,
      userSpecificPath: userSpecificPath,
      mainFilePath: answersPath,
      dataDir: writableDir,
      originalDataDir: originalDataDir,
      isRender: isRender,
      isServerless: isServerless,
      timestamp: timestamp,
      directoryFallbackUsed: writableDir !== (isServerless ? '/tmp' : originalDataDir),
      answers: sortedAnswers.map((a) => ({ field: a.field, value: a.value })), // Include answers for debugging
    });
  } catch (error) {
    console.error('Error saving answers:', error);
    return NextResponse.json({ error: 'Failed to save answers' }, { status: 500 });
  }
}

export async function GET() {
  try {
    // Detect serverless environment
    const isServerless =
      process.cwd().includes('/var/task') || process.env.VERCEL || process.env.LAMBDA_TASK_ROOT;
    const writableDir = isServerless ? '/tmp' : null;

    console.log('🌐 GET Environment check:', {
      isServerless: isServerless,
      writableDir: writableDir,
      cwd: process.cwd(),
    });

    // Directories to search (writable directory first if serverless, then original data directories)
    const searchDirectories = [];
    if (writableDir) {
      searchDirectories.push(writableDir);
    }

    // Find the original data directory by looking for questions.csv
    const possibleQuestionsPaths = [
      path.join(process.cwd(), '../data/questions.csv'),
      path.join(process.cwd(), '../../data/questions.csv'),
      path.join(process.cwd(), 'data/questions.csv'),
      path.join(process.cwd(), './data/questions.csv'),
    ];

    let originalDataDir = '';
    for (const testPath of possibleQuestionsPaths) {
      if (fs.existsSync(testPath)) {
        originalDataDir = path.dirname(testPath);
        searchDirectories.push(originalDataDir);
        console.log('✅ Found original data directory at:', originalDataDir);
        break;
      }
    }

    console.log('🔍 Searching directories:', searchDirectories);

    // Search through all possible directories
    for (const searchDir of searchDirectories) {
      try {
        if (!fs.existsSync(searchDir)) {
          console.log('📁 Directory does not exist:', searchDir);
          continue;
        }

        // Look for both main file and user-specific files in this directory
        const mainAnswersPath = path.join(searchDir, 'user_questionnaire_responses.csv');
        const allFiles = fs.readdirSync(searchDir);
        const userSpecificFiles = allFiles.filter(
          (file) => file.startsWith('user_questionnaire_responses_') && file.endsWith('.csv'),
        );

        console.log(`📁 In directory ${searchDir}, found user-specific files:`, userSpecificFiles);

        // Prefer the most recent user-specific file, then fall back to main file
        let answersPath = '';
        let isUserSpecific = false;

        if (userSpecificFiles.length > 0) {
          // Sort by timestamp (filename contains timestamp)
          userSpecificFiles.sort((a, b) => {
            const timestampA = parseInt(
              a.replace('user_questionnaire_responses_', '').replace('.csv', ''),
            );
            const timestampB = parseInt(
              b.replace('user_questionnaire_responses_', '').replace('.csv', ''),
            );
            return timestampB - timestampA; // Most recent first
          });

          answersPath = path.join(searchDir, userSpecificFiles[0]);
          isUserSpecific = true;
          console.log('✅ Using most recent user-specific file:', userSpecificFiles[0]);
        } else if (fs.existsSync(mainAnswersPath)) {
          answersPath = mainAnswersPath;
          console.log('✅ Using main answers file:', mainAnswersPath);
        }

        if (answersPath && fs.existsSync(answersPath)) {
          const csvContent = fs.readFileSync(answersPath, 'utf-8');
          const lineCount = csvContent.split('\n').length;
          console.log('📊 Found answers file with', lineCount, 'lines');

          return NextResponse.json({
            exists: true,
            content: csvContent,
            message: 'Answers file found',
            filePath: answersPath,
            lineCount: lineCount,
            isUserSpecific: isUserSpecific,
            dataDir: searchDir,
            originalDataDir: originalDataDir,
            isServerless: isServerless,
            availableUserFiles: userSpecificFiles,
          });
        }
      } catch (dirError) {
        console.log(`❌ Error searching directory ${searchDir}:`, dirError);
        continue;
      }
    }

    // If no files found in any directory, return 404
    console.log('📄 No answers file found in any directory');
    return NextResponse.json(
      {
        exists: false,
        message: 'No answers file found in any directory',
        searchedDirectories: searchDirectories,
        isServerless: isServerless,
        cwd: process.cwd(),
      },
      { status: 404 },
    );
  } catch (error) {
    console.error('Error checking answers:', error);
    return NextResponse.json({ error: 'Failed to check answers' }, { status: 500 });
  }
}
