# Policy Edit Automation

🤖 **Automate policy editing with AI** - Generate DOCX files with tracked changes you can accept/reject in Word or LibreOffice.

## 📊 How It Works

```text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Policy DOCX   │    │  Web Questionnaire │    │  Company Logo   │
│                 │    │   (13 questions)   │    │   (optional)    │
└─────────┬───────┘    └──────────┬───────────┘    └─────────┬───────┘
          │                       │                          │
          │                       ▼                          │
          │              ┌─────────────────┐                 │
          │              │  localStorage   │                 │
          │              │   (JSON data)   │                 │
          │              └─────────┬───────┘                 │
          │                       │                          │
          ▼                       ▼                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Claude AI Processing                          │
│          (ai_policy_processor.py + Claude Sonnet 4)             │
│   • Analyzes policy document                                    │
│   • Processes questionnaire responses                           │
│   • Detects [ADD COMPANY LOGO] placeholders                     │
│   • Generates intelligent edits                                 │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
                ┌─────────────────┐
                │   JSON Edits    │
                │  Instructions   │
                └─────────┬───────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│              LibreOffice Document Processing                     │
│             (apply_tracked_edits_libre.py)                      │
│   • Applies edits with tracked changes                          │
│   • Inserts company logo in placeholders                        │
│   • Maintains original formatting                               │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
                ┌─────────────────┐
                │   Final DOCX    │
                │ with Tracked    │
                │    Changes      │
                └─────────────────┘
```

**Key Benefits:**

- **Tracked Changes** - Review and accept/reject each edit individually
- **Logo Integration** - Automatically replaces `[ADD COMPANY LOGO]` placeholders
- **Smart AI** - Context-aware edits based on your company details
- **Professional Output** - Ready for legal/compliance review

## 🚀 Quick Start (3 Steps)

### 1. Setup API Key

```bash
cp env.example .env
# Edit .env and add your Claude API key:
# CLAUDE_API_KEY=sk-ant-your-key-here
```

### 2. Start the App

```bash
./start_app.sh
```

This starts both the backend and frontend, then opens your browser to <http://localhost:3000>

### 3. Use the Web Interface

1. **Fill out the questionnaire** (20 questions about your company/policy)
2. **Upload your company logo** (optional - converted to base64 automatically)
3. **Click "Start Automation"**
4. **Download the result** - your customized policy with tracked changes

That's it! 🎉

---

## 📋 What You Get

The system:

- **Analyzes your policy document** and questionnaire responses
- **Generates intelligent edits** using Claude AI
- **Creates a DOCX with tracked changes** that you can review and accept/reject
- **Automatically inserts your company logo** in placeholder locations
- **Supports multi-user environments** with automatic file isolation

## 🎯 Perfect For

- **Policy teams** updating access control, security, or compliance policies
- **Legal departments** customizing template policies for different entities
- **Consultants** generating client-specific policy documents
- **Organizations** maintaining consistent policy standards across teams

---

## 📁 What You Need

**Required:**

- Claude API key from [Anthropic](https://console.anthropic.com/)

**Included:**

- Sample policy document
- Default questionnaire with 20 common questions
- Example company logo

**Note:** Everything else (your policy, logo, responses) is handled through the web interface!

---

## ⚙️ Advanced Configuration

### Environment Variables

Only one environment variable is required for basic use:

```bash
# Required
CLAUDE_API_KEY=your_claude_api_key_here
```

For **production deployment only** (see DEPLOYMENT.md):

```bash
# Only needed for GitHub Actions and production deployment
GITHUB_REPO_OWNER=your_username
GITHUB_REPO_NAME=your_repo
GIT_USER_NAME=your_name
GIT_USER_EMAIL=your_email
GITHUB_TOKEN=your_github_token_here
```

### Command Line Alternative

If you prefer command line over web interface:

```bash
./quick_automation.sh
```

Note: Command line mode still uses legacy configuration files. The web interface is much simpler!

### Manual Setup

If `./start_app.sh` doesn't work, you can start services manually:

**Backend:**

```bash
cd web_ui
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

**Frontend:**

```bash
cd web_app
npm install
npm run dev
```

---

## 🏗️ Architecture

**Simple flow:**

```text
Web Questionnaire → AI Processing → DOCX with Tracked Changes
```

**Technical details:**

- **Frontend**: Next.js (React) dashboard
- **Backend**: Flask API with real-time logging
- **AI**: Claude Sonnet 4 for policy analysis
- **Document Processing**: LibreOffice for DOCX manipulation
- **Optional**: GitHub Actions for CI/CD workflows

---

## 📂 Project Structure

```text
├── start_app.sh              # 🚀 Main startup script
├── data/
│   ├── v5 Freya POL-11 Access Control.docx
│   ├── questions.csv
│   └── company_logo_default.png
├── web_app/                  # Next.js frontend
├── web_ui/                   # Flask backend
└── scripts/                  # Core automation scripts
```

---

## 🔧 Troubleshooting

**App won't start?**

- Check you have Python 3 and Node.js installed
- Run from the project root directory
- Make sure ports 3000 and 5001 are available

**API errors?**

- Verify your `CLAUDE_API_KEY` in `.env`
- Check you have API credits in your Anthropic account

**Can't generate DOCX?**

- Install LibreOffice: `brew install libreoffice` (Mac) or `apt install libreoffice` (Linux)

**Need help?**

- Check `DEPLOYMENT.md` for production setup
- Look at sample files in the `data/` directory
- Review the automation logs in the web interface

---

## 🚀 Production Deployment

For production deployment to platforms like Render, Railway, or Vercel, see [DEPLOYMENT.md](DEPLOYMENT.md) for complete instructions.

---

## 📄 Requirements

- **Python 3.8+** for automation scripts
- **Node.js 18+** for web interface
- **LibreOffice** for document processing
- **Claude API key** for AI processing
