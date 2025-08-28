# Policy Customization Request - JSON Output

I need you to analyze customer data and generate JSON-formatted customization instructions for a policy document.

## What I'm Providing:

- **Processing Instructions** (markdown file) - Contains all the rules and guidelines for generating JSON instructions with universal AI-powered grammar analysis
- **Customer Responses** (Excel/CSV file) - Contains the customer's answers to configuration questions
- **Policy Template** (document) - The base policy document that needs customization

## Your Task:

Read the processing instructions to understand all customization rules and JSON output format requirements. Analyze the customer data to extract their responses and preferences. Generate a structured JSON file following the exact format specified in the processing instructions.

## CRITICAL Requirements:

**Complete all validation and processing steps as specified in the processing instructions before generating JSON.**

## Important Guidelines:

- **Follow the processing instructions exactly** - use the specified JSON output format and action types defined in the instructions
- **Follow all rules and guidelines** as specified in the processing instructions document
- Remove markdown asterisks from target_text and replacement fields (Word doesn't understand \*\* formatting)
- Handle "Other" responses contextually using the guidelines provided in the instructions
- **CRITICAL: target_text must EXACTLY match text from the policy document** - NEVER invent or make up target_text that doesn't exist
- **🧠 UNIVERSAL AI DECISION: For EVERY rule, AI must analyze full sentence context**
- **Scenario A: IF user response fits grammatically → target_text = placeholder**
- **Scenario B: IF sentence needs restructuring → target_text = full sentence + restructured replacement**
- **This applies to ALL rules (RULE_01 through RULE_12), not just complex ones**
- **CRITICAL: When user response matches current document text, use "comment" action** - do NOT use "replace" or "smart_replace" to avoid duplication
- **CRITICAL: Follow the exact JSON structure and field requirements** specified in the processing instructions

## Expected JSON Output:

Generate a complete JSON structure **exactly as specified in the processing instructions**. The structure, field names, action types, and formatting requirements are all defined in the processing instructions document.

## Processing Requirements:

Follow all comment requirements, processing rules, and guidelines **exactly as specified in the processing instructions document**. This includes:

- Comment formatting and content requirements
- Address normalization rules
- "Other" response handling
- Company size context requirements
- Target text accuracy requirements
- Placeholder removal requirements
- Action type selection criteria
- All other processing rules defined in the instructions

**IMPORTANT**: Output ONLY the clean JSON structure. Do NOT include any internal validation results, processing details, or explanatory text outside the JSON. The response should start directly with the opening brace `{` and end with the closing brace `}`.

Please analyze the provided files and generate the JSON customization instructions following the processing instructions format.
