# Policy Customization Request - JSON Output

I need you to analyze customer data and generate JSON-formatted customization instructions for a policy document.

## What I'm Providing:

- **Processing Instructions v3.8** (markdown file) - Contains all the rules and guidelines for generating JSON instructions
- **Customer Responses** (Excel/CSV file) - Contains the customer's answers to configuration questions
- **Policy Template** (document) - The base policy document that needs customization

## Your Task:

Read the processing instructions v3.8 to understand all customization rules and JSON output format requirements. Analyze the customer data to extract their responses and preferences. Generate a structured JSON file following the exact format specified in the processing instructions.

## CRITICAL Requirements:

**You must complete internal data validation before generating JSON:**

1. **Verify question count** matches form type expectations (SaaS=20, Professional Services=18)
2. **Extract ALL rule-relevant data** for the 12 customization rules (see processing instructions checklist)
3. **Follow JSON formatting requirements** - proper structure with metadata and operations array
4. **Include comment_author** field for all operations with "Secfix AI" as default

## Important Guidelines:

- Follow the processing instructions v3.8 exactly - use the specified JSON output format
- **Include detailed comments for all rules except company name, address, and logo** (which use "Replaced")
- Remove markdown asterisks from target_text and replacement fields (Word doesn't understand \*\* formatting)
- Provide exact "target_text" and "replacement" values for each operation
- Use appropriate action types: "replace", "delete", or "comment"
- Handle "Other" responses contextually using the guidelines provided
- Normalize multi-line addresses to single line format with commas when provided
- Extract tool names properly (remove parenthetical text like "(recommended)")
- Include company size context for termination timeframe when <50 employees

## Expected JSON Output:

Generate a complete JSON structure as specified in processing instructions v3.8, including:

```json
{
  "metadata": {
    "generated_timestamp": "[ISO timestamp]",
    "company_name": "[from CSV]",
    "format_version": "operations",
    "total_operations": [count],
    "generator": "PolicyWorkflow v2.0"
  },
  "instructions": {
    "operations": [
      {
        "target_text": "[exact text to find]",
        "action": "replace|delete|comment",
        "replacement": "[replacement text for replace action, empty string for delete/comment]",
        "comment": "[detailed reasoning for rules 4-12, 'Replaced' for rules 1-3]",
        "comment_author": "Secfix AI"
      }
    ]
  }
}
```

## Action Types:

- **"replace"**: Suggest text replacement with detailed comment explaining the change
- **"delete"**: Suggest text deletion with detailed comment explaining why
- **"comment"**: Add explanatory comment only (no text change needed)

## Comment Requirements:

- **For RULE_01, RULE_02, RULE_03**: Use "Replaced"
- **For RULE_04-RULE_12**: Format as "[Customer-specific context] [General business logic]"
- Reference what the customer indicated in their responses
- Explain the business principle (e.g., "No office = no guest network needed")

## Critical Processing Rules:

1. **Address Normalization**: Convert multi-line addresses to single line with commas
2. **"Other" Response Handling**: Interpret custom text contextually for each rule
3. **Company Size Context**: Include for termination timeframe when <50 employees
4. **Password Management Target Text**: Use `Password management systems should be user-friendly` to avoid duplicate matches
5. **Separate Exception/Violations Placeholders**: Use `<Exceptions: IT Manager>` and `<Violations: IT Manager>` as distinct targets
6. **Simplified Termination Timeframe**: Use `<24 business hours>` placeholder format
7. **NO ACTION REQUIRED Cases**: Use "comment" action with appropriate reasoning
8. **Tool Name Extraction**: Remove parenthetical text like "(recommended)" from tool names

**IMPORTANT**: Output ONLY the clean JSON structure. Do NOT include any internal validation results, processing details, or explanatory text outside the JSON. The response should start directly with the opening brace `{` and end with the closing brace `}`.

Please analyze the provided files and generate the JSON customization instructions following the processing instructions v3.8 format.
