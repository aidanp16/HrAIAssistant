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
- [x] LangGraph workflow nodes
- [x] Individual content generation tools
- [x] Streamlit frontend
- [x] Session persistence
- [x] Testing and documentation

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/aidanp16/HrAIAssistant.git
   cd HrAIAssistant
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and add your OpenAI API key:
   # OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Run the application:**
   ```bash
   streamlit run src/app.py
   ```

6. **Open your browser:**
   The app will automatically open at `http://localhost:8501`

## 💡 Usage Examples

### Basic Usage

1. **Start a conversation:**
   - "I need to hire a founding engineer and a GenAI intern"
   - "Help me hire a senior frontend developer for my SaaS startup"
   - "I need a product manager and marketing specialist"

2. **Answer follow-up questions:**
   - Company size and funding stage
   - Budget ranges and timeline
   - Specific skills and requirements

3. **Get comprehensive materials:**
   - Job descriptions tailored for startups
   - Actionable hiring checklists
   - Realistic hiring timelines
   - Market-based salary recommendations
   - Role-specific interview questions

### Advanced Features

- **Session Management:** Save, load, and manage multiple hiring plans
- **File Downloads:** Export all generated materials as markdown files
- **Progress Tracking:** Visual progress through the hiring planning process
- **Multi-Role Support:** Handle multiple positions in a single conversation

## 🏗️ Architecture Deep Dive

### LangGraph Workflow

The application uses a sophisticated LangGraph workflow:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Initial         │────│ Question         │────│ Response        │
│ Analysis        │    │ Generation       │    │ Processing      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Content         │────│ Content          │────│ Completion      │
│ Coordination    │    │ Generation       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Component Overview

- **State Management (`src/state.py`):** TypedDict-based state with comprehensive tracking
- **Workflow Nodes (`src/nodes.py`):** GPT-powered analysis, question generation, and routing
- **Content Tools (`tools/`):** Individual generators for each content type
- **Session Management (`src/session_manager.py`):** File-based persistence with cleanup
- **Streamlit Frontend (`src/app.py`):** Professional web interface with chat-style interaction

### Content Generation Tools

 Each tool is independently testable and generates startup-focused content:

- `job_description.py` - Compelling job descriptions with equity focus
- `hiring_checklist.py` - Comprehensive checklists for startup hiring
- `hiring_timeline.py` - Realistic timelines considering market conditions
- `salary_recommendation.py` - Market-rate analysis with startup adjustments
- `interview_questions.py` - Role-specific questions emphasizing startup fit

## 🧪 Testing

### Manual Testing Scenarios

1. **Single Role Hiring:**
   ```
   Input: "I need to hire a senior React developer"
   Expected: Questions about company, budget, timeline
   Result: 5 comprehensive documents for the role
   ```

2. **Multi-Role Hiring:**
   ```
   Input: "I need a founding engineer and GenAI intern"
   Expected: Role-specific questions for each position
   Result: 10 documents total (5 per role)
   ```

3. **Session Persistence:**
   ```
   Test: Start conversation, close browser, reopen
   Expected: Session loads with all previous context
   Result: Conversation continues seamlessly
   ```

### Tool Testing

Run individual tools for testing:

```bash
# Test job description generator
cd tools
python job_description.py

# Test other tools similarly
python hiring_checklist.py
python hiring_timeline.py
python salary_recommendation.py
python interview_questions.py
```

## 🔧 Configuration

### Environment Variables

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
APP_NAME=HR Assistant
DEBUG=False
SESSION_TIMEOUT=3600
```

### Customization

- **Prompts:** Modify templates in `config/prompts.py`
- **Styling:** Adjust Streamlit styling in `src/app.py`
- **Workflow:** Customize routing logic in `src/workflow.py`
- **Content:** Extend tools in `tools/` directory

## 📁 Project Structure

```
hr_assistant/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── state.py             # State management with TypedDict
│   ├── nodes.py             # LangGraph workflow nodes
│   ├── workflow.py          # Main workflow orchestrator
│   ├── session_manager.py   # Session persistence
│   └── app.py              # Streamlit frontend
├── tools/                   # Individual content generators
│   ├── __init__.py
│   ├── job_description.py
│   ├── hiring_checklist.py
│   ├── hiring_timeline.py
│   ├── salary_recommendation.py
│   └── interview_questions.py
├── config/
│   └── prompts.py          # GPT prompt templates
├── output/                 # Generated markdown files
├── sessions/               # Session persistence storage
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🚨 Troubleshooting

### Common Issues

1. **OpenAI API Key Error:**
   ```
   Error: OpenAI API key not found
   Solution: Check .env file and API key validity
   ```

2. **Import Errors:**
   ```
   Error: Module not found
   Solution: Ensure virtual environment is activated
   ```

3. **Session Loading Issues:**
   ```
   Error: Failed to load session
   Solution: Check sessions/ directory permissions
   ```

4. **Content Generation Timeout:**
   ```
   Error: Request timeout
   Solution: Check internet connection and API limits
   ```

### Debug Mode

Enable debug logging:
```bash
DEBUG=True streamlit run src/app.py
```

## 🎯 Key Features Demonstrated

✅ **Multi-step reasoning** - GPT analyzes needs, asks follow-ups, makes decisions  
✅ **LangGraph orchestration** - Complex workflow with conditional routing  
✅ **Session persistence** - File-based state management across sessions  
✅ **Modular tools** - Individual content generators as separate modules  
✅ **Professional UI** - Clean Streamlit interface with advanced features  
✅ **Startup focus** - All content tailored for startup hiring challenges  
✅ **Error handling** - Comprehensive error handling and fallbacks  
✅ **File export** - All content saved as downloadable markdown files  

## 🤝 Contributing

This project was built as part of a technical challenge demonstrating:
- Advanced AI workflow orchestration
- Production-ready application architecture
- User-centered design principles
- Comprehensive documentation

Contributions and feedback are welcome!

## 📄 License

MIT License - see LICENSE file for details

---

*Built with ❤️ for startup hiring efficiency*
