# 📜 Scripts Overview

All available automation scripts in this repository.

## 🤖 Complete AI Automation (GitHub Actions)

### `quick_automation.sh` ⚡ (Easiest)

Your exact command, but as a convenient script:

```bash
./quick_automation.sh
```

- ✅ Uses your current file setup
- ✅ Handles environment setup automatically
- ✅ Creates .env from template if needed

### `run_complete_automation.sh` 📋 (Default Setup)

Full automation with predefined files:

```bash
./run_complete_automation.sh
```

- 📋 Policy: `data/v5 Freya POL-11 Access Control.docx`
- 📊 Questionnaire: `data/questionnaire_responses.csv`
- 📝 Output: `secfix_with_authors`

### `run_custom_automation.sh` 🛠️ (Customizable)

Flexible automation with custom parameters:

```bash
./run_custom_automation.sh [policy] [questionnaire] [output_name]

# Examples:
./run_custom_automation.sh
./run_custom_automation.sh data/my_policy.docx
./run_custom_automation.sh data/my_policy.docx data/my_data.csv "custom_v1"
```

## 📂 Configuration Files

### `env.example` 🔑

Template for environment setup:

```bash
cp env.example .env
# Edit .env with your CLAUDE_API_KEY
```

### Example `.env` content:

```
CLAUDE_API_KEY=your_claude_api_key_here
GITHUB_TOKEN=your_github_token_here
```

## 🎯 Which Script Should I Use?

### For Complete AI Automation:

- **Just starting?** → `./quick_automation.sh`
- **Custom files?** → `./run_custom_automation.sh data/my_policy.docx data/my_data.csv`
- **Advanced control?** → Manual Python command

## 🔄 Workflow Comparison

| Script Type       | Speed      | Privacy   | Setup      | Use Case   |
| ----------------- | ---------- | --------- | ---------- | ---------- |
| **AI Automation** | 🐢 2-3 min | ☁️ GitHub | 🔑 API key | Production |
| **Quick Scripts** | 🐢 2-3 min | ☁️ GitHub | ✅ Minimal | Daily use  |

## 📖 Documentation

- **Complete setup**: `COMPLETE_AI_AUTOMATION.md`
- **Basic usage**: `README.md`

All scripts include built-in help: `./script_name.sh --help`
