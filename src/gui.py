import customtkinter as ctk
import webbrowser
import re
import os
import tkinter as tk
from src.merpai_model import LLMChatbotModel

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ModernStyle:
    """ dark theme colors and styling"""
    BG_PRIMARY = "#0a0e27"
    BG_SECONDARY = "#1a1f3a"
    BG_TERTIARY = "#252d47"
    BG_HOVER = "#2d3557"

    TEXT_PRIMARY = "#e0e6ff"
    TEXT_SECONDARY = "#a0aec0"

    ACCENT_CYAN = "#00d9ff"
    ACCENT_PURPLE = "#b366ff"
    ACCENT_GREEN = "#00ff88"

    FONT_TITLE = ("Segoe UI", 20, "bold")
    FONT_LARGE = ("Segoe UI", 13, "bold")
    FONT_NORMAL = ("Segoe UI", 11)
    FONT_SMALL = ("Segoe UI", 10)


class ChatbotApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("merpai")
        self.geometry("1200x900")
        self.minsize(900, 700)

        try:
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            media_dir = os.path.join(root_dir, "media")
            icon_ico = os.path.join(media_dir, "icon.ico")

            preferred_names = ["cat-4x.png", "icon.png"]
            ico_pref = os.path.join(media_dir, "cat-4x.ico")
            if os.path.exists(ico_pref):
                try:
                    self.iconbitmap(ico_pref)
                except Exception:
                    pass

            icon_png = None
            for name in preferred_names:
                p = os.path.join(media_dir, name)
                if os.path.exists(p):
                    icon_png = p
                    break
            if icon_png is None and os.path.isdir(media_dir):
                for f in os.listdir(media_dir):
                    if f.lower().endswith('.png'):
                        icon_png = os.path.join(media_dir, f)
                        break

            if icon_png and os.path.exists(icon_png):
                try:
                    img = tk.PhotoImage(file=icon_png)
                    self.iconphoto(False, img)
                except Exception:
                    pass

            self._icon_png = icon_png if icon_png and os.path.exists(icon_png) else None
            self._icon_ico = ico_pref if os.path.exists(ico_pref) else (icon_ico if os.path.exists(icon_ico) else None)

            if os.path.exists(icon_ico):
                try:
                    self.iconbitmap(icon_ico)
                except Exception:
                    pass
        except Exception:
            pass

        self.configure(fg_color=ModernStyle.BG_PRIMARY)

        self.model = LLMChatbotModel(model_name="mistral")
        self.model.load_user_data()
        self.link_count = 0

        self.setup_ui()
        try:
            self.model.register_status_callback(self._on_model_status_event)
            self.model.register_model_callback(self._on_model_event)
            self.model.start_health_monitor(poll_interval=5)
        except Exception:
            pass
        self.show_welcome()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """save user data and current conversation, then close app"""
        if self.model.conversation_history:
            self.model.save_current_conversation()
        self.model.save_user_data()
        self.destroy()

    def setup_ui(self):
        """setup the modern user interface"""
        main_frame = ctk.CTkFrame(self, fg_color=ModernStyle.BG_PRIMARY)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        try:
            if getattr(self, '_icon_png', None):
                try:
                    img = tk.PhotoImage(file=self._icon_png)
                    try:
                        w = img.width()
                        h = img.height()
                        max_dim = 32
                        if w > max_dim or h > max_dim:
                            subsample = max(1, int(max(w, h) // max_dim))
                            img = img.subsample(subsample, subsample)
                    except Exception:
                        pass
                    self._title_icon_img = img
                    ctk.CTkLabel(header_frame, image=self._title_icon_img, text="").pack(side="left", padx=(0, 8))
                except Exception:
                    pass
        except Exception:
            pass

        title_label = ctk.CTkLabel(
            header_frame, text="merpai",
            font=("Segoe UI", 24, "bold"),
            text_color=ModernStyle.ACCENT_CYAN
        )
        title_label.pack(side="left", padx=(0, 15))

        status_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        status_frame.pack(side="right")

        self.status_indicator = ctk.CTkLabel(
            status_frame, text="●",
            font=("Arial", 16, "bold"),
            text_color=ModernStyle.ACCENT_GREEN
        )
        self.status_indicator.pack(side="left", padx=(0, 8))

        self.status_label = ctk.CTkLabel(
            status_frame, text="ready",
            font=("Segoe UI", 11),
            text_color=ModernStyle.ACCENT_GREEN
        )
        self.status_label.pack(side="left")

        divider = ctk.CTkFrame(main_frame, height=1, fg_color=ModernStyle.BG_SECONDARY)
        divider.pack(fill="x", pady=(0, 15))

        chat_label = ctk.CTkLabel(
            main_frame, text="💬 conversation",
            font=("Segoe UI", 13, "bold"),
            text_color=ModernStyle.ACCENT_CYAN
        )
        chat_label.pack(anchor="w", pady=(0, 8))

        self.chat_display = ctk.CTkTextbox(
            main_frame,
            wrap="word",
            font=ModernStyle.FONT_NORMAL,
            fg_color=ModernStyle.BG_TERTIARY,
            text_color=ModernStyle.TEXT_PRIMARY,
            border_color=ModernStyle.BG_SECONDARY,
            border_width=2,
            corner_radius=10
        )
        self.chat_display.pack(fill="both", expand=True, pady=(0, 18))
        self.chat_display.configure(state="disabled")

        self.chat_display.tag_config("user", foreground=ModernStyle.ACCENT_CYAN)
        self.chat_display.tag_config("bot", foreground=ModernStyle.ACCENT_GREEN)
        self.chat_display.tag_config("system", foreground=ModernStyle.ACCENT_PURPLE)

        input_label = ctk.CTkLabel(
            main_frame, text="✉️ message",
            font=("Segoe UI", 13, "bold"),
            text_color=ModernStyle.ACCENT_CYAN
        )
        input_label.pack(anchor="w", pady=(0, 8))

        input_frame = ctk.CTkFrame(main_frame, fg_color=ModernStyle.BG_SECONDARY, corner_radius=10)
        input_frame.pack(fill="x", pady=(0, 15))

        self.input_field = ctk.CTkEntry(
            input_frame,
            placeholder_text="type your message here...",
            font=ModernStyle.FONT_NORMAL,
            fg_color=ModernStyle.BG_TERTIARY,
            text_color=ModernStyle.TEXT_PRIMARY,
            placeholder_text_color=ModernStyle.TEXT_SECONDARY,
            border_color=ModernStyle.BG_SECONDARY,
            border_width=0,
            corner_radius=8
        )
        self.input_field.pack(fill="x", side="left", expand=True, padx=12, pady=12)
        self.input_field.bind("<Return>", lambda e: self.send_message())

        self.send_btn = ctk.CTkButton(
            input_frame, text="send",
            command=self.send_message,
            font=("Segoe UI", 11, "bold"),
            fg_color=ModernStyle.ACCENT_CYAN,
            text_color=ModernStyle.BG_PRIMARY,
            hover_color=ModernStyle.ACCENT_PURPLE,
            corner_radius=8,
            width=100
        )
        self.send_btn.pack(side="left", padx=(0, 12), pady=12)

        control_label = ctk.CTkLabel(
            main_frame, text="tools",
            font=("Segoe UI", 10, "bold"),
            text_color=ModernStyle.TEXT_SECONDARY
        )
        control_label.pack(anchor="w", pady=(8, 6))

        control_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        control_frame.pack(fill="x")

        button_config = {
            "font": ("Segoe UI", 10, "bold"),
            "fg_color": ModernStyle.BG_SECONDARY,
            "text_color": ModernStyle.ACCENT_CYAN,
            "hover_color": ModernStyle.BG_TERTIARY,
            "corner_radius": 8,
            "height": 35
        }

        ctk.CTkButton(control_frame, text="🤖 model", command=self.show_model_selector, **button_config).pack(side="left", padx=(0, 10))
        ctk.CTkButton(control_frame, text="👤 profile", command=self.show_profile_editor, **button_config).pack(side="left", padx=(0, 10))
        ctk.CTkButton(control_frame, text="💬 conversations", command=self.show_conversations, **button_config).pack(side="left", padx=(0, 10))
        ctk.CTkButton(control_frame, text="🆕 new convo", command=self.new_conversation, **button_config).pack(side="left", padx=(0, 10))
        ctk.CTkButton(control_frame, text="🗑️ clear", command=self.clear_chat, **button_config).pack(side="left", padx=(0, 10))
        ctk.CTkButton(control_frame, text="ℹ️ info", command=self.show_info, **button_config).pack(side="left", padx=(0, 10))
        ctk.CTkButton(control_frame, text="⚙️ current settings", command=self.show_settings, **button_config).pack(side="left")

        self.input_field.focus()
        self.debug_visible = False
        self.debug_frame = ctk.CTkFrame(self, fg_color=ModernStyle.BG_TERTIARY, corner_radius=8, width=360, height=180)
        dbg_header = ctk.CTkFrame(self.debug_frame, fg_color="transparent")
        dbg_header.pack(fill="x", padx=8, pady=(6, 0))
        self.debug_title = ctk.CTkLabel(dbg_header, text="status", font=ModernStyle.FONT_SMALL, text_color=ModernStyle.TEXT_SECONDARY)
        self.debug_title.pack(side="left")
        self.debug_clear_btn = ctk.CTkButton(dbg_header, text="✕", width=28, height=24, command=lambda: self.clear_debug(), fg_color=ModernStyle.BG_SECONDARY, text_color=ModernStyle.ACCENT_CYAN, corner_radius=6)
        self.debug_clear_btn.pack(side="right", padx=(0, 6))
        self.debug_toggle_btn = ctk.CTkButton(dbg_header, text="▾", width=28, height=24, command=self.toggle_debug_panel, fg_color=ModernStyle.BG_SECONDARY, text_color=ModernStyle.ACCENT_CYAN, corner_radius=6)
        self.debug_toggle_btn.pack(side="right")
        self.debug_popout_btn = ctk.CTkButton(dbg_header, text="⇱", width=28, height=24, command=self.popout_debug_panel, fg_color=ModernStyle.BG_SECONDARY, text_color=ModernStyle.ACCENT_CYAN, corner_radius=6)
        self.debug_popout_btn.pack(side="right", padx=(6, 0))
        self.debug_expand_btn = ctk.CTkButton(dbg_header, text="⤢", width=28, height=24, command=self.toggle_debug_expand, fg_color=ModernStyle.BG_SECONDARY, text_color=ModernStyle.ACCENT_CYAN, corner_radius=6)
        self.debug_expand_btn.pack(side="right", padx=(6, 0))

        self.debug_text = ctk.CTkTextbox(self.debug_frame, width=360, height=180, fg_color=ModernStyle.BG_PRIMARY, text_color=ModernStyle.TEXT_PRIMARY, corner_radius=6)
        self.debug_text.pack(fill="both", expand=True, padx=8, pady=6)
        self.debug_text.configure(state="disabled")
        self.debug_frame.place_forget()
        self.debug_window = None
        self.debug_expanded = False
        self.debug_open_btn = ctk.CTkButton(self, text="status", width=90, height=28, command=self.toggle_debug_panel, fg_color=ModernStyle.BG_SECONDARY, text_color=ModernStyle.ACCENT_CYAN, corner_radius=8)
        self.debug_open_btn.place(relx=0.995, rely=0.995, anchor="se")

    def show_welcome(self):
        """show welcome message"""
        self.add_system_message("━" * 70)
        if self.model.is_connected:
            user_data = self.model.get_user_data()
            if user_data['name']:
                self.add_bot_message(f"welcome back, {user_data['name']}! how can i help?")
            else:
                self.add_bot_message("hi .-. What's your name?")
        else:
            self.add_bot_message("⚠️ Ollama is not running!")
            self.add_bot_message("Please install Ollama from https://ollama.ai and run: ollama serve")
            self.add_bot_message("Then pull a model: ollama pull mistral")
        try:
            self.append_debug(f"ollama_connected={self.model.is_connected}")
            self.append_debug(f"model={self.model.model_name}")
        except Exception:
            pass
        self.add_system_message("━" * 70)
        
    def add_user_message(self, message):
        """add user message to chat display"""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", "you: ", "user")
        self.chat_display.insert("end", message + "\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
        
    def add_bot_message(self, message):
        """add bot message to chat display with clickable links"""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", "merp: ", "bot")
        url_regex = r"https?://[^\s)]+"
        parts = re.split(f'({url_regex})', message)
        for part in parts:
            if not part:
                continue
            if re.match(url_regex, part):
                url = part
                tag = f"link_{self.link_count}"
                self.link_count += 1
                self.chat_display.insert("end", url, tag)
                self.chat_display.tag_config(tag, foreground=ModernStyle.ACCENT_CYAN, underline=True)
                self.chat_display.tag_bind(tag, "<Button-1>", lambda e, u=url: webbrowser.open(u))
            else:
                self.chat_display.insert("end", part.lower())

        self.chat_display.insert("end", "\n\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
        
    def add_system_message(self, message):
        """add system message to chat display"""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", message + "\n", "system")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
        
    def send_message(self):
        """send user message and get bot response"""
        user_message = self.input_field.get().strip()

        if not user_message:
            return

        self.status_indicator.configure(text_color=ModernStyle.ACCENT_PURPLE)
        self.status_label.configure(text="processing...")
        self.update()
        try:
            self.append_debug(f"sending: {user_message}")
        except Exception:
            pass

        self.add_user_message(user_message)
        self.model.add_to_history('user', user_message)

        response = self.model.process_input(user_message)
        try:
            self.append_debug(f"response_len={len(response)}")
        except Exception:
            pass
        self.add_bot_message(response)
        self.model.add_to_history('bot', response)

        user_data = self.model.get_user_data()
        if user_data['name']:
            name_display = f"{user_data['name']}"
            self.status_indicator.configure(text_color=ModernStyle.ACCENT_GREEN)
        else:
            name_display = "anonymous"
            self.status_indicator.configure(text_color=ModernStyle.ACCENT_CYAN)

        self.status_label.configure(text=f"ready • {name_display}")

        self.input_field.delete(0, "end")
        self.input_field.focus()
        
    def clear_chat(self):
        """clear chat history"""
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self.model.conversation_history = []
        self.show_welcome()
        self.input_field.focus()

    def new_conversation(self):
        """save the current conversation and start a new one"""
        if self.model.conversation_history:
            saved_path = self.model.save_current_conversation()
            if saved_path:
                self.add_system_message(f"✓ saved previous conversation: {saved_path}")
            else:
                self.add_system_message("✗ failed to save previous conversation")
        else:
            self.add_system_message("ℹ️ no messages to save")

        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self.model.conversation_history = []

        self.show_welcome()
        self.input_field.focus()
        
    def show_info(self):
        """show conversation info and AI learning"""
        user_data = self.model.get_user_data()

        topics = ', '.join(user_data['topics_discussed']) if user_data['topics_discussed'] else 'None yet'

        info = f"\n📊 conversation insights\n{'─' * 50}\n"
        info += f"👤 user: {user_data['name'] or 'not provided'}\n"
        info += f"💬 messages: {len(self.model.conversation_history)}\n"
        info += f"🎯 topics discussed: {topics}\n"

        if user_data.get('interests'):
            info += f"⭐ interests: {', '.join(user_data['interests'][:3])}\n"
        if user_data.get('dislikes'):
            info += f"❌ dislikes: {', '.join(user_data['dislikes'][:2])}\n"

        if user_data.get('emotions_mentioned'):
            emotions_count = len(user_data['emotions_mentioned'])
            info += f"😊 emotional moments recorded: {emotions_count}\n"

        info += f"{'─' * 50}\n"

        try:
            info_win = ctk.CTkToplevel(self)
            info_win.title("conversation info")
            info_win.geometry("560x420")
            info_win.configure(fg_color=ModernStyle.BG_PRIMARY)
            info_win.transient(self)
            info_win.grab_set()

            mainf = ctk.CTkFrame(info_win, fg_color=ModernStyle.BG_PRIMARY)
            mainf.pack(fill="both", expand=True, padx=16, pady=12)

            textbox = ctk.CTkTextbox(mainf, fg_color=ModernStyle.BG_TERTIARY, text_color=ModernStyle.TEXT_PRIMARY, corner_radius=8)
            textbox.pack(fill="both", expand=True, pady=(0,12))
            textbox.configure(state="normal")
            textbox.insert("end", info)
            textbox.configure(state="disabled")

            btnf = ctk.CTkFrame(mainf, fg_color="transparent")
            btnf.pack(fill="x")
            ctk.CTkButton(btnf, text="close", command=info_win.destroy, fg_color=ModernStyle.BG_SECONDARY, text_color=ModernStyle.ACCENT_CYAN, corner_radius=8).pack(side="right")
        except Exception:
            self.add_system_message(info)
        
    def show_settings(self):
        """show settings (placeholder for future features)"""
        settings_info = f"\n⚙️ settings\n{'─' * 50}\n"
        settings_info += "theme: dark mode (modern custom)\n"
        settings_info += "language: english\n"
        settings_info += "model: real conversational ai\n"
        settings_info += f"{'─' * 50}\n"
        # show data directory path
        data_dir = getattr(self.model, 'data_dir', os.path.join(os.getcwd(), 'data'))
        settings_info += f"data dir: {data_dir}\n"

        # show settings in a modal popup instead of chat
        try:
            set_win = ctk.CTkToplevel(self)
            set_win.title("settings")
            set_win.geometry("520x360")
            set_win.configure(fg_color=ModernStyle.BG_PRIMARY)
            set_win.transient(self)
            set_win.grab_set()

            mainf = ctk.CTkFrame(set_win, fg_color=ModernStyle.BG_PRIMARY)
            mainf.pack(fill="both", expand=True, padx=12, pady=12)

            textbox = ctk.CTkTextbox(mainf, fg_color=ModernStyle.BG_TERTIARY, text_color=ModernStyle.TEXT_PRIMARY, corner_radius=8)
            textbox.pack(fill="both", expand=True, pady=(0,12))
            textbox.configure(state="normal")
            textbox.insert("end", settings_info)
            textbox.configure(state="disabled")

            btnf = ctk.CTkFrame(mainf, fg_color="transparent")
            btnf.pack(fill="x")
            ctk.CTkButton(btnf, text="open data folder", command=lambda: os.startfile(data_dir), font=("Segoe UI", 10, "bold"), fg_color=ModernStyle.BG_SECONDARY, text_color=ModernStyle.ACCENT_CYAN, corner_radius=8).pack(side="left")
            ctk.CTkButton(btnf, text="close", command=set_win.destroy, fg_color=ModernStyle.BG_SECONDARY, text_color=ModernStyle.ACCENT_CYAN, corner_radius=8).pack(side="right")
        except Exception:
            # fallback to chat if popup fails
            self.add_system_message(settings_info)

    # =================== debug / status helpers ===================
    def toggle_debug_panel(self):
        """show/hide the lower-right debug/status panel"""
        # toggle visibility, try to place/show the docked panel, or hide it if visible
        try:
            if getattr(self, 'debug_visible', False):
                # hide panel, show open button
                try:
                    self.debug_frame.place_forget()
                except Exception as e:
                    print(f"toggle_debug_panel: error hiding debug_frame: {e}")
                try:
                    self.debug_open_btn.place(relx=0.995, rely=0.995, anchor="se")
                except Exception as e:
                    print(f"toggle_debug_panel: error placing open_btn: {e}")
                self.debug_visible = False
                try:
                    self.debug_toggle_btn.configure(text="▾")
                except Exception:
                    pass
            else:
                # attempt to show the panel
                try:
                    # ensure desired size is configured on the frame, then place it
                    try:
                        self.debug_frame.configure(width=360, height=180)
                    except Exception:
                        pass
                    self.debug_frame.place(relx=0.995, rely=0.995, anchor="se")
                    try:
                        self.debug_frame.lift()
                    except Exception:
                        try:
                            self.debug_frame.tkraise()
                        except Exception:
                            pass
                    # hide the open button now that the panel is visible
                    try:
                        self.debug_open_btn.place_forget()
                    except Exception as e:
                        print(f"toggle_debug_panel: error hiding open_btn after show: {e}")
                    self.debug_visible = True
                    try:
                        self.debug_toggle_btn.configure(text="▴")
                    except Exception:
                        pass
                except Exception as e:
                    # failed to place the panel — keep open button visible and print error
                    print(f"toggle_debug_panel: error showing debug_frame: {e}")
                    try:
                        self.debug_open_btn.place(relx=0.995, rely=0.995, anchor="se")
                    except Exception:
                        pass
        except Exception as e:
            print(f"toggle_debug_panel: unexpected error: {e}")

    def toggle_debug_expand(self):
        """toggle between compact and expanded sizes for the docked debug panel"""
        try:
            if getattr(self, 'debug_expanded', False):
                # shrink back to docked taller size
                try:
                    self.debug_frame.configure(width=360, height=180)
                except Exception:
                    pass
                self.debug_expanded = False
                self.debug_expand_btn.configure(text="⤢")
            else:
                # expand to a larger, taller size
                try:
                    self.debug_frame.configure(width=720, height=420)
                except Exception:
                    pass
                self.debug_expanded = True
                self.debug_expand_btn.configure(text="⤡")
        except Exception:
            pass

    def popout_debug_panel(self):
        """detach the debug panel into a separate movable, resizable window"""
        # if already popped out, focus it
        if getattr(self, 'debug_window', None):
            try:
                self.debug_window.lift()
                return
            except Exception:
                self.debug_window = None

        # hide docked panel and open a new Toplevel
        try:
            self.debug_frame.place_forget()
        except Exception:
            pass
        try:
            self.debug_open_btn.place_forget()
        except Exception:
            pass

        self.debug_window = ctk.CTkToplevel(self)
        self.debug_window.title("status")
        # default larger size for popout window
        self.debug_window.geometry("800x420")
        self.debug_window.configure(fg_color=ModernStyle.BG_PRIMARY)
        # allow resizing and moving by OS window manager
        self.debug_window.resizable(True, True)

        # when the popout window closes, re-dock the panel
        def on_close():
            try:
                self.debug_window.destroy()
            except Exception:
                pass
            self.debug_window = None
            # re-show the compact docked panel
            try:
                self.debug_frame.place(relx=0.995, rely=0.995, anchor="se")
                self.debug_visible = True
            except Exception:
                pass

        self.debug_window.protocol("WM_DELETE_WINDOW", on_close)

        popup_frame = ctk.CTkFrame(self.debug_window, fg_color=ModernStyle.BG_TERTIARY, corner_radius=8)
        popup_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # header inside popup
        popup_header = ctk.CTkFrame(popup_frame, fg_color="transparent")
        popup_header.pack(fill="x", padx=6, pady=(6, 0))
        ctk.CTkLabel(popup_header, text="status", font=ModernStyle.FONT_SMALL, text_color=ModernStyle.TEXT_SECONDARY).pack(side="left")
        ctk.CTkButton(popup_header, text="Dock", width=60, height=26, command=on_close, fg_color=ModernStyle.BG_SECONDARY, text_color=ModernStyle.ACCENT_CYAN, corner_radius=6).pack(side="right")

        # create a new debug textbox for the popup and copy existing content
        popup_text = ctk.CTkTextbox(popup_frame, fg_color=ModernStyle.BG_PRIMARY, text_color=ModernStyle.TEXT_PRIMARY, corner_radius=6)
        popup_text.pack(fill="both", expand=True, padx=6, pady=6)
        popup_text.configure(state="normal")
        try:
            # copy existing debug contents
            existing = ""
            try:
                existing = self.debug_text.get("1.0", "end")
            except Exception:
                existing = ""
            popup_text.insert("end", existing)
        except Exception:
            pass
        popup_text.configure(state="disabled")

        # expose popup_text so append_debug can write to it
        self.debug_popup_text = popup_text

    def append_debug(self, text: str):
        """append a line to the debug panel safely"""
        try:
            # write to docked text if present
            if getattr(self, 'debug_text', None):
                try:
                    self.debug_text.configure(state="normal")
                    self.debug_text.insert("end", text + "\n")
                    self.debug_text.see("end")
                    self.debug_text.configure(state="disabled")
                except Exception:
                    pass
            # also write to popup if present
            if getattr(self, 'debug_popup_text', None):
                try:
                    self.debug_popup_text.configure(state="normal")
                    self.debug_popup_text.insert("end", text + "\n")
                    self.debug_popup_text.see("end")
                    self.debug_popup_text.configure(state="disabled")
                except Exception:
                    pass
        except Exception:
            pass

    def clear_debug(self):
        try:
            self.debug_text.configure(state="normal")
            self.debug_text.delete("1.0", "end")
            self.debug_text.configure(state="disabled")
        except Exception:
            pass

    # =================== model status event handlers ===================
    def _on_model_status_event(self, event, data):
        """handle status events from the model in the GUI thread-safe way"""
        try:
            if event == 'connected':
                self.after(0, lambda: self._handle_connected(data))
            elif event == 'disconnected':
                self.after(0, lambda: self._handle_disconnected(data))
            elif event == 'health':
                self.after(0, lambda: self.append_debug(f"health: {data.get('connected')}") )
        except Exception:
            pass

    def _on_model_event(self, event, data):
        try:
            if event == 'model_switched':
                model = data.get('model')
                self.after(0, lambda: self.append_debug(f"model_switched -> {model}"))
                self.after(0, lambda: self.status_label.configure(text=f"ready • {self.model.user_data.get('name') or 'anonymous'}"))
        except Exception:
            pass

    def _handle_connected(self, data):
        # update UI to show connected
        try:
            self.append_debug(f"connected to ollama: {data.get('url')}")
            self.status_indicator.configure(text_color=ModernStyle.ACCENT_GREEN)
            name_display = self.model.user_data.get('name') or 'anonymous'
            self.status_label.configure(text=f"ready • {name_display}")
        except Exception:
            pass

    def _handle_disconnected(self, data):
        try:
            self.append_debug(f"disconnected: {data.get('error')}")
            self.status_indicator.configure(text_color=ModernStyle.ACCENT_PURPLE)
            self.status_label.configure(text="offline")
        except Exception:
            pass
    
    def show_profile_editor(self):
        """show profile editor window"""
        profile_window = ctk.CTkToplevel(self)
        profile_window.title("edit profile")
        profile_window.geometry("450x480")
        profile_window.configure(fg_color=ModernStyle.BG_PRIMARY)
        profile_window.resizable(False, False)
        
        # make it modal
        profile_window.transient(self)
        profile_window.grab_set()
        
        main_frame = ctk.CTkFrame(profile_window, fg_color=ModernStyle.BG_PRIMARY)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # title
        title = ctk.CTkLabel(
            main_frame, text="📝 your profile",
            font=("Segoe UI", 18, "bold"),
            text_color=ModernStyle.ACCENT_CYAN
        )
        title.pack(pady=(0, 20))
        
        # name field
        ctk.CTkLabel(main_frame, text="name:", text_color=ModernStyle.TEXT_PRIMARY).pack(anchor="w", pady=(0, 5))
        name_entry = ctk.CTkEntry(
            main_frame,
            fg_color=ModernStyle.BG_TERTIARY,
            text_color=ModernStyle.TEXT_PRIMARY,
            border_color=ModernStyle.BG_SECONDARY,
            border_width=2,
            corner_radius=8
        )
        name_entry.insert(0, self.model.user_data['name'] or "")
        name_entry.pack(fill="x", pady=(0, 15))
        
        # interests field
        ctk.CTkLabel(main_frame, text="interests (comma separated):", text_color=ModernStyle.TEXT_PRIMARY).pack(anchor="w", pady=(0, 5))
        interests_entry = ctk.CTkEntry(
            main_frame,
            fg_color=ModernStyle.BG_TERTIARY,
            text_color=ModernStyle.TEXT_PRIMARY,
            border_color=ModernStyle.BG_SECONDARY,
            border_width=2,
            corner_radius=8
        )
        interests_entry.insert(0, ", ".join(self.model.user_data['interests']) if self.model.user_data['interests'] else "")
        interests_entry.pack(fill="x", pady=(0, 15))
        
        # dislikes field
        ctk.CTkLabel(main_frame, text="dislikes (comma separated):", text_color=ModernStyle.TEXT_PRIMARY).pack(anchor="w", pady=(0, 5))
        dislikes_entry = ctk.CTkEntry(
            main_frame,
            fg_color=ModernStyle.BG_TERTIARY,
            text_color=ModernStyle.TEXT_PRIMARY,
            border_color=ModernStyle.BG_SECONDARY,
            border_width=2,
            corner_radius=8
        )
        dislikes_entry.insert(0, ", ".join(self.model.user_data['dislikes']) if self.model.user_data['dislikes'] else "")
        dislikes_entry.pack(fill="x", pady=(0, 25))
        
        # buttons frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        def save_profile():
            # Update name
            name = name_entry.get().strip()
            if name:
                self.model.user_data['name'] = name
            
            # update interests
            interests_text = interests_entry.get().strip()
            if interests_text:
                self.model.user_data['interests'] = [i.strip() for i in interests_text.split(',')]
            else:
                self.model.user_data['interests'] = []
            
            # update dislikes
            dislikes_text = dislikes_entry.get().strip()
            if dislikes_text:
                self.model.user_data['dislikes'] = [d.strip() for d in dislikes_text.split(',')]
            else:
                self.model.user_data['dislikes'] = []
            
            # save to disk immediately
            self.model.save_user_data()
            
            # update status display
            user_data = self.model.get_user_data()
            if user_data['name']:
                name_display = user_data['name']
                self.status_indicator.configure(text_color=ModernStyle.ACCENT_GREEN)
            else:
                name_display = "anonymous"
                self.status_indicator.configure(text_color=ModernStyle.ACCENT_CYAN)
            self.status_label.configure(text=f"ready • {name_display}")
            
            # show confirmation
            self.add_system_message("✓ profile updated!")
            
            profile_window.destroy()
        
        ctk.CTkButton(
            button_frame, text="save", command=save_profile,
            font=("Segoe UI", 11, "bold"),
            fg_color=ModernStyle.ACCENT_CYAN,
            text_color=ModernStyle.BG_PRIMARY,
            hover_color=ModernStyle.ACCENT_PURPLE,
            corner_radius=8,
            width=100
        ).pack(side="right", padx=(5, 0))
        
        ctk.CTkButton(
            button_frame, text="cancel", command=profile_window.destroy,
            font=("Segoe UI", 11, "bold"),
            fg_color=ModernStyle.BG_SECONDARY,
            text_color=ModernStyle.ACCENT_CYAN,
            hover_color=ModernStyle.BG_TERTIARY,
            corner_radius=8,
            width=100
        ).pack(side="right")
    
    def show_model_selector(self):
        """show model selector window"""
        model_window = ctk.CTkToplevel(self)
        model_window.title("select model")
        model_window.geometry("550x500")
        model_window.configure(fg_color=ModernStyle.BG_PRIMARY)
        model_window.resizable(False, False)
        
        model_window.transient(self)
        model_window.grab_set()
        
        main_frame = ctk.CTkFrame(model_window, fg_color=ModernStyle.BG_PRIMARY)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # title
        title = ctk.CTkLabel(
            main_frame, text="🤖 choose ai model",
            font=("Segoe UI", 18, "bold"),
            text_color=ModernStyle.ACCENT_CYAN
        )
        title.pack(pady=(0, 10))
        
        # info
        info_text = ctk.CTkLabel(
            main_frame, text="select a model below. uncensored models are better for creative/adult content:",
            font=("Segoe UI", 10),
            text_color=ModernStyle.TEXT_SECONDARY,
            wraplength=500
        )
        info_text.pack(anchor="w", pady=(0, 20))
        
        # get available models
        available_models = self.model.get_available_models()
        
        # create scrollable frame for models
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            fg_color=ModernStyle.BG_TERTIARY,
            corner_radius=10
        )
        scroll_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        if not available_models:
            ctk.CTkLabel(
                scroll_frame, 
                text="no models found. download one with: ollama pull [model-name]",
                text_color=ModernStyle.TEXT_SECONDARY
            ).pack(pady=15)
        else:
            # model descriptions
            descriptions = {
                "mistral": "general purpose - slightly filtered",
                "llama2": "general purpose - balanced",
                "neural-chat": "conversational - flexible",
                "llama2-uncensored": "unrestricted - creative/adult friendly ⭐",
                "dolphin-mixtral": "creative - less filtered ⭐",
                "nous-hermes-2": "helpful - minimal restrictions ⭐",
                "openchat": "open - explicit content friendly ⭐"
            }
            
            model_var = ctk.StringVar(value=self.model.model_name)
            
            for model in available_models:
                model_short = model.split(':')[0]  # remove version tags
                desc = descriptions.get(model_short, "")
                label_text = f"{model_short}"
                if desc:
                    label_text += f" — {desc}"
                
                radio = ctk.CTkRadioButton(
                    scroll_frame, text=label_text,
                    variable=model_var, value=model,
                    font=("Segoe UI", 10),
                    text_color=ModernStyle.TEXT_PRIMARY,
                    fg_color=ModernStyle.ACCENT_CYAN,
                    hover_color=ModernStyle.ACCENT_PURPLE
                )
                radio.pack(anchor="w", pady=8, padx=15)
            
            # buttons
            button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            button_frame.pack(fill="x")
            
            def switch_model():
                new_model = model_var.get()
                self.model.switch_model(new_model)
                self.add_system_message(f"✓ switched to {new_model}! will use next message.")
                model_window.destroy()
            
            ctk.CTkButton(
                button_frame, text="switch", command=switch_model,
                font=("Segoe UI", 11, "bold"),
                fg_color=ModernStyle.ACCENT_CYAN,
                text_color=ModernStyle.BG_PRIMARY,
                hover_color=ModernStyle.ACCENT_PURPLE,
                corner_radius=8,
                width=100
            ).pack(side="right", padx=(5, 0))
            
            ctk.CTkButton(
                button_frame, text="cancel", command=model_window.destroy,
                font=("Segoe UI", 11, "bold"),
                fg_color=ModernStyle.BG_SECONDARY,
                text_color=ModernStyle.ACCENT_CYAN,
                hover_color=ModernStyle.BG_TERTIARY,
                corner_radius=8,
                width=100
            ).pack(side="right")    
    def show_conversations(self):
        """show saved conversations window"""
        conv_window = ctk.CTkToplevel(self)
        conv_window.title("saved conversations")
        conv_window.geometry("600x600")
        conv_window.configure(fg_color=ModernStyle.BG_PRIMARY)
        conv_window.resizable(True, True)
        
        conv_window.transient(self)
        conv_window.grab_set()
        
        main_frame = ctk.CTkFrame(conv_window, fg_color=ModernStyle.BG_PRIMARY)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # title
        title = ctk.CTkLabel(
            main_frame, text="💬 conversation history",
            font=("Segoe UI", 18, "bold"),
            text_color=ModernStyle.ACCENT_CYAN
        )
        title.pack(pady=(0, 20))
        
        # get conversations
        conversations = self.model.get_conversation_list()
        
        if not conversations:
            ctk.CTkLabel(
                main_frame, text="no saved conversations yet",
                font=("Segoe UI", 12),
                text_color=ModernStyle.TEXT_SECONDARY
            ).pack(pady=30)
        else:
            # create scrollable frame for conversation list
            scroll_frame = ctk.CTkScrollableFrame(
                main_frame,
                fg_color=ModernStyle.BG_TERTIARY,
                corner_radius=10
            )
            scroll_frame.pack(fill="both", expand=True, pady=(0, 20))
            
            for conv in conversations:
                # parse timestamp
                from datetime import datetime as dt
                timestamp = dt.fromisoformat(conv['timestamp'])
                time_str = timestamp.strftime("%b %d, %H:%M")
                
                # conversation frame
                conv_frame = ctk.CTkFrame(
                    scroll_frame,
                    fg_color=ModernStyle.BG_SECONDARY,
                    corner_radius=8
                )
                conv_frame.pack(fill="x", pady=8, padx=10)
                
                # info frame
                info_frame = ctk.CTkFrame(conv_frame, fg_color="transparent")
                info_frame.pack(fill="x", padx=12, pady=8, side="left", expand=True)
                
                # conversation info
                title_text = conv.get('title') or conv.get('user_name')
                ctk.CTkLabel(
                    info_frame,
                    text=f"{title_text} • {conv['message_count']} messages",
                    font=("Segoe UI", 11, "bold"),
                    text_color=ModernStyle.ACCENT_CYAN
                ).pack(anchor="w")
                
                ctk.CTkLabel(
                    info_frame,
                    text=time_str,
                    font=("Segoe UI", 9),
                    text_color=ModernStyle.TEXT_SECONDARY
                ).pack(anchor="w")
                
                # action buttons frame
                action_frame = ctk.CTkFrame(conv_frame, fg_color="transparent")
                action_frame.pack(side="right", padx=12, pady=8)
                
                def load_conv(filepath=conv['filepath']):
                    self.model.load_conversation_by_file(filepath)
                    self.chat_display.configure(state="normal")
                    self.chat_display.delete("1.0", "end")
                    self.chat_display.configure(state="disabled")
                    # reload chat display
                    for msg in self.model.conversation_history:
                        if msg['role'] == 'user':
                            self.add_user_message(msg['message'])
                        else:
                            self.add_bot_message(msg['message'])
                    self.add_system_message("✓ loaded previous conversation")
                    conv_window.destroy()
                
                ctk.CTkButton(
                    action_frame, text="load", command=load_conv,
                    font=("Segoe UI", 10, "bold"),
                    fg_color=ModernStyle.ACCENT_CYAN,
                    text_color=ModernStyle.BG_PRIMARY,
                    hover_color=ModernStyle.ACCENT_PURPLE,
                    corner_radius=6,
                    width=60
                ).pack(side="left", padx=(0, 5))
                
                def delete_conv(filepath=conv['filepath']):
                    import os
                    try:
                        os.remove(filepath)
                        self.add_system_message("✓ conversation deleted")
                    except:
                        pass
                    conv_window.destroy()
                    self.show_conversations()  # refresh
                
                ctk.CTkButton(
                    action_frame, text="delete", command=delete_conv,
                    font=("Segoe UI", 10, "bold"),
                    fg_color=ModernStyle.BG_SECONDARY,
                    text_color=ModernStyle.ACCENT_CYAN,
                    hover_color=ModernStyle.BG_TERTIARY,
                    corner_radius=6,
                    width=60
                ).pack(side="left")
                
                # rename button
                def rename_conv(filepath=conv['filepath']):
                    # Modal to enter new title
                    rename_win = ctk.CTkToplevel(conv_window)
                    rename_win.title("rename conversation")
                    rename_win.geometry("420x160")
                    rename_win.transient(conv_window)
                    rename_win.grab_set()

                    mainf = ctk.CTkFrame(rename_win, fg_color=ModernStyle.BG_PRIMARY)
                    mainf.pack(fill="both", expand=True, padx=12, pady=12)

                    ctk.CTkLabel(mainf, text="Title:", text_color=ModernStyle.TEXT_PRIMARY).pack(anchor="w", pady=(0,6))
                    title_entry = ctk.CTkEntry(mainf, fg_color=ModernStyle.BG_TERTIARY, text_color=ModernStyle.TEXT_PRIMARY)
                    # prefill with existing title if any
                    title_entry.insert(0, conv.get('title') or "")
                    title_entry.pack(fill="x", pady=(0,12))

                    def save_title():
                        new_title = title_entry.get().strip()
                        if new_title:
                            ok = self.model.rename_conversation(filepath, new_title)
                            if ok:
                                self.add_system_message("✓ conversation renamed")
                        rename_win.destroy()
                        conv_window.destroy()
                        self.show_conversations()

                    btnf = ctk.CTkFrame(mainf, fg_color="transparent")
                    btnf.pack(fill="x")
                    ctk.CTkButton(btnf, text="save", command=save_title, fg_color=ModernStyle.ACCENT_CYAN, text_color=ModernStyle.BG_PRIMARY).pack(side="right", padx=(6,0))
                    ctk.CTkButton(btnf, text="cancel", command=rename_win.destroy, fg_color=ModernStyle.BG_SECONDARY, text_color=ModernStyle.ACCENT_CYAN).pack(side="right")

                ctk.CTkButton(
                    action_frame, text="rename", command=rename_conv,
                    font=("Segoe UI", 10, "bold"),
                    fg_color=ModernStyle.BG_SECONDARY,
                    text_color=ModernStyle.ACCENT_CYAN,
                    hover_color=ModernStyle.BG_TERTIARY,
                    corner_radius=6,
                    width=70
                ).pack(side="left", padx=(6,5))
        
        # close button
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        ctk.CTkButton(
            button_frame, text="close", command=conv_window.destroy,
            font=("Segoe UI", 11, "bold"),
            fg_color=ModernStyle.BG_SECONDARY,
            text_color=ModernStyle.ACCENT_CYAN,
            hover_color=ModernStyle.BG_TERTIARY,
            corner_radius=8,
            width=100
        ).pack(side="right")