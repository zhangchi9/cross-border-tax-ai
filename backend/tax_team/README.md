# Tax Team Knowledge Base

## Owner
**Tax Domain Experts**

## Purpose
This directory contains all tax knowledge content in human-readable markdown format. No coding required - tax experts can directly edit these files to update the AI's knowledge base.

## Structure

```
tax_team/
├── knowledge_base/
│   ├── intake/
│   │   ├── questions.md        # Intake questions & modules
│   │   └── modules.md          # Module-specific questions
│   ├── tags/
│   │   └── definitions.md      # Tag definitions & forms mapping
│   ├── forms/
│   │   ├── us_forms.md         # US tax forms catalog
│   │   └── canada_forms.md     # Canadian tax forms catalog
│   └── scenarios/
│       └── cross_border_scenarios.md
└── templates/
    ├── intake_templates.md     # Response templates for intake
    └── analysis_templates.md   # Templates for analysis output
```

## How to Edit Content

### 1. Intake Questions (`intake/questions.md`)

```markdown
## Gating Questions

### Are you a U.S. citizen or U.S. green-card holder?
- **ID**: us_person_check
- **Action**: Go to Module A — Residency & Elections
- **Quick Replies**: Yes, No, Not sure

### For this tax year, are you a Canadian tax resident?
- **ID**: canadian_resident_check
- **Action**: Go to Module A — Residency & Elections
- **Quick Replies**: Yes, No, Not sure
```

### 2. Tag Definitions (`tags/definitions.md`)

```markdown
## us_person_worldwide_filing

**Name**: U.S. person (citizen/green-card holder) - worldwide U.S. filing

**Description**: You are a U.S. citizen or U.S. lawful permanent resident (green-card holder). The U.S. taxes you on worldwide income each year, regardless of where you live.

**Forms:**

### United States
- **Form 1040**: Annual U.S. individual income tax return reporting worldwide income
- **Form 1116**: Claim credit for income tax paid to Canada to mitigate double tax
- **Form 8938**: Report specified foreign financial assets if thresholds are met
- **FinCEN Form 114 (FBAR)**: Report non-U.S. financial accounts if aggregate balance exceeds USD $10,000

**Why**: U.S. persons must report worldwide income on Form 1040; Form 1116 prevents double taxation.
```

### 3. Forms Catalog (`forms/us_forms.md`)

```markdown
# United States Tax Forms

## Form 1040 - U.S. Individual Income Tax Return
- **Purpose**: Annual income tax return for U.S. taxpayers
- **Due Date**: April 15 (following tax year)
- **Who Files**: All U.S. citizens and residents
- **Extensions**: Form 4868 for 6-month extension

## Form 1116 - Foreign Tax Credit
- **Purpose**: Claim credit for foreign taxes paid
- **Due Date**: With Form 1040
- **Who Files**: U.S. persons with foreign income tax paid
- **Complexity**: High (separate by income category)
```

## Markdown Format Rules

### Required Fields

Every intake question must have:
- **ID**: Unique identifier (snake_case)
- **Question text**: Clear, conversational question
- **Action**: What happens when answered "yes"
- **Quick Replies**: Suggested response options

Every tag definition must have:
- **Name**: Human-readable tag name
- **Description**: Clear explanation of the tax situation
- **Forms**: List of forms by jurisdiction
- **Why**: Justification for the forms required

## Workflow

1. **Tax Expert Edits**: Update markdown files in this directory
2. **Backend Eng Parses**: Automated parser converts MD → JSON
3. **Science Team Consumes**: AI workflow reads parsed JSON
4. **Git Commit**: Changes are version controlled

## Best Practices

### Writing Questions
- ✅ Use conversational language
- ✅ Ask one thing at a time
- ✅ Provide clear quick reply options
- ❌ Avoid technical jargon
- ❌ Don't ask for sensitive data (SSN, SIN)

### Writing Descriptions
- ✅ Explain the "why" behind requirements
- ✅ Use plain English
- ✅ Include relevant deadlines
- ❌ Don't assume prior knowledge

### Organizing Forms
- ✅ Group by jurisdiction (US, Canada, State)
- ✅ Include due dates
- ✅ Note complexity level
- ✅ Link related forms

## Example Workflow

### Adding a New Tax Scenario

1. **Identify the scenario**: e.g., "US person retiring to Canada"

2. **Add gating question** (`intake/questions.md`):
```markdown
### Are you planning to retire in Canada?
- **ID**: retiring_to_canada
- **Action**: Go to Module — Retirement Planning
- **Quick Replies**: Yes, No, In the future
```

3. **Create tag** (`tags/definitions.md`):
```markdown
## us_retiree_to_canada

**Name**: U.S. retiree relocating to Canada

**Description**: U.S. citizen or green card holder planning retirement in Canada. Complex tax situation involving both countries' pension systems and tax treaties.

**Forms:**

### United States
- **Form 1040**: Continue filing as U.S. person
- **Form 8938**: Report Canadian financial accounts
- **Form 8621**: Report Canadian mutual funds (PFICs)

### Canada
- **T1 General**: Canadian tax return
- **T1135**: Foreign income verification
- **Schedule T2209**: Foreign tax credit

**Why**: Dual filing obligations, PFIC issues with Canadian investments, pension withholding taxes.
```

4. **Document forms** (`forms/` directory if needed)

5. **Commit changes**: Git commit with clear message

## Version Control

All changes are tracked in Git:
- **Who**: Changed author
- **When**: Commit timestamp
- **What**: Diff of markdown changes
- **Why**: Commit message

This allows:
- Rollback to previous versions
- Audit trail of knowledge updates
- Review process before deployment

## No Coding Required

❌ You do NOT need to:
- Write Python code
- Edit JSON files
- Understand LangGraph
- Configure AI models
- Deploy applications

✅ You only need to:
- Edit markdown files
- Follow the format templates
- Commit changes to Git
- Document your changes

## Support

**Questions about:**
- **Content/accuracy**: Tax team lead
- **Format/structure**: Backend eng team
- **AI behavior**: Science team

**Reporting issues:**
- Create GitHub issue with "tax-content" label
- Include affected file and suggested change
- Tag appropriate team member

## Future Enhancements

- [ ] Add validation tool for markdown format
- [ ] Create web UI for editing (no Git required)
- [ ] Add preview mode to test changes
- [ ] Integrate with tax law database
- [ ] Auto-generate forms catalog from IRS/CRA sources