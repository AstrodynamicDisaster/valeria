import os
from core.valeria_agent import ValeriaAgent

def main():
    """Example usage"""
    import argparse
    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    parser = argparse.ArgumentParser(description="ValerIA AI Agent for Spanish Payroll Processing")
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY in .env file)")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")

    args = parser.parse_args()

    # Get API key from argument or environment variable
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ Error: OpenAI API key not found!")
        print("   Please either:")
        print("   1. Set OPENAI_API_KEY in your .env file")
        print("   2. Use --api-key argument")
        return

    agent = ValeriaAgent(api_key)

    if args.interactive:
        print("🤖 ValerIA Agent initialized. Type 'quit' to exit.")
        print("\n📋 I can help you with:")
        print("   • Import employee data from vida laboral CSV")
        print("   • Process payroll documents (nominas) from PDF files")
        print("   • Manage companies, employees, and payroll records")
        print("   • Generate reports and detect missing payslips")
        print("\n💡 Examples:")
        print("   - 'Show me all companies'")
        print("   - 'Import vida laboral from /path/to/file.csv'")
        print("   - 'Create a new company called ACME Corp'")
        print("   - 'List all employees for company X'")
        print("   - 'Show database statistics'")

        while True:
            user_input = input("\n👤 You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                break

            response = agent.run_conversation(user_input)
            print(f"\n🤖 ValerIA: {response}")
    else:
        print("Use --interactive for interactive mode")


if __name__ == "__main__":
    main()
