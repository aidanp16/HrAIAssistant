# HR Assistant - Agentic AI Hiring Planner 🤖

An intelligent HR assistant that helps startups plan their hiring process using LangGraph and GPT. Simply describe your hiring needs, and the assistant will guide you through creating comprehensive hiring materials.

## 🚀 Features

- **Intelligent Question Generation**: GPT-powered contextual questions to gather hiring requirements
- **Multi-Role Support**: Handle multiple positions in a single conversation
- **Comprehensive Content Generation**:
  - Job descriptions tailored for startups
  - Hiring checklists with actionable items
  - Realistic hiring timelines
  - Market-based salary recommendations
  - Role-specific interview questions
- **Session Persistence**: Maintains conversation context across sessions
- **Streamlit Frontend**: User-friendly web interface
- **LangGraph Orchestration**: Sophisticated workflow management

## 🏗️ Architecture

The application uses **LangGraph** to orchestrate a multi-step workflow:

```
User Input → GPT Analysis → Question Generation → Context Gathering → Content Generation → Output Files
```

### Key Components

- **State Management**: Persistent conversation state tracking
- **GPT-Powered Nodes**: Intelligent analysis and question generation
- **Modular Tools**: Individual content generators for each deliverable type
- **Conditional Routing**: Smart decision making for workflow progression

## 🛠️ Tech Stack

- **LangGraph**: Workflow orchestration
- **OpenAI GPT**: Content generation and analysis
- **Streamlit**: Web interface
- **Python**: Core application logic
- **TypedDict**: State schema management

## 📁 Project Structure

```
hr_assistant/
├── src/                 # Core application logic
├── tools/               # Individual content generation tools
├── config/              # Prompt templates and configuration
├── output/              # Generated markdown files
├── sessions/            # Session persistence storage
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/[username]/hr-assistant.git
cd hr-assistant
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

5. Run the application:
```bash
streamlit run src/app.py
```

## 💡 Usage Examples

**Input**: "I need to hire a founding engineer and a GenAI intern. Can you help?"

**The assistant will**:
- Extract the job roles (Founding Engineer, GenAI Intern)
- Ask clarifying questions about company size, budget, timeline
- Generate comprehensive hiring materials for each role

## 🔧 Development Status

- [x] Project structure and dependencies
- [x] State management system
- [x] Prompt templates
- [ ] LangGraph workflow nodes
- [ ] Individual content generation tools
- [ ] Streamlit frontend
- [ ] Session persistence
- [ ] Testing and documentation

## 🤝 Contributing

This project is part of a coding challenge. Contributions and feedback are welcome!

## 📄 License

MIT License - see LICENSE file for details

---

*Built with ❤️ for startup hiring efficiency*
