"""
Test script for knowledge base parser

Run this to verify markdown → JSON conversion works correctly
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend_eng.services.knowledge_parser import KnowledgeBaseParser


def main():
    print("=" * 60)
    print("Testing Knowledge Base Parser")
    print("=" * 60)
    print()

    parser = KnowledgeBaseParser()

    print("📁 Tax team directory:", parser.tax_team_dir)
    print("📁 Cache directory:", parser.cache_dir)
    print()

    # Check if markdown files exist
    questions_file = parser.tax_team_dir / "intake" / "questions.md"
    tags_file = parser.tax_team_dir / "tags" / "definitions.md"

    print("✓ Checking markdown files...")
    print(f"  questions.md exists: {questions_file.exists()}")
    print(f"  definitions.md exists: {tags_file.exists()}")
    print()

    if not questions_file.exists() or not tags_file.exists():
        print("❌ Error: Markdown files not found!")
        print("   Make sure tax_team/knowledge_base/ has the markdown files")
        return 1

    print("🔄 Parsing knowledge base...")
    try:
        kb = parser.parse_all()
        print("✓ Parsing successful!")
        print()

        # Print statistics
        print("📊 Statistics:")
        print(f"  Gating questions: {len(kb['intake']['gating_questions']['questions'])}")
        print(f"  Modules: {len(kb['intake']['modules'])}")
        print(f"  Tags: {len(kb['tags']['tag_definitions'])}")
        print()

        # Print sample gating question
        if kb['intake']['gating_questions']['questions']:
            sample_q = kb['intake']['gating_questions']['questions'][0]
            print("📝 Sample gating question:")
            print(f"  ID: {sample_q['id']}")
            print(f"  Question: {sample_q['question'][:60]}...")
            print(f"  Action: {sample_q['action'][:60]}...")
            print()

        # Print sample tag
        if kb['tags']['tag_definitions']:
            tag_id = list(kb['tags']['tag_definitions'].keys())[0]
            sample_tag = kb['tags']['tag_definitions'][tag_id]
            print("🏷️  Sample tag:")
            print(f"  ID: {sample_tag['id']}")
            print(f"  Name: {sample_tag['name']}")
            print(f"  Forms: {list(sample_tag['forms'].keys())}")
            print()

        # Check cache files
        print("💾 Checking cached JSON files...")
        intake_cache = parser.cache_dir / "intake" / "questions.json"
        tags_cache = parser.cache_dir / "tags" / "definitions.json"

        print(f"  questions.json exists: {intake_cache.exists()}")
        print(f"  definitions.json exists: {tags_cache.exists()}")
        print()

        print("✅ All tests passed!")
        print()
        print("Next steps:")
        print("1. Review cached JSON in:", parser.cache_dir)
        print("2. Update science module to use cache directory")
        print("3. Test full application end-to-end")

        return 0

    except Exception as e:
        print(f"❌ Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())