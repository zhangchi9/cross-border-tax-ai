"""
Interactive Terminal Chat for Tax Consultation Intake Agent

A standalone script for chatting with the intake agent in the terminal.
Provides a clean interface with color coding, progress tracking, and session management.

Usage:
    python chat_interactive.py
    python chat_interactive.py --model openai
    python chat_interactive.py --session my-session-id

Commands during chat:
    /quit       - Exit the chat
    /state      - Show current state summary
    /tags       - Show assigned tags with confidence
    /force      - Force transition to forms analysis
    /save       - Save conversation to file
    /clear      - Clear screen
    /help       - Show all commands
"""

import asyncio
import sys
import os
import json
import argparse
from datetime import datetime
from typing import Optional, Dict, Any

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from science.agents.workflow import TaxConsultationWorkflow
from science.config import science_config


# ============================================================================
# COLOR UTILITIES (ANSI Colors)
# ============================================================================

class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'


def colored(text: str, color: str = Colors.RESET, bold: bool = False) -> str:
    """Apply color to text"""
    prefix = Colors.BOLD if bold else ''
    return f"{prefix}{color}{text}{Colors.RESET}"


def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


# ============================================================================
# DISPLAY UTILITIES
# ============================================================================

def print_banner():
    """Print welcome banner"""
    clear_screen()
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              🏛️  CROSS-BORDER TAX CONSULTATION ASSISTANT  🏛️                 ║
║                                                                              ║
║                         Interactive Terminal Chat                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(colored(banner, Colors.BRIGHT_CYAN, bold=True))
    print(colored(f"AI Model: {science_config.AI_MODEL_PROVIDER} ({science_config.OPENAI_MODEL if science_config.AI_MODEL_PROVIDER == 'openai' else science_config.GEMINI_MODEL})", Colors.BRIGHT_BLACK))
    print(colored("Type /help for available commands\n", Colors.BRIGHT_BLACK))


def print_separator(char: str = "─", length: int = 80):
    """Print a separator line"""
    print(colored(char * length, Colors.BRIGHT_BLACK))


def print_user_message(message: str):
    """Print user message with formatting"""
    print(colored("\n👤 You:", Colors.BRIGHT_GREEN, bold=True))
    print(colored(f"   {message}", Colors.GREEN))


def print_assistant_message(message: str, quick_replies: list = None):
    """Print assistant message with formatting"""
    print(colored("\n🤖 Assistant:", Colors.BRIGHT_BLUE, bold=True))

    # Split message into lines and indent
    lines = message.split('\n')
    for line in lines:
        print(colored(f"   {line}", Colors.BLUE))

    # Print quick replies if available
    if quick_replies:
        print(colored("\n   Quick Replies:", Colors.BRIGHT_CYAN))
        for i, reply in enumerate(quick_replies, 1):
            print(colored(f"     {i}. {reply}", Colors.CYAN))


def print_progress(state: Dict[str, Any]):
    """Print progress indicators"""
    tags_count = len(state.get('assigned_tags', []))
    tags = state.get('assigned_tags', [])
    turns = state.get('conversation_turns', 0)
    phase = state.get('current_phase', 'intake')

    print(colored("\n   📊 Progress:", Colors.BRIGHT_BLACK))
    print(colored(f"      Phase: {phase.upper()}", Colors.BRIGHT_BLACK))
    print(colored(f"      Tags Assigned: {tags_count}", Colors.BRIGHT_BLACK))

    # Display list of tags
    if tags:
        tags_display = ", ".join(tags)
        print(colored(f"      Tags: {tags_display}", Colors.BRIGHT_BLACK))
    else:
        print(colored(f"      Tags: (none yet)", Colors.BRIGHT_BLACK))

    print(colored(f"      Conversation Turns: {turns}", Colors.BRIGHT_BLACK))


def print_state_summary(state: Dict[str, Any]):
    """Print detailed state summary"""
    print_separator("═")
    print(colored("📋 CURRENT STATE SUMMARY", Colors.BRIGHT_YELLOW, bold=True))
    print_separator("═")

    # Basic info
    print(colored(f"\n🔹 Phase:", Colors.BRIGHT_WHITE, bold=True), state.get('current_phase', 'N/A'))
    print(colored(f"🔹 Session ID:", Colors.BRIGHT_WHITE, bold=True), state.get('session_id', 'N/A'))
    print(colored(f"🔹 Conversation Turns:", Colors.BRIGHT_WHITE, bold=True), state.get('conversation_turns', 0))

    # Tags
    tags = state.get('assigned_tags', [])
    print(colored(f"\n🏷️  Assigned Tags ({len(tags)}):", Colors.BRIGHT_WHITE, bold=True))
    if tags:
        for tag in tags:
            confidence = state.get('tag_confidence', {}).get(tag, 'unknown')
            confidence_color = Colors.GREEN if confidence == 'high' else Colors.YELLOW if confidence == 'medium' else Colors.RED
            print(colored(f"   • {tag}", Colors.WHITE), colored(f"[{confidence}]", confidence_color))
    else:
        print(colored("   (none)", Colors.BRIGHT_BLACK))

    # Extracted facts (Phase 3)
    facts = state.get('extracted_facts', [])
    if facts:
        print(colored(f"\n💡 Extracted Facts ({len(facts)}):", Colors.BRIGHT_WHITE, bold=True))
        for fact in facts[:5]:  # Show first 5
            print(colored(f"   • {fact.get('fact', 'N/A')}", Colors.WHITE))
            print(colored(f"     Confidence: {fact.get('confidence', 'N/A')}", Colors.BRIGHT_BLACK))
        if len(facts) > 5:
            print(colored(f"   ... and {len(facts) - 5} more", Colors.BRIGHT_BLACK))

    # Transition readiness
    should_transition = state.get('should_transition', False)
    transition_color = Colors.BRIGHT_GREEN if should_transition else Colors.BRIGHT_BLACK
    print(colored(f"\n🚦 Ready to Transition:", Colors.BRIGHT_WHITE, bold=True), colored(str(should_transition), transition_color))

    if state.get('transition_reason'):
        print(colored(f"   Reason: {state.get('transition_reason')}", Colors.BRIGHT_BLACK))

    print_separator("═")


def print_tags_summary(state: Dict[str, Any]):
    """Print detailed tags with reasoning"""
    print_separator("═")
    print(colored("🏷️  TAG ASSIGNMENT DETAILS", Colors.BRIGHT_YELLOW, bold=True))
    print_separator("═")

    tags = state.get('assigned_tags', [])
    if not tags:
        print(colored("\nNo tags assigned yet.", Colors.BRIGHT_BLACK))
        print_separator("═")
        return

    tag_reasoning = state.get('tag_assignment_reasoning', {})
    tag_confidence = state.get('tag_confidence', {})

    for i, tag in enumerate(tags, 1):
        print(colored(f"\n{i}. {tag}", Colors.BRIGHT_CYAN, bold=True))

        confidence = tag_confidence.get(tag, 'unknown')
        confidence_color = Colors.GREEN if confidence == 'high' else Colors.YELLOW if confidence == 'medium' else Colors.RED
        print(colored(f"   Confidence: ", Colors.WHITE), colored(confidence.upper(), confidence_color))

        reasoning = tag_reasoning.get(tag, {})
        if reasoning:
            if reasoning.get('method'):
                print(colored(f"   Method: {reasoning.get('method')}", Colors.BRIGHT_BLACK))
            if reasoning.get('reasoning'):
                print(colored(f"   Reasoning: {reasoning.get('reasoning')}", Colors.BRIGHT_BLACK))

    print_separator("═")


def print_forms_analysis(state: Dict[str, Any]):
    """Print forms analysis results"""
    print_separator("═")
    print(colored("📄 FORMS ANALYSIS RESULTS", Colors.BRIGHT_YELLOW, bold=True))
    print_separator("═")

    complexity = state.get('estimated_complexity', 'N/A')
    if complexity and complexity != 'N/A':
        print(colored(f"\n📊 Complexity: {complexity.upper()}", Colors.BRIGHT_WHITE, bold=True))
    else:
        print(colored(f"\n📊 Complexity: N/A", Colors.BRIGHT_WHITE, bold=True))

    forms = state.get('required_forms', [])
    print(colored(f"\n📋 Required Forms ({len(forms)}):", Colors.BRIGHT_WHITE, bold=True))
    if forms:
        for form in forms:
            print(colored(f"\n   {form.get('form', 'N/A')} - {form.get('jurisdiction', 'N/A')}", Colors.BRIGHT_CYAN, bold=True))
            print(colored(f"   Priority: {form.get('priority', 'N/A')}", Colors.WHITE))
            if form.get('due_date'):
                print(colored(f"   Due Date: {form.get('due_date')}", Colors.YELLOW))
            if form.get('description'):
                print(colored(f"   Description: {form.get('description')}", Colors.BRIGHT_BLACK))
    else:
        print(colored("   (none)", Colors.BRIGHT_BLACK))

    # Recommendations
    recommendations = state.get('recommendations', [])
    if recommendations:
        print(colored(f"\n💡 Recommendations:", Colors.BRIGHT_WHITE, bold=True))
        for rec in recommendations:
            print(colored(f"   • {rec}", Colors.WHITE))

    # Next steps
    next_steps = state.get('next_steps', [])
    if next_steps:
        print(colored(f"\n🔜 Next Steps:", Colors.BRIGHT_WHITE, bold=True))
        for step in next_steps:
            print(colored(f"   • {step}", Colors.WHITE))

    print_separator("═")


def print_help():
    """Print help information"""
    print_separator("═")
    print(colored("❓ AVAILABLE COMMANDS", Colors.BRIGHT_YELLOW, bold=True))
    print_separator("═")

    commands = [
        ("/quit", "Exit the chat session"),
        ("/state", "Show current state summary (tags, phase, progress)"),
        ("/tags", "Show detailed tag assignments with reasoning"),
        ("/force", "Force transition to forms analysis phase"),
        ("/save", "Save conversation to a JSON file"),
        ("/clear", "Clear the terminal screen"),
        ("/help", "Show this help message"),
    ]

    print()
    for cmd, desc in commands:
        print(colored(f"   {cmd:<12}", Colors.BRIGHT_CYAN, bold=True), colored(desc, Colors.WHITE))

    print(colored("\nTips:", Colors.BRIGHT_YELLOW, bold=True))
    print(colored("   • The assistant will ask questions to understand your tax situation", Colors.BRIGHT_BLACK))
    print(colored("   • Answer naturally - the AI will extract relevant information", Colors.BRIGHT_BLACK))
    print(colored("   • Use quick reply numbers (e.g., '1', '2') for faster responses", Colors.BRIGHT_BLACK))
    print(colored("   • The conversation will automatically transition to forms analysis when ready", Colors.BRIGHT_BLACK))

    print_separator("═")


def print_error(message: str):
    """Print error message"""
    print(colored(f"\n❌ Error: {message}", Colors.BRIGHT_RED, bold=True))


def print_success(message: str):
    """Print success message"""
    print(colored(f"\n✅ {message}", Colors.BRIGHT_GREEN, bold=True))


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def save_session_to_file(state: Dict[str, Any], session_id: str):
    """Save conversation session to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"session_{session_id}_{timestamp}.json"
    filepath = os.path.join("chat_sessions", filename)

    # Create directory if not exists
    os.makedirs("chat_sessions", exist_ok=True)

    # Save to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, default=str)

    return filepath


# ============================================================================
# MAIN CHAT LOGIC
# ============================================================================

async def interactive_chat(session_id: Optional[str] = None):
    """Main interactive chat loop"""

    # Print welcome banner
    print_banner()

    # Initialize workflow
    workflow = TaxConsultationWorkflow()

    # Generate session ID if not provided
    if session_id is None:
        session_id = "interactive_" + datetime.now().strftime("%Y%m%d_%H%M%S")

    print(colored(f"Session ID: {session_id}", Colors.BRIGHT_BLACK))
    print(colored("Starting conversation...\n", Colors.BRIGHT_BLACK))
    print_separator()

    # Get initial message
    print(colored("\n💬 Start by describing your tax situation, or just say 'hi'", Colors.BRIGHT_YELLOW))
    user_input = input(colored("\n👤 You: ", Colors.BRIGHT_GREEN, bold=True)).strip()

    if not user_input or user_input.lower() in ['quit', '/quit']:
        print(colored("\nGoodbye! 👋", Colors.BRIGHT_CYAN))
        return

    # Start consultation
    try:
        result = await workflow.start_consultation(user_input, session_id=session_id)
        print_assistant_message(result.get('assistant_response', ''), result.get('quick_replies', []))
        print_progress(result)

    except Exception as e:
        print_error(f"Failed to start consultation: {str(e)}")
        return

    # Main conversation loop
    while True:
        print_separator()

        # Get user input
        user_input = input(colored("\n👤 You: ", Colors.BRIGHT_GREEN, bold=True)).strip()

        if not user_input:
            continue

        # Handle commands
        if user_input.startswith('/'):
            command = user_input.lower()

            if command == '/quit':
                print(colored("\n👋 Ending conversation. Goodbye!", Colors.BRIGHT_CYAN))
                break

            elif command == '/help':
                print_help()
                continue

            elif command == '/clear':
                clear_screen()
                print_banner()
                continue

            elif command == '/state':
                print_state_summary(result)
                continue

            elif command == '/tags':
                print_tags_summary(result)
                continue

            elif command == '/force':
                print(colored("\n⚡ Forcing transition to forms analysis...", Colors.BRIGHT_YELLOW))
                try:
                    result = await workflow.force_transition_to_forms_analysis(session_id)
                    print_assistant_message(result.get('message', result.get('assistant_response', '')))
                    print_forms_analysis(result)
                    print_success("Forms analysis completed!")
                    break
                except Exception as e:
                    print_error(f"Failed to force transition: {str(e)}")
                continue

            elif command == '/save':
                try:
                    filepath = save_session_to_file(result, session_id)
                    print_success(f"Session saved to: {filepath}")
                except Exception as e:
                    print_error(f"Failed to save session: {str(e)}")
                continue

            else:
                print_error(f"Unknown command: {user_input}")
                print(colored("Type /help for available commands", Colors.BRIGHT_BLACK))
                continue

        # Process user message
        try:
            result = await workflow.continue_consultation(session_id, user_input)
            print_assistant_message(result.get('assistant_response', ''), result.get('quick_replies', []))
            print_progress(result)

            # Check if forms analysis is complete (completed phase with forms data)
            if result.get('current_phase') == 'completed' and result.get('required_forms'):
                print(colored("\n🎉 Forms analysis complete!", Colors.BRIGHT_GREEN, bold=True))
                print_forms_analysis(result)
                print_success("Analysis completed!")

                # Ask if user wants to save
                save_input = input(colored("\n💾 Save this session? (y/n): ", Colors.BRIGHT_YELLOW)).strip().lower()
                if save_input == 'y':
                    try:
                        filepath = save_session_to_file(result, session_id)
                        print_success(f"Session saved to: {filepath}")
                    except Exception as e:
                        print_error(f"Failed to save session: {str(e)}")

                break

            # Check if completed without forms (shouldn't normally happen)
            elif result.get('current_phase') == 'completed':
                print(colored("\n✅ Consultation completed!", Colors.BRIGHT_GREEN, bold=True))
                break

        except Exception as e:
            print_error(f"Error processing message: {str(e)}")
            print(colored("Please try again or type /quit to exit", Colors.BRIGHT_BLACK))


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Interactive chat with the tax consultation intake agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chat_interactive.py
  python chat_interactive.py --session my-session
  python chat_interactive.py --model openai
        """
    )

    parser.add_argument(
        '--session',
        type=str,
        default=None,
        help='Session ID to use (auto-generated if not provided)'
    )

    parser.add_argument(
        '--model',
        type=str,
        choices=['openai', 'gemini'],
        default=None,
        help='AI model provider to use (overrides config)'
    )

    args = parser.parse_args()

    # Override model if specified
    if args.model:
        science_config.AI_MODEL_PROVIDER = args.model

    # Run interactive chat
    try:
        asyncio.run(interactive_chat(session_id=args.session))
    except KeyboardInterrupt:
        print(colored("\n\n👋 Chat interrupted. Goodbye!", Colors.BRIGHT_CYAN))
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    main()
