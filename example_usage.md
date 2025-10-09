# ValerIA Agent Usage Examples

## 🚀 Quick Start with .env File

1. **Create `.env` file:**
```bash
echo "OPENAI_API_KEY=your_actual_api_key" > .env
```

2. **Run interactive mode:**
```bash
python valeria_agent.py --interactive
```

## 💬 Example Conversation Flow

### Step 1: Start the Agent
```bash
$ python valeria_agent.py --interactive
🤖 ValerIA Agent initialized. Type 'quit' to exit.
📋 Start by providing a vida laboral CSV file, then nominas PDFs or ZIP files.

👤 You: Hello, I need to process payroll data
🤖 ValerIA: Hello! I'm ValerIA AI, your Spanish payroll processing assistant.

I'll guide you through processing your payroll documents in this order:
1️⃣ First: Vida laboral CSV file (employee data)
2️⃣ Then: Nominas PDFs or ZIP files (payslip data)
3️⃣ Finally: Generate processing reports

💡 **Next step**: Please provide the path to your vida laboral CSV file (e.g., `/path/to/vida_laboral.csv` or drag and drop the file path here)
```

### Step 2: Provide Vida Laboral CSV
```bash
👤 You: legacy/original_data/vl_ccc.csv
🤖 ValerIA: 🔍 Auto-detected vida laboral CSV: legacy/original_data/vl_ccc.csv
🔧 process_vida_laboral_csv: Successfully processed vida laboral for Client from vl_ccc

➡️  Please provide nominas PDF files or ZIP file paths
```

### Step 3: Provide Nominas Files
```bash
👤 You: I have PDFs in legacy/original_data/Nominas 2025/Febrero/*.pdf
🤖 ValerIA: 🔍 Auto-detected 1 PDF files
🔧 process_payslip_batch: Processed 0 payslips, 1 failed
🔧 generate_processing_report: Processing report generated successfully

✅ **Workflow Complete!** All files processed successfully.
💡 You can process more files or type 'quit' to exit.
```

## 📂 File Input Methods

### Method 1: Direct File Paths
```bash
👤 You: Process this file: /Users/albert/data/vida_laboral.csv
👤 You: Here are the nominas: /Users/albert/nominas/file1.pdf /Users/albert/nominas/file2.pdf
```

### Method 2: Quoted Paths (for paths with spaces)
```bash
👤 You: Please process "/Users/albert/My Documents/vida laboral.csv"
👤 You: Nominas are in "/Users/albert/Payroll Data/nominas.zip"
```

### Method 3: Relative Paths
```bash
👤 You: ./data/vida_laboral.csv
👤 You: ./nominas/*.pdf
```

### Method 4: Glob Patterns
```bash
👤 You: Process all PDFs: *.pdf
👤 You: All nominas in folder: ./nominas_2025/*.pdf
```

## 🔧 Programmatic Usage

```python
from valeria_agent import ValeriaAgent

# Initialize agent
agent = ValeriaAgent("your_openai_api_key")

# Process vida laboral
response1 = agent.run_conversation("legacy/original_data/vl_ccc.csv")
print(response1)

# Process nominas
response2 = agent.run_conversation("legacy/original_data/Nominas 2025/Febrero/*.pdf")
print(response2)

# Generate report
response3 = agent.run_conversation("generate a final report")
print(response3)
```

## ⚡ Key Features

### Auto-Detection
- **Automatic file type detection** - CSV, PDF, ZIP files
- **Path validation** - Checks if files exist
- **Workflow progression** - Moves to next step automatically

### Persistent Workflow
- **State tracking** - Remembers what's been processed
- **Error recovery** - Guides you to fix issues and retry
- **Step-by-step guidance** - Always shows what's needed next

### Flexible Input
- **Multiple formats** - Absolute paths, relative paths, quoted paths
- **Batch processing** - Multiple PDFs at once
- **ZIP extraction** - Automatically extracts and processes PDFs from ZIP files

## 🛠️ Troubleshooting

### "File not found" errors:
```bash
👤 You: /wrong/path/file.csv
🤖 ValerIA: ⚠️  Some files were not found:
  ❌ /wrong/path/file.csv

💡 Please check the file paths and try again.
```

### Workflow order issues:
The agent enforces the correct order:
1. ✅ Vida laboral CSV first
2. ✅ Then nominas PDFs/ZIP
3. ✅ Auto-generates reports

### API key issues:
```bash
❌ Error: OpenAI API key not found!
   Please either:
   1. Set OPENAI_API_KEY in your .env file
   2. Use --api-key argument
```