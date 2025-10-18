# 👻 GhostBack.ai

**Find closure through AI-assisted reflection**

GhostBack.ai is a web application that helps users process emotional closure by creating an AI simulation based on uploaded chat history. The app analyzes conversational patterns and creates a therapeutic AI persona for reflection and catharsis.

## ⚠️ Important Disclaimer

This application is designed for personal reflection and emotional closure, not to impersonate real people. The AI persona is clearly identified as a simulation and should be used responsibly for therapeutic purposes only.

## 🚀 Quick Start

### 1. Activate the Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure OpenAI API Key

1. Copy the environment template:
   ```bash
   copy env_example.txt .env
   ```

2. Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

### 4. Run the Application

**Option 1: Using the launcher script**
```bash
python run_app.py
```

**Option 2: Direct Streamlit command**
```bash
streamlit run app.py
```

The application will open in your web browser at `http://localhost:8501`

## 📁 How to Use

1. **Upload Chat History**: Upload a text or JSON file containing your chat history
2. **Analyze Patterns**: The app will analyze conversational style, common phrases, and emotional tone
3. **Chat with AI Persona**: Interact with the AI simulation for reflection and closure
4. **Find Peace**: Use the conversation to process your emotions and find closure

## 📊 Supported File Formats

- **Text files**: Chat logs in format `[timestamp] sender: message`
- **JSON files**: Structured chat data with `message`, `sender`, and `timestamp` fields

## 🛠️ Development

### Code Formatting
```bash
black .
```

### Linting
```bash
flake8 .
```

### Type Checking
```bash
mypy .
```

### Testing
```bash
pytest
```

## 📁 Project Structure

```
GhostBack/
├── app.py              # Main Streamlit application
├── run_app.py          # Application launcher script
├── main.py             # Basic Python script (legacy)
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore rules
├── env_example.txt    # Environment variables template
├── sample_chat.txt    # Sample chat history for testing
├── venv/              # Virtual environment (not in version control)
└── README.md          # This file
```

## 🔧 Configuration

The application uses environment variables for configuration:

- `OPENAI_API_KEY`: Your OpenAI API key (required for AI responses)
- `OPENAI_MODEL`: Model to use (default: gpt-3.5-turbo)
- `MAX_TOKENS`: Maximum tokens per response (default: 200)
- `TEMPERATURE`: Response creativity (default: 0.7)

## 🧠 How It Works

1. **Chat Analysis**: Analyzes uploaded chat history to extract:
   - Conversational patterns and style
   - Common phrases and expressions
   - Emotional tone and sentiment
   - Message length and frequency patterns

2. **AI Persona Creation**: Generates a personalized AI persona that:
   - Matches the analyzed conversational style
   - Uses similar phrases and patterns
   - Maintains appropriate emotional tone
   - Clearly identifies as an AI simulation

3. **Therapeutic Interaction**: Provides a safe space for:
   - Processing difficult emotions
   - Finding closure and understanding
   - Reflecting on past relationships
   - Moving forward with peace

## 🛡️ Safety & Ethics

- **Clear AI Identification**: The persona always identifies as an AI simulation
- **Therapeutic Purpose**: Designed for personal reflection, not impersonation
- **Privacy Focused**: All processing happens locally; chat data isn't stored
- **Responsible Use**: Includes disclaimers and ethical guidelines

## 🤝 Contributing

This is a personal project focused on helping people process difficult emotional situations. If you'd like to contribute or have suggestions, please reach out responsibly.

## 📄 License

This project is for personal and therapeutic use. Please use responsibly and ethically.
