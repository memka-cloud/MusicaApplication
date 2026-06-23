import customtkinter as ctk
import keyring
import requests
import vlc
from tkinter import messagebox
import os


SERVER_URL = "http://127.0.0.1:8000"



vlc_instance = vlc.Instance("--no-video --quiet")
player = vlc_instance.media_player_new()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_NAME = ("MyMusicApp")
KEY_USER = "logged_in_username"


audio_stream = None
playback_thread = None
is_paused = False



class SettingsPanel(ctk.CTkFrame):
    def __init__(self, master, on_close_callback, on_logout_callback):
        
        super().__init__(master, fg_color=("#ebebeb", "#212121"), corner_radius=0, border_width=1)
        self.on_close_callback = on_close_callback
        self.on_logout_callback = on_logout_callback
        self.label_title = ctk.CTkLabel(self, text="Настройки", font=("Arial", 18, "bold"))
        self.label_title.pack(pady=(20, 20))
        self.label_theme = ctk.CTkLabel(self, text="Тема оформления:")
        self.label_theme.pack(pady=5)
        self.theme_switch = ctk.CTkSegmentedButton(
            self,
            values=["Dark", "Light"],
            command=self.change_theme
        )
        self.theme_switch.set("Dark" if ctk.get_appearance_mode() == "Dark" else "Light")
        self.theme_switch.pack(pady=5)
        self.spacer = ctk.CTkLabel(self, text="")
        self.spacer.pack(expand=True, fill="both")
        self.btn_logout = ctk.CTkButton(
            self,
            text="Выйти из аккаунта",
            width=160,
            height=35,
            fg_color="#8b0000",
            hover_color="#660000",
            command=self.logout
        )
        self.btn_logout.pack(pady=10)
        self.btn_close_cross = ctk.CTkButton(
            self,
            text="×",
            font=("Arial", 22),
            width=35,
            height=35,
            fg_color = "transparent",
            hover_color = ("#dbdbdb", "#2b2b2b"),
            text_color = ("black", "white"),
            command = self.on_close_callback
        )
        self.btn_close_cross.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)

    def change_theme(self, theme):
        ctk.set_appearance_mode(theme)

    def logout(self):
        try:
            keyring.delete_password(APP_NAME, KEY_USER)
        except keyring.errors.PasswordDeleteError:
            pass
        self.on_logout_callback()




class RegisterFrame(ctk.CTkFrame):
    def __init__(self, master, on_success_callback=None):  
        super().__init__(master)
        self.on_success_callback = on_success_callback  
        self.configure(fg_color="transparent")

        
        self.mode = "login"  

        
        self.title_label = ctk.CTkLabel(self, text="Авторизация", font=("Arial", 24, "bold"))
        self.title_label.pack(pady=(20, 30))

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Имя пользователя", width=250)
        self.username_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Пароль", show="*", width=250)
        self.password_entry.pack(pady=10)

        self.confirm_password_entry = ctk.CTkEntry(self, placeholder_text="Повторите пароль", show="*", width=250)

        self.action_button = ctk.CTkButton(self, text="Войти", command=self.handle_action, width=250)
        self.action_button.pack(pady=(20, 10))

        self.switch_button = ctk.CTkButton(
            self,
            text="Нет аккаунта? Зарегистрироваться",
            command=self.toggle_mode,
            fg_color="transparent",
            hover_color=("#DBDBDB", "#2B2B2B"),
            text_color=("#1F6AA5", "#1F85DE")
        )
        self.switch_button.pack(pady=10)

    def toggle_mode(self):
        if self.mode == "login":
            self.mode = "register"
            self.title_label.configure(text="Регистрация")
            self.action_button.configure(text="Создать аккаунт")
            self.switch_button.configure(text="Уже есть аккаунт? Войти")
            self.confirm_password_entry.pack(after=self.password_entry, pady=10)
        else:
            self.mode = "login"
            self.title_label.configure(text="Авторизация")
            self.action_button.configure(text="Войти")
            self.switch_button.configure(text="Нет аккаунта? Зарегистрироваться")
            self.confirm_password_entry.pack_forget()

    def handle_action(self):
        
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return

        if self.mode == "register":
            confirm_password = self.confirm_password_entry.get().strip()
            if password != confirm_password:
                messagebox.showerror("Ошибка", "Пароли не совпадают!")
                return
            self.register_user(username, password)
        else:
            self.login_user(username, password)

    def register_user(self, username, password):
        
        try:
            payload = {"username": username, "password": password}
            response = requests.post(f"{SERVER_URL}/register", json=payload)

            if response.status_code == 200:
                messagebox.showinfo("Успех", "Регистрация прошла успешно! Теперь вы можете войти.")
                self.toggle_mode()  
            else:
                error_detail = response.json().get("detail", "Неизвестная ошибка сервера")
                messagebox.showerror("Ошибка регистрации", error_detail)
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Ошибка сети", "Не удалось связаться с сервером. Проверьте, запущен ли он.")

    def login_user(self, username, password):
        try:
            payload = {"username": username, "password": password}
            headers = {
                "Bypass-Tunnel-Reminder": "true",
                "X-Tuna-Skip-Warning": "true"
            }
            response = requests.post(f"{SERVER_URL}/login", json=payload, headers=headers)

            if response.status_code == 200:
                keyring.set_password("my_app_auth", "current_user", username)
                messagebox.showinfo("Успех", f"Добро пожаловать, {username}!")
                if self.on_success_callback:
                    self.on_success_callback(username)
            else:
                
                try:
                    error_detail = response.json().get("detail", "Неверный логин или пароль")
                except Exception:
                    error_detail = "Сервер вернул некорректный ответ (проверьте туннель)"
                messagebox.showerror("Ошибка авторизации", error_detail)
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Ошибка сети", "Не удалось связаться с сервером. Проверьте, запущен ли он.")


