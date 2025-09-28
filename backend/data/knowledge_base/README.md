# Tax Agent Knowledge Base

This directory contains structured data for the cross-border tax consultant AI agent.

## Directory Structure

```
knowledge_base/
├── scenarios/          # Tax scenarios and strategies
├── forms/             # Tax forms and their requirements
├── treaties/          # Tax treaty articles and interpretations
├── tax_codes/         # Tax code sections and regulations
├── regulations/       # Regulatory guidance and procedures
├── examples/          # Real-world examples and case studies
└── README.md          # This file
```

## Data Files

### scenarios/
- `US-Canada_Cross-Border_Tax_Scenarios_With_Strategies.csv` - Comprehensive US-Canada cross-border tax scenarios with strategies, forms, deadlines, and treaty references

## Usage

This knowledge base is designed to be accessed by the tax consultant AI to provide:
- Specific scenario-based guidance
- Form recommendations
- Treaty article references
- Deadline awareness
- Strategy suggestions

## Data Format

CSV files should maintain consistent column structures:
- ID: Unique identifier
- Category: Tax category/area
- Scenario: Description of the situation
- Strategy: Recommended approach
- Forms/Elections: Required tax forms
- Treaty Articles: Relevant treaty provisions
- Deadlines/Traps: Important timing considerations

## Adding New Data

When adding new data files:
1. Place them in the appropriate subdirectory
2. Use descriptive filenames
3. Maintain consistent data structure
4. Update this README if adding new categories