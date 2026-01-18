import json
import os
import shutil
from datetime import datetime
from collections import defaultdict
import requests
try:
    from duckduckgo_search import DDGS
except Exception:
    DDGS = None
    print("⚠️ optional package 'duckduckgo_search' not found — web search will be limited")
import urllib.parse
import threading
import time

try:
    import appdirs
except Exception:
    appdirs = None


class LLMChatbotModel:
    """conversational ai using local LLM via Ollama"""

    def __init__(self, model_name="mistral", ollama_url="http://localhost:11434"):
        """initialize chatbot with local LLM.

        Args:
            model_name: Ollama model to use (mistral, llama2, neural-chat, etc.)
            ollama_url: URL where Ollama is running
        """
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.is_connected = False

        self.conversation_history = []
        self.user_data = {
            'name': None,
            'preferences': defaultdict(list),
            'topics_discussed': set(),
            'conversation_count': 0,
            'interests': [],
            'dislikes': [],
            'emotions_mentioned': [],
        }

        self._status_callbacks = []
        self._model_callbacks = []
        self.check_connection()
        self._init_data_dirs()

    def _init_data_dirs(self):
        """initialize data directory and migrate old 'data/' if present"""
        if appdirs:
            user_data_root = appdirs.user_data_dir("merp-ai", "merpai")
        else:
            user_data_root = os.path.join(os.getcwd(), "data")

        os.makedirs(user_data_root, exist_ok=True)
        self.data_dir = user_data_root

        local_data = os.path.join(os.getcwd(), "data")
        if os.path.exists(local_data) and os.path.abspath(local_data) != os.path.abspath(self.data_dir):
            try:
                for name in os.listdir(local_data):
                    src = os.path.join(local_data, name)
                    dst = os.path.join(self.data_dir, name)
                    if os.path.exists(dst):
                        if os.path.isdir(src) and os.path.isdir(dst):
                            for sub in os.listdir(src):
                                shutil.move(os.path.join(src, sub), os.path.join(dst, sub))
                        else:
                            shutil.move(src, dst)
                    else:
                        shutil.move(src, dst)
                try:
                    os.rmdir(local_data)
                except Exception:
                    pass
                print(f"✓ migrated existing ./data to {self.data_dir}")
            except Exception as e:
                print(f"⚠️ failed to migrate local data folder: {e}")

    def check_connection(self):
        """check if Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            self.is_connected = response.status_code == 200
            if self.is_connected:
                print(f"✓ connected to ollama at {self.ollama_url}")
                self._notify_status('connected', {'url': self.ollama_url})
            return self.is_connected
        except Exception as e:
            print(f"✗ could not connect to ollama: {e}")
            print(f"  make sure ollama is running (ollama serve)")
            was_connected = self.is_connected
            self.is_connected = False
            if was_connected:
                self._notify_status('disconnected', {'error': str(e)})
            return False

    def register_status_callback(self, callback):
        """register a callback for connection status changes.

        Callback signature: fn(event: str, data: dict)
        Events: 'connected', 'disconnected', 'health'
        """
        try:
            if callback not in self._status_callbacks:
                self._status_callbacks.append(callback)
                return True
        except Exception:
            pass
        return False

    def register_model_callback(self, callback):
        """register callbacks for model-related events.

        Callback signature: fn(event: str, data: dict)
        Events: 'model_switched'
        """
        try:
            if callback not in self._model_callbacks:
                self._model_callbacks.append(callback)
                return True
        except Exception:
            pass
        return False

    def _notify_status(self, event, data=None):
        data = data or {}
        for cb in list(self._status_callbacks):
            try:
                cb(event, data)
            except Exception:
                pass

    def _notify_model(self, event, data=None):
        data = data or {}
        for cb in list(self._model_callbacks):
            try:
                cb(event, data)
            except Exception:
                pass

    def start_health_monitor(self, poll_interval=5):
        """start a background thread to periodically check Ollama health."""
        def _monitor():
            last_connected = self.is_connected
            while True:
                try:
                    ok = self.check_connection()
                    try:
                        self._notify_status('health', {'connected': ok})
                    except Exception:
                        pass
                    last_connected = ok
                except Exception:
                    pass
                time.sleep(poll_interval)

        t = threading.Thread(target=_monitor, daemon=True)
        t.start()

    def get_available_models(self):
        """get list of available models from Ollama"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                return [m.get('name', m) for m in models]
            return []
        except:
            return []

    def switch_model(self, model_name):
        """switch to a different model"""
        self.model_name = model_name
        self._notify_model('model_switched', {'model': model_name})
        return True

    def search_web(self, query, num_results=5):
        """search the web using duckduckgo"""
        try:
            if DDGS is None:
                print("⚠️ duckduckgo_search not available — cannot perform web search")
                return []

            results = []
            ddgs = DDGS()
            search_results = ddgs.text(query, max_results=num_results)

            for result in search_results:
                results.append({
                    'title': result.get('title', 'No title'),
                    'link': result.get('href', '#'),
                    'description': result.get('body', 'No description'),
                })

            return results
        except Exception as e:
            print(f"Web search error: {e}")
            return []

    def should_search_web(self, user_input):
        """determine if user wants web search based on their input

        returns: tuple (should_search: bool, search_query: str)
        """
        search_keywords = [
            'search', 'find', 'look up', 'what is', 'who is', 'link to',
            'url', 'website', 'latest', 'current', 'recent', 'today',
            'news about', 'information about', 'tell me about', 'get me',
            'show me', 'help me find', 'where is', 'when is', 'how to',
            'tutorial', 'guide', 'documentation', 'research', 'learn about',
            'facts about', 'details about', 'background on', 'history of'
        ]

        user_lower = user_input.lower()

        for keyword in search_keywords:
            if keyword in user_lower:
                query = user_input
                for prefix in ['search ', 'find ', 'look up ', 'search for ']:
                    if query.lower().startswith(prefix):
                        query = query[len(prefix):]
                        break

                return True, query.strip()

        return False, ""

    def format_search_results(self, results, query):
        """format search results for display with clickable links"""
        if not results:
            return f"No results found for '{query}'. Try a different search term."

        formatted = f"🔍 Web Search Results for '{query}':\n{'─' * 70}\n"

        for i, result in enumerate(results, 1):
            formatted += f"\n{i}. {result['title']}\n"
            formatted += f"   🔗 {result['link']}\n"
            formatted += f"   {result['description']}\n"

        return formatted

    def create_resource_links(self, query):
        """create a set of useful resource/search links for a given query"""
        q = urllib.parse.quote_plus(query)
        google_search = f"https://www.google.com/search?q={q}"
        google_books = f"https://www.google.com/search?tbm=bks&q={q}"
        wikipedia = f"https://en.wikipedia.org/w/index.php?search={q}"
        scholar = f"https://scholar.google.com/scholar?q={q}"
        amazon = f"https://www.amazon.com/s?k={q}"

        response = f"Here are some helpful links for '{query}':\n{'─'*50}\n"
        response += f"\n🔗 Google search: {google_search}\n"
        response += f"\n🔗 Google Books: {google_books}\n"
        response += f"\n🔗 Wikipedia search: {wikipedia}\n"
        response += f"\n🔗 Google Scholar: {scholar}\n"
        response += f"\n🔗 Amazon search: {amazon}\n"
        response += f"\n\nIf you'd like direct article links, say 'search for: <topic>' or 'links for <topic>'."
        return response

    def extract_name(self, text):
        """extract name from text"""
        import re
        text_stripped = text.strip()

        patterns = [
            r"(?:my name is|i'm|i am|call me|it's|it is|change my name to|name me)\s+([A-Za-z]+)",
            r"(?:you can call me|name is|i go by|i'm called)\s+([A-Za-z]+)",
            r"^(?:it's|its?|i'm|i'm called)\s+([A-Za-z]+)$",
            r"(?:change my name to|just call me)\s+([A-Za-z]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).capitalize()

        if len(text_stripped) < 15 and ' ' not in text_stripped and text_stripped.isalpha():
            if not any(word in text.lower() for word in ['what', 'why', 'how', 'do', 'can', 'should', 'would', 'could', 'is', 'are', 'change', 'name', 'to']):
                return text_stripped.capitalize()

        return None

    def process_input(self, user_input):
        """process user input and generate response using LLM"""
        if not self.is_connected:
            return "⚠️ Ollama not connected. Please install Ollama and run: ollama serve"

        if not self.user_data['name']:
            name = self.extract_name(user_input)
            if name:
                self.user_data['name'] = name
                return f"Nice to meet you, {name}! I'm your AI companion. What would you like to talk about?"

        user_lower = user_input.lower()
        if 'link' in user_lower or 'links' in user_lower:
            query = user_input
            for prefix in ['send me a', 'send me', 'give me', 'show me', 'i want', 'i need', 'links for', 'link for', 'links to', 'link to']:
                if query.lower().startswith(prefix):
                    query = query[len(prefix):].strip()
                    break

            query = query.replace('google', '').replace('please', '').strip()

            if not query:
                response = (
                    "Here are some useful links:\n"
                    "\n🔗 https://www.google.com/\n"
                    "\n🔗 https://en.wikipedia.org/\n"
                    "\n🔗 https://scholar.google.com/\n"
                    "\nTell me the topic you want links for and I'll search specifically."
                )
                return response

            resource_text = self.create_resource_links(query)
            return resource_text

        should_search, search_query = self.should_search_web(user_input)

        if should_search and search_query:
            search_results = self.search_web(search_query, num_results=8)

            if search_results:
                formatted_results = self.format_search_results(search_results, search_query)

                context = self.build_context()
                analysis_prompt = self.create_prompt(
                    f"Based on these web search results for '{search_query}', provide a comprehensive analysis and answer. Include key findings, important links mentioned, and relevant information:\n\n{formatted_results}",
                    context
                )
                ai_analysis = self.get_ollama_response(analysis_prompt)

                response = f"{formatted_results}\n\n💭 Detailed Analysis:\n{ai_analysis}"

                self.learn_from_interaction(user_input, response)

                return response
            else:
                context = self.build_context()
                prompt = self.create_prompt(user_input, context)
                response = self.get_ollama_response(prompt)
                self.learn_from_interaction(user_input, response)
                return response

        context = self.build_context()

        prompt = self.create_prompt(user_input, context)
        
        # get response from Ollama
        response = self.get_ollama_response(prompt)

        # learn from the interaction
        self.learn_from_interaction(user_input, response)

        return response
    
    def build_context(self):
        """build conversation context from history"""
        context = "Conversation history:\n"
        
        # include recent messages for context
        recent_messages = self.conversation_history[-6:]  # Last 6 messages
        
        for msg in recent_messages:
            role = "User" if msg['role'] == 'user' else "Assistant"
            context += f"{role}: {msg['message']}\n"
        
        # add user information
        if self.user_data['name']:
            context += f"\nUser's name: {self.user_data['name']}\n"
        
        if self.user_data['interests']:
            context += f"User's interests: {', '.join(self.user_data['interests'])}\n"
        
        if self.user_data['dislikes']:
            context += f"User dislikes: {', '.join(self.user_data['dislikes'])}\n"
        
        if self.user_data['topics_discussed']:
            context += f"Topics discussed: {', '.join(self.user_data['topics_discussed'])}\n"
        
        return context
    
    def create_prompt(self, user_input, context):
        """create a smart prompt for the LLM"""
        name = self.user_data['name'] or "friend"

        interests_str = ", ".join(self.user_data['interests']) if self.user_data['interests'] else "not specified"
        dislikes_str = ", ".join(self.user_data['dislikes']) if self.user_data['dislikes'] else "not specified"

        # only include interests/dislikes details if they appear relevant to the current message/context
        def is_profile_relevant(text, ctx):
            combined = (text + " " + (ctx or "")).lower()
            # check explicit interest/dislike keywords
            for item in self.user_data.get('interests', []) or []:
                if item and item.lower() in combined:
                    return True
            for item in self.user_data.get('dislikes', []) or []:
                if item and item.lower() in combined:
                    return True
            # check topics discussed
            for t in self.user_data.get('topics_discussed', []) or []:
                if t and t.lower() in combined:
                    return True
            return False

        profile_relevant = is_profile_relevant(user_input, context)

        header = "You are a friendly, conversational AI."
        name_line = f"- Name: {name}\n"

        if profile_relevant:
            profile_lines = (
                f"- Interests: {interests_str}\n"
                f"- Dislikes: {dislikes_str}\n\n"
                "Use their interests in conversation when relevant. Avoid discussing their dislikes. Be personal and reference what you know about them.\n\n"
            )
        else:
            profile_lines = (
                "Only use the user's interests and dislikes if they are directly relevant to the user's current question or topic.\n\n"
            )

        system_prompt = f"""{header}
{name_line}{profile_lines}
{context}

User: {user_input}
Assistant:"""

        return system_prompt
    
    def get_ollama_response(self, prompt):
        """get response from Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.5,
                    "top_p": 0.9,
                    "num_predict": 80
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('response', '').strip()
                if text:
                    return text
                return "hm, let me think about that..."
            else:
                return "having trouble thinking right now, try again."
                
        except requests.exceptions.Timeout:
            return "taking a moment... try again."
        except Exception as e:
            print(f"Error getting Ollama response: {e}")
            return "got an error, try again."
    
    def learn_from_interaction(self, user_input, response):
        """extract and store learning data from interaction"""
        text_lower = user_input.lower()
        
        # detect sentiment/emotions
        negative_words = ['sad', 'angry', 'frustrated', 'depressed', 'lonely', 'hurt', 'heartbreak', 'bad']
        positive_words = ['happy', 'great', 'awesome', 'love', 'excellent', 'wonderful']
        
        if any(word in text_lower for word in negative_words):
            self.user_data['emotions_mentioned'].append({
                'type': 'negative',
                'timestamp': datetime.now()
            })
        elif any(word in text_lower for word in positive_words):
            self.user_data['emotions_mentioned'].append({
                'type': 'positive',
                'timestamp': datetime.now()
            })
        
        # store preferences
        self.user_data['preferences'][user_input] = {
            'response': response,
            'timestamp': datetime.now()
        }
    
    def add_to_history(self, role, message):
        """add message to conversation history"""
        self.conversation_history.append({
            'role': role,
            'message': message,
            'timestamp': datetime.now()
        })
    
    def get_user_data(self):
        """get current user data"""
        return self.user_data
    
    def get_learning_summary(self):
        """get what the ai has learned"""
        summary = {
            'name': self.user_data['name'],
            'topics': list(self.user_data['topics_discussed']),
            'emotions': len(self.user_data['emotions_mentioned']),
            'model': self.model_name,
            'connected': self.is_connected
        }
        return summary
    
    def save_conversation(self, filepath):
        """save conversation history"""
        try:
            # ensure parent dir exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump({
                    'history': [
                        {
                            'role': msg['role'],
                            'message': msg['message'],
                            'timestamp': msg['timestamp'].isoformat()
                        }
                        for msg in self.conversation_history
                    ],
                    'user_data': {
                        'name': self.user_data['name'],
                        'topics_discussed': list(self.user_data['topics_discussed']),
                        'emotions_mentioned': len(self.user_data['emotions_mentioned'])
                    }
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving conversation: {e}")
    
    def load_conversation(self, filepath):
        """load previous conversation"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    # could restore history here if desired
                    return True
        except Exception as e:
            print(f"Error loading conversation: {e}")
        return False
    
    def save_current_conversation(self):
        """save current conversation to conversations folder"""
        try:
            conversations_dir = os.path.join(self.data_dir, "conversations")
            os.makedirs(conversations_dir, exist_ok=True)
            
            # generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(conversations_dir, f"conversation_{timestamp}.json")
            
            conversation_data = {
                'timestamp': datetime.now().isoformat(),
                'user_name': self.user_data['name'] or 'Anonymous',
                'message_count': len(self.conversation_history),
                'messages': [
                    {
                        'role': msg['role'],
                        'message': msg['message'],
                        'timestamp': msg['timestamp'].isoformat()
                    }
                    for msg in self.conversation_history
                ]
            }
            
            with open(filename, 'w') as f:
                json.dump(conversation_data, f, indent=2)
            print(f"✓ conversation saved to {filename}")
            return filename
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return None
    
    def get_conversation_list(self):
        """get list of all saved conversations"""
        try:
            conversations_dir = os.path.join(self.data_dir, "conversations")
            if not os.path.exists(conversations_dir):
                return []
            
            conversations = []
            for filename in sorted(os.listdir(conversations_dir), reverse=True):
                if filename.endswith('.json'):
                    filepath = os.path.join(conversations_dir, filename)
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        conversations.append({
                            'filename': filename,
                            'filepath': filepath,
                            'timestamp': data.get('timestamp'),
                            'user_name': data.get('user_name', 'Anonymous'),
                            'title': data.get('title', None),
                            'message_count': data.get('message_count', 0)
                        })
            return conversations
        except Exception as e:
            print(f"Error loading conversation list: {e}")
            return []
    
    def load_conversation_by_file(self, filepath):
        """load a specific conversation from file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    self.conversation_history = [
                        {
                            'role': msg['role'],
                            'message': msg['message'],
                            'timestamp': datetime.fromisoformat(msg['timestamp'])
                        }
                        for msg in data.get('messages', [])
                    ]
                    return True
        except Exception as e:
            print(f"Error loading conversation: {e}")
        return False

    def rename_conversation(self, filepath, title):
        """rename or add a title to a saved conversation file"""
        try:
            if not os.path.exists(filepath):
                return False
            with open(filepath, 'r') as f:
                data = json.load(f)

            data['title'] = title

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            print(f"Error renaming conversation: {e}")
            return False
    
    def save_user_data(self):
        """save user data to JSON file"""
        try:
            user_data_file = os.path.join(self.data_dir, "user_data.json")
            os.makedirs(os.path.dirname(user_data_file), exist_ok=True)
            
            data_to_save = {
                'name': self.user_data['name'],
                'interests': self.user_data['interests'],
                'dislikes': self.user_data['dislikes'],
                'topics_discussed': list(self.user_data['topics_discussed']),
            }
            
            with open(user_data_file, 'w') as f:
                json.dump(data_to_save, f, indent=2)
            print(f"✓ user data saved")
        except Exception as e:
            print(f"Error saving user data: {e}")
    
    def load_user_data(self):
        """load user data from JSON file"""
        try:
            user_data_file = os.path.join(self.data_dir, "user_data.json")
            if os.path.exists(user_data_file):
                with open(user_data_file, 'r') as f:
                    data = json.load(f)
                    self.user_data['name'] = data.get('name')
                    self.user_data['interests'] = data.get('interests', [])
                    self.user_data['dislikes'] = data.get('dislikes', [])
                    self.user_data['topics_discussed'] = set(data.get('topics_discussed', []))
                print(f"✓ user data loaded")
                return True
        except Exception as e:
            print(f"Error loading user data: {e}")
        return False