class MainMenuFrame(ctk.CTkFrame):
    def __init__(self, master, username, on_logout_callback):
        super().__init__(master, fg_color="transparent")

        self.all_server_songs = []   
        self.loaded_count = 0        
        self.songs_per_page = 30
        self.on_logout_callback = on_logout_callback
        self.settings_visible = False
        self.is_playing = False
        self.current_url = None
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent", height=60)
        self.top_bar.pack(fill="x", padx=15, pady=10)

        self.label_welcome = ctk.CTkLabel(self.top_bar, text=f"Привет, {username}!", font=("Arial", 16, "bold"),
                                          text_color="#1DB954")
        self.label_welcome.pack(side="left")

        
        self.btn_settings = ctk.CTkButton(
            self.top_bar, text="⚙", font=("Arial", 20), width=35, height=35,
            fg_color="transparent", hover_color=("#dbdbdb", "#2b2b2b"), command=self.toggle_settings
        )
        self.btn_settings.pack(side="right")

        
        self.entry_search = ctk.CTkEntry(self.top_bar, placeholder_text="Поиск песен...", width=200, height=30)
        self.entry_search.pack(side="right", padx=20)


        self.label_section = ctk.CTkLabel(self, text="Выбранное для вас", font=("Arial", 14, "bold"), anchor="w")
        self.label_section.pack(fill="x", padx=20, pady=(15, 5))

        self.songs_frame = ctk.CTkScrollableFrame(self, fg_color=("#f3f3f3", "#141414"), corner_radius=10)
        self.songs_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # --- НИЖНЯЯ ПАНЕЛЬ: МИНИ-ПЛЕЕР ---
        self.player_bar = ctk.CTkFrame(self, fg_color=("#e6e6e6", "#1f1f1f"), height=90, corner_radius=12)
        self.player_bar.pack(fill="x", padx=15, pady=15)

        self.label_current_song = ctk.CTkLabel(self.player_bar, text="Ничего не воспроизводится",
                                               font=("Arial", 13, "bold"), anchor="w")
        self.label_current_song.pack(fill="x", padx=15, pady=(8, 2))

        self.controls_frame = ctk.CTkFrame(self.player_bar, fg_color="transparent")
        self.controls_frame.pack(pady=2)

        self.btn_prev = ctk.CTkButton(
            self.controls_frame, text="⏮", font=("Arial", 16), width=35, height=30,
            fg_color="transparent", hover_color=("#cdcdcd", "#2e2e2e"),
            command=self.play_prev_song
        )
        self.btn_prev.pack(side="left", padx=5)

        self.btn_play_pause = ctk.CTkButton(
            self.controls_frame, text="▶", font=("Arial", 16), width=45, height=30,
            fg_color="#1DB954", hover_color="#1aa34a", command=self.toggle_play_pause
        )
        self.btn_play_pause.pack(side="left", padx=5)

        self.btn_next = ctk.CTkButton(
            self.controls_frame, text="⏭", font=("Arial", 16), width=35, height=30,
            fg_color="transparent", hover_color=("#cdcdcd", "#2e2e2e"),
            command=self.play_next_song
        )
        self.btn_next.pack(side="left", padx=5)

        
        self.label_volume_icon = ctk.CTkLabel(self.controls_frame, text="🔊", font=("Arial", 14))
        self.label_volume_icon.pack(side="left", padx=(15, 5))

        
        self.slider_volume = ctk.CTkSlider(
            self.controls_frame, from_=0, to=1, width=100, height=12,
            fg_color="gray", progress_color="#1DB954", command=self.change_volume
        )
        self.slider_volume.set(0.7)  
        self.slider_volume.pack(side="left", padx=5)

        
        self.slider_progress = ctk.CTkSlider(
            self.player_bar, from_=0, to=100, height=15,
            fg_color="gray", progress_color="#1DB954",
            command=self.scroll_song
        )
        self.slider_progress.set(0)
        self.slider_progress.pack(fill="x", padx=20, pady=(2, 8))
        self.settings_panel = SettingsPanel(self, on_close_callback=self.toggle_settings,
        on_logout_callback=self.on_logout_callback)


        self.songs_frame.bind_all("<MouseWheel>", lambda e: self.check_scroll_bottom())
        self.current_song_index = -1
        self.load_songs_from_sql()

    def load_songs_from_sql(self):
        try:
            for widget in self.songs_frame.winfo_children():
                widget.destroy()
            response = requests.get(f"{SERVER_URL}/get_songs", headers={"X-Tuna-Skip-Warning": "true"})
            if response.status_code == 200:
                self.all_server_songs = response.json()
                if not self.all_server_songs:
                    label_empty = ctk.CTkLabel(
                        self.songs_frame,
                        text="В базе данных пока нет песен.",
                        font=("Arial", 14)
                    )
                    label_empty.pack(pady=40)
                    return
                for index, song in enumerate(self.all_server_songs):
                    song_text = f"{song['artist']} - {song['title']} (Добавил: {song['added_by']})"
                    btn_song = ctk.CTkButton(
                        self.songs_frame,
                        text=song_text,
                        anchor="w",
                        fg_color="transparent",
                        text_color=("#000000", "#FFFFFF"),
                        hover_color=("#dbdbdb", "#2b2b2b"),
                        height=35,
                        
                        command=lambda idx=index: self.play_song_from_sql(idx)
                    )
                    btn_song.pack(fill="x", padx=10, pady=5)
            else:
                import tkinter.messagebox as messagebox
                messagebox.showerror("Ошибка", f"Сервер вернул код: {response.status_code}")

        except requests.exceptions.ConnectionError:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Ошибка сети", "Не удалось загрузить песни. Проверьте туннель.")

    def play_song_from_sql(self, index):
        self.current_song_index = index
        try:
            import vlc
            selected_song = self.all_server_songs[index]
            self.current_url = selected_song['url']
            self.label_current_song.configure(text=f"{selected_song['artist']} - {selected_song['title']}")

            if not hasattr(self, 'vlc_player') or self.vlc_player is None:
                self.vlc_instance = vlc.Instance()
                self.vlc_player = self.vlc_instance.media_player_new()
            self.vlc_player.stop()
            media = self.vlc_instance.media_new(self.current_url)
            self.vlc_player.set_media(media)
            self.vlc_player.play()
            self.is_playing = True
            self.btn_play_pause.configure(text="⏸")
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Ошибка VLC", f"Детали: {e}")

    def toggle_play_pause(self):
        if not hasattr(self, 'current_url') or not self.current_url:
            import tkinter.messagebox as messagebox
            messagebox.showinfo("Плеер", "Сначала выберите песню из списка выше!")
            return
        try:
            if self.is_playing:
                self.vlc_player.pause()
                self.is_playing = False
                self.btn_play_pause.configure(text="▶")
            else:
                self.vlc_player.play()
                self.is_playing = True
                self.btn_play_pause.configure(text="⏸")
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Ошибка управления", f"Детали: {e}")




    def load_next_batch(self):
        
        start = self.loaded_count
        end = start + self.songs_per_page
        batch = self.all_server_songs[start:end]

        for song in batch:
            title = song["title"]
            clean_title = title[0] if isinstance(title, list) else title
            self.add_song_to_list(clean_title, song["audio_url"])
        self.loaded_count += len(batch)

    def check_scroll_bottom(self):
        
        if self.loaded_count >= len(self.all_server_songs):
            return
        scroll_pos = self.songs_frame._scrollbar.get()
        if scroll_pos[1] > 0.95:
            self.load_next_batch()


    def add_song_to_list(self, song_title, audio_url):
        
        row = ctk.CTkFrame(self.songs_frame, fg_color="transparent", height=40)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        lbl_text = ctk.CTkLabel(row, text=song_title, font=("Arial", 12), anchor="w")
        lbl_text.pack(side="left", padx=15, fill="x", expand=True)

        btn = ctk.CTkButton(
            row, text="▶", font=("Arial", 10), width=30, height=26, fg_color="#2b2b2b", hover_color="#1DB954",
            command=lambda t=song_title, url=audio_url: self.select_song(t, url)
        )
        btn.pack(side="right", padx=15)

    def select_song(self, song_title, audio_url):
        
        
        print(f"Потоковое воспроизведение через VLC: {song_title}")
        print(f"Ссылка от сервера: {audio_url}")

        self.label_current_song.configure(text=song_title)
        self.btn_play_pause.configure(text="⏸")
        self.slider_progress.set(0)
        self.current_url = audio_url
        self.is_playing = True
        media = vlc_instance.media_new(audio_url)
        player.set_media(media)
        player.play()


    def update_progress_slider(self):
        try:
            if hasattr(self, 'vlc_player') and self.vlc_player and self.is_playing:
                position = self.vlc_player.get_position() * 100
                if position > 0:
                    self.slider_progress.set(position)
        except Exception:
            pass

        
        self.after(500, self.update_progress_slider)

    def scroll_song(self, value):
        
        try:
            if hasattr(self, 'vlc_player') and self.vlc_player:
                
                vlc_position = float(value) / 100.0
                self.vlc_player.set_position(vlc_position)
        except Exception as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Ошибка перемотки", f"Детали: {e}")

    def toggle_settings(self):
        
        if not self.settings_visible:
            
            self.settings_panel.place(relx=1.0, rely=0.0, anchor="ne", relwidth=0.4, relheight=1.0)
            self.settings_panel.lift()
            self.settings_visible = True
        else:
            self.settings_panel.place_forget()
            self.settings_visible = False

    def change_volume(self, value):
        
        
        volume_percent = int(value * 100)
        player.audio_set_volume(volume_percent)

        
        if volume_percent == 0:
            self.label_volume_icon.configure(text="🔇")
        elif volume_percent < 35:
            self.label_volume_icon.configure(text="🔈")
        elif volume_percent < 70:
            self.label_volume_icon.configure(text="🔉")
        else:
            self.label_volume_icon.configure(text="🔊")

    def play_next_song(self):

        if not self.all_server_songs or self.current_song_index == -1:
            return

        
        next_index = (self.current_song_index + 1) % len(self.all_server_songs)
        self.play_song_from_sql(next_index)

    def play_prev_song(self):
        if not self.all_server_songs or self.current_song_index == -1:
            return

        
        prev_index = (self.current_song_index - 1) % len(self.all_server_songs)
        self.play_song_from_sql(prev_index)


class MusicApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Music App")
        self.geometry("400x500")
        self.resizable(False, False)
        self.current_frame = None
        self.show_register_screen()

    def show_register_screen(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = RegisterFrame(self, on_success_callback=self.show_main_menu)
        self.current_frame.pack(padx=20, pady=20, fill="both", expand=True)

    def show_main_menu(self, username="Пользователь"):

        if self.current_frame:
            self.current_frame.pack_forget()
            self.current_frame.destroy()
        self.geometry("1050x650")
        self.resizable(True, True)
        self.current_frame = MainMenuFrame(
            master=self,
            username=username,
            on_logout_callback=self.show_register_screen
        )
        self.current_frame.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = MusicApp()
    app.mainloop()

