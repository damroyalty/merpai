# 🤖 AI MERP - Advanced Conversational AI Chatbot

> A modern AI chatbot powered by **real language models** (Ollama), not templates. Runs completely locally and free.

## ✨ Features

- 🧠 **Real AI Understanding** - Powered by Mistral 7B or other open-source models
- 💬 **Genuine Conversations** - Context-aware responses that actually make sense
- 📚 **Learning System** - Remembers your name, interests, and emotional state
- 🎨 **Modern UI** - Glass morphism dark theme with real-time status
- 🔒 **100% Local** - No cloud, no tracking, completely private
- ⚡ **GPU Accelerated** - Uses your RTX 3060 for fast inference
- 🆓 **Completely Free** - No subscriptions or API costs

## 🚀 Quick Start

### Prerequisites
- Windows/Mac/Linux with Python 3.9+
- 8GB RAM minimum (16GB recommended for better models)
- NVIDIA GPU optional but recommended (you have RTX 3060 ✓)

### Step 1: Install Ollama
```bash
# Download from https://ollama.ai
# Install and run the installer
```

### Step 2: Download a Model
```bash
ollama pull mistral
# or: ollama pull neural-chat
```

### Step 3: Start Ollama (keep running in background)
```bash
ollama serve
```

### Step 4: Run Chatbot (in new terminal)
```bash
cd ai-project
.\venv\Scripts\activate
python main.py
```

## 📊 Example Conversations

### Before (Pattern Matching)
```
You: my girl cheated on me
Bot: New recipe or restaurant?  ❌ WRONG CONTEXT
```

### After (Real LLM)
```
You: my girl cheated on me
Bot: I'm really sorry to hear that. Betrayal is incredibly painful. 
     How are you holding up? Do you have people to talk to about this?  ✅ EMPATHETIC & CONTEXTUAL
```

## 🎯 Available Models

```bash
ollama pull mistral          # ⭐ Recommended - Fast & Quality (5GB)
ollama pull neural-chat      # Good for conversations (5GB)
ollama pull llama2           # Meta's model (4GB)
ollama pull dolphin-mixtral  # Most capable but slow (26GB)
```

## 🔧 Usage

### Change Model
Edit `main.py` or the ChatbotApp initialization:
```python
self.model = LLMChatbotModel(model_name="neural-chat")
```

### Adjust Response Style
In `src/ollama_model.py`, modify `temperature`:
```python
"temperature": 0.7,  # 0.1 = precise, 1.0 = creative
```

## 📁 Project Structure
```
ai-project/
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── OLLAMA_SETUP.md        # Detailed setup guide
├── run_chatbot.bat        # Quick start script
└── src/
    ├── gui.py             # Modern UI
    ├── ollama_model.py    # LLM chatbot engine
    └── merp_model.py      # Legacy pattern-matching (kept for reference)
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Ollama not connected" | Make sure `ollama serve` is running |
| Model not found | Run `ollama pull mistral` |
| Slow responses | Normal first run - GPU is loading model |
| Out of memory | Close other apps, try smaller model |

## 📖 Full Setup Guide

See [OLLAMA_SETUP.md](OLLAMA_SETUP.md) for detailed instructions and advanced configuration.

## 🎓 Learning More

- [Ollama Docs](https://github.com/ollama/ollama)
- [Model Library](https://ollama.ai/library)
- [Mistral 7B](https://mistral.ai)
- [How Language Models Work](https://karpathy.ai)

## 📝 What's Inside

### Core Features
- Real conversational AI using Ollama
- Context-aware responses
- User learning and preference tracking
- Conversation history
- Modern glass morphism UI with Tkinter

### How It Works
1. User sends message
2. Chat history + user preferences are sent to LLM
3. Ollama generates contextual response using GPU
4. Response appears in UI with proper formatting
5. Interaction is logged for learning

## 🔐 Privacy
100% local processing - nothing leaves your computer. All data stays on your machine.

## 📄 License
Open source - modify and use as you wish!

---

**Ready to chat with real AI? 🚀**

Make sure Ollama is running, then launch the chatbot!
