import os
import json
import threading
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import get_color_from_hex

# ==========================================
# KONFIGURASI API & MODEL (100% ASLI)
# ==========================================
CONFIG_FILE = os.path.join(App.get_running_app().user_data_dir if App.get_running_app() else ".", "config.json")

MODELS = {
    "DeepSeek Chat": "https://api.deepseek.com/v1/chat/completions",
    "OpenAI GPT-4o": "https://api.openai.com/v1/chat/completions"
}

# ==========================================
# UI APLIKASI (KIVY)
# ==========================================
class ChatUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.api_key = self.load_api_key()
        self.current_model = "DeepSeek Chat"
        
        # Warna Tema
        Window.clearcolor = get_color_from_hex('#0f172a')

        # --- TOP BAR ---
        top_bar = BoxLayout(size_hint_y=None, height=dp(50), padding=[dp(10), dp(10)])
        title = Label(text="[b]🧠 LuttzzGrox AI[/b]", markup=True, color=get_color_from_hex('#60a5fa'), size_hint_x=0.6)
        btn_settings = Button(text="⚙️ API Key", size_hint_x=0.4, background_color=get_color_from_hex('#1e293b'))
        btn_settings.bind(on_press=self.show_settings)
        top_bar.add_widget(title)
        top_bar.add_widget(btn_settings)
        self.add_widget(top_bar)

        # --- AREA CHAT ---
        self.scroll = ScrollView()
        self.chat_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10), padding=dp(10))
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        self.scroll.add_widget(self.chat_layout)
        self.add_widget(self.scroll)

        # --- INPUT BAR ---
        input_bar = BoxLayout(size_hint_y=None, height=dp(50), padding=[dp(10), dp(5), dp(10), dp(10)])
        self.input_text = TextInput(hint_text="Ketik pesan...", multiline=False, background_color=get_color_from_hex('#1e293b'), foreground_color=get_color_from_hex('#e2e8f0'))
        self.input_text.bind(on_text_validate=self.send_message)
        btn_send = Button(text="Kirim", size_hint_x=0.25, background_color=get_color_from_hex('#2563eb'))
        btn_send.bind(on_press=self.send_message)
        input_bar.add_widget(self.input_text)
        input_bar.add_widget(btn_send)
        self.add_widget(input_bar)

    def load_api_key(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f).get("api_key", "")
        except:
            return ""

    def save_api_key(self, key):
        self.api_key = key
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"api_key": key}, f)

    def show_settings(self, instance):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        txt_key = TextInput(text=self.api_key, hint_text="Masukkan API Key (sk-...)", password=True)
        
        # Dropdown model sederhana pakai tombol
        btn_model = Button(text=f"Model: {self.current_model}", size_hint_y=None, height=dp(40))
        def switch_model(btn):
            self.current_model = "OpenAI GPT-4o" if self.current_model == "DeepSeek Chat" else "DeepSeek Chat"
            btn.text = f"Model: {self.current_model}"
            
        btn_model.bind(on_press=switch_model)
        
        btn_save = Button(text="Simpan", size_hint_y=None, height=dp(40), background_color=get_color_from_hex('#10b981'))
        popup = Popup(title='Pengaturan LuttzzGrox', content=layout, size_hint=(0.9, 0.6))
        
        def save_and_close(instance):
            self.save_api_key(txt_key.text.strip())
            popup.dismiss()
            self.add_message("Sistem", "✅ API Key berhasil disimpan!")

        btn_save.bind(on_press=save_and_close)
        
        layout.add_widget(Label(text="API Key (Simpan lokal di HP):", size_hint_y=None, height=dp(30)))
        layout.add_widget(txt_key)
        layout.add_widget(btn_model)
        layout.add_widget(btn_save)
        popup.open()

    def add_message(self, sender, text):
        color = '#2563eb' if sender == "Anda" else '#1e293b'
        text_color = '#ffffff' if sender == "Anda" else '#e2e8f0'
        
        # Label dengan teks rata kiri-kanan dan bisa panjang
        msg_label = Label(
            text=f"[b]{sender}:[/b]\n{text}",
            markup=True,
            size_hint_y=None,
            text_size=(Window.width - dp(40), None),
            halign='left',
            valign='top',
            color=get_color_from_hex(text_color),
            padding=[dp(10), dp(10)]
        )
        msg_label.bind(texture_size=msg_label.setter('size'))
        
        # Bungkus label dengan kotak berwarna
        bubble = BoxLayout(size_hint_y=None, padding=[dp(5), dp(5)])
        bubble.bind(minimum_height=bubble.setter('height'))
        
        # Simulasi chat bubble
        bubble_wrapper = BoxLayout(size_hint_y=None, padding=dp(5))
        bubble_wrapper.bind(minimum_height=bubble_wrapper.setter('height'))
        bubble_wrapper.add_widget(msg_label)
        
        self.chat_layout.add_widget(bubble_wrapper)
        Clock.schedule_once(lambda dt: setattr(self.scroll, 'scroll_y', 0))

    def send_message(self, instance):
        text = self.input_text.text.strip()
        if not text: return
        if not self.api_key:
            self.add_message("Sistem", "⚠️ API Key belum diisi! Klik tombol ⚙️ API Key di kanan atas.")
            return

        self.input_text.text = ""
        self.add_message("Anda", text)
        self.add_message("LuttzzGrox", "⏳ Sedang berpikir...")

        # Jalankan API call di background agar UI tidak freeze
        threading.Thread(target=self.call_api, args=(text,), daemon=True).start()

    def call_api(self, prompt):
        url = MODELS[self.current_model]
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prompt Sistem: Memaksa AI menjawab lengkap, mendalam, tanpa dipotong
        system_prompt = (
            "Anda adalah LuttzzGrox, AI super canggih dengan penalaran mendalam. "
            "ATURAN WAJIB: (1) Jawab dengan SANGAT LENGKAP dan detail, jangan pernah memotong jawaban. "
            "(2) Gunakan penalaran kritis dan berikan data ilmu pengetahuan yang akurat. "
            "(3) Jika memberikan kode, berikan kode penuh yang siap dijalankan. "
            "Gunakan bahasa Indonesia yang profesional."
        )
        
        payload = {
            "model": "deepseek-chat" if "DeepSeek" in self.current_model else "gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4096  # Maksimal output agar jawaban full
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            reply = data['choices'][0]['message']['content']
            
            # Hapus teks "Sedang berpikir..." dan ganti dengan jawaban asli
            Clock.schedule_once(lambda dt: self.update_last_message(reply))
            
        except requests.exceptions.RequestException as e:
            error_msg = f"❌ Error Koneksi/API:\n{str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f"\nDetail: {e.response.text}"
            Clock.schedule_once(lambda dt: self.update_last_message(error_msg))

    def update_last_message(self, new_text):
        # Hapus pesan loading terakhir
        if len(self.chat_layout.children) > 0:
            self.chat_layout.remove_widget(self.chat_layout.children[0])
        self.add_message("LuttzzGrox", new_text)


class LuttzzGroxApp(App):
    def build(self):
        self.title = "LuttzzGrox AI"
        return ChatUI()

if __name__ == '__main__':
    LuttzzGroxApp().run()
