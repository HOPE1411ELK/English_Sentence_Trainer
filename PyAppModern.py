import os, sys, time, random
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import pygame

# -------------------- util --------------------
def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def norm(s: str) -> str:
    return s.replace("’", "'").replace("‘", "'").replace("`", "'").strip()

# -------------------- sounds --------------------

pygame.mixer.init()
startsound = pygame.mixer.Sound(resource_path("startsound.wav"))
correctsound = pygame.mixer.Sound(resource_path("correctsound.wav"))
wrongsound = pygame.mixer.Sound(resource_path("wrongsound.wav"))
giveupsound = pygame.mixer.Sound(resource_path("giveupsound.wav"))
gameoversound = pygame.mixer.Sound(resource_path("gameoversound.wav"))
gameendsound = pygame.mixer.Sound(resource_path("gameendsound.wav"))
shufflesound = pygame.mixer.Sound(resource_path("shufflesound.wav"))

for s in (startsound, correctsound, wrongsound, giveupsound, gameendsound, shufflesound):
    s.set_volume(0.5)
gameoversound.set_volume(0.3)




# 候補を列挙（ファイルが無いものは除外）
bgm_candidates = [
    resource_path("battlebgm1.mp3"),
    resource_path("battlebgm2.mp3"),
    resource_path("battlebgm3.mp3"),
    resource_path("battlebgm4.mp3"),
]
bgm_files = [p for p in bgm_candidates if os.path.exists(p)]

if bgm_files:
    track = random.choice(bgm_files)   # ← 1曲だけランダム選択
    pygame.mixer.music.load(track)
    pygame.mixer.music.set_volume(0.07)

    pygame.mixer.music.play(-1) # 同じ曲をずっとループ
else:
    print("[BGM] mp3 が見つかりません（スキップ）")


# -------------------- data --------------------
def load_sentences_from_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        if not lines:
            raise ValueError("File is empty")
        random.shuffle(lines)
        return lines
    except (FileNotFoundError, ValueError) as e:
        messagebox.showerror("ERROR", f"File read error: {e}")
        return []

SENTENCE_FILE = resource_path("sentences.txt")
SENTENCES = load_sentences_from_file(SENTENCE_FILE)
if not SENTENCES:
    messagebox.showwarning("WARNING", "The sentence list is empty. Please check your file.")
    sys.exit(0)

# -------------------- app --------------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

BG = "#C4F3E4"
CARD = "#E4F2E7"
TEXT = "#1C1C1C"
PRIMARY = "#3CC07C"
PRIMARY_HOVER = "#31A37D"
RADIUS = 14
PAD = 12

class ESBApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ENGLISH SENTENCE BUILDER")
        self.tile_font = ctk.CTkFont(family="Yu Gothic UI", size=28, weight="bold")
        self.geometry("1100x740")
        self.configure(fg_color=BG)

        # ---- state ----
        self.sentences = SENTENCES
        self.sentence_index = -1
        self.sentence = ""
        self.words = []
        self.shuffled = []
        self.selected = []
        self.used = set()
        self.correct_count = 0
        self.question_count = 0
        self.give_up_count = 0
        self.wrong_attempts = 0
        self.solve_times = []
        self.round_start_time = None
        self.total_time_limit = 15 * 60
        self.timer_running = False
        self.timer_job = None
        self.game_has_ended = False
        self.game_start_time = time.time()
        self.mode_var = ctk.StringVar(value="sequential")

        self._build_ui()
        self.new_game(first=True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- UI ----------
    
    def _build_ui(self):
        # Header
        top = ctk.CTkFrame(self, corner_radius=0, fg_color="#D4ECD9")
        top.pack(fill="x")
        ctk.CTkLabel(
            top, text="ENGLISH SENTENCE BUILDER",
            font=("Yu Gothic UI", 20, "bold")
        ).pack(side="left", padx=16, pady=12)
        self.timer_label = ctk.CTkLabel(top, text="TIME: 15:00", font=("Segoe UI", 18))
        self.timer_label.pack(side="right", padx=16)

        # Body
        body = ctk.CTkFrame(self, fg_color=BG)
        body.pack(fill="both", expand=True, padx=PAD, pady=PAD)

        # Left panel (game area)
        left = ctk.CTkFrame(body, fg_color=CARD, corner_radius=RADIUS)
        left.pack(side="left", fill="both", expand=True, padx=(0, PAD))

        self.question_label = ctk.CTkLabel(
            left, text="MAKE THE CORRECT SENTENCES!",
            font=("Segoe UI", 18), text_color="#2E2E2E"
        )
        self.question_label.pack(anchor="w", padx=18, pady=(0, 6))

        self.result_label = ctk.CTkLabel(
            left, text="HERE IS YOUR ANSWER",
            font=("Segoe UI", 24), text_color="#2E2E2E"
        )
        self.result_label.pack(fill="x", padx=18, pady=(0, 8))

        # Word pool
        self.pool = ctk.CTkFrame(left, fg_color=CARD)
        self.pool.pack(fill="x", padx=18, pady=(4, 4))

        # Buttons row (Answer / Shuffle / Clear)
        btns = ctk.CTkFrame(left, fg_color=CARD)
        btns.pack(fill="x", padx=18, pady=(10, 18))
        self.answer_btn = ctk.CTkButton(
            btns, text="ANSWER", font=("Segoe UI", 18), width=180, height=56,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER, command=self.check_answer
        )
        self.answer_btn.pack(side="right")
        ctk.CTkButton(btns, text="SHUFFLE", command=self.shuffle_words).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text="CLEAR", command=self.clear_answer).pack(side="left", padx=(0, 8))

        # Status
        self.message_label = ctk.CTkLabel(left, text="", text_color="#C0392B", font=("Segoe UI", 16, "bold"))
        self.message_label.pack(anchor="w", padx=18, pady=(0, 4))
        self.correct_sentence_label = ctk.CTkLabel(left, text="", text_color="#1B7A33", font=("Segoe UI", 16))
        self.correct_sentence_label.pack(anchor="w", padx=18, pady=(0, 2))
        self.avg_time_label = ctk.CTkLabel(
            left, text="CORRECT: 0/0 | AVG: 0.0 sec", text_color="#1B4F72", font=("Segoe UI", 16)
        )
        self.avg_time_label.pack(anchor="w", padx=18, pady=(0, 12))

        # Right panel (controls)
        right = ctk.CTkFrame(body, fg_color=CARD, corner_radius=RADIUS, width=280)
        right.pack(side="right", fill="y")

        ctk.CTkLabel(right, text="QUESTION STYLE", font=("Yu Gothic UI", 16, "bold")).pack(anchor="w", padx=16, pady=(16, 6))
        style_row = ctk.CTkFrame(right, fg_color=CARD)
        style_row.pack(anchor="w", padx=12, pady=(0, 10))
        ctk.CTkRadioButton(style_row, text="SAME",   variable=self.mode_var, value="sequential").pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(style_row, text="RANDOM", variable=self.mode_var, value="random").pack(side="left")

        ctk.CTkLabel(right, text="HINT", font=("Yu Gothic UI", 16, "bold")).pack(anchor="w", padx=16, pady=(10, 4))
        ctk.CTkLabel(right, text="FIND THE SUBJECT AND THE ENDING", justify="left").pack(anchor="w", padx=16)

        ctrl = ctk.CTkFrame(right, fg_color=CARD)
        ctrl.pack(fill="x", padx=12, pady=(20, 10))
        ctk.CTkButton(ctrl, text="GIVE UP", command=self.give_up).pack(fill="x", pady=(0, 8))
        ctk.CTkButton(ctrl, text="NEW GAME", command=self.new_game).pack(fill="x")

        ctk.CTkLabel(right, text="Music: MaouDamashii").pack(side="bottom", pady=10)







    # ---------- ゲームロジック ----------
    def _build_pool(self):
        for w in self.pool.winfo_children():
            w.destroy()
        cols = 4
        self.pool_buttons = []
        for i, w in enumerate(self.shuffled):
            b = ctk.CTkButton(self.pool, text=w, width=160, height=48, font=self.tile_font,
                              corner_radius=RADIUS, fg_color="white", text_color=TEXT,
                              hover_color="#EAF7EF", command=lambda ww=w, idx=i: self.on_word_click(ww, idx))
            r, c = divmod(i, cols)
            b.grid(row=r, column=c, padx=8, pady=8, sticky="ew")
            self.pool_buttons.append(b)
        for c in range(cols):
            self.pool.grid_columnconfigure(c, weight=1)

    def on_word_click(self, word, idx):
        if idx in self.used:
            return
        self.used.add(idx)
        self.selected.append(word)
        self.pool_buttons[idx].configure(state="disabled", fg_color="#F0F0F0")
        self._update_result()

    def _update_result(self):
        self.result_label.configure(text=" ".join(self.selected) if self.selected else "HERE IS YOUR ANSWER")
        self.avg_time_label.configure(text=f"CORRECT: {self.correct_count}/{self.question_count} | AVG: {self._avg_time():.1f} sec")

    def _avg_time(self):
        return (sum(self.solve_times) / len(self.solve_times)) if self.solve_times else 0.0

    def shuffle_words(self):
        random.shuffle(self.shuffled)
        shufflesound.play()
        self.selected.clear()
        self.used.clear()
        self._build_pool()
        self._update_result()
        self.message_label.configure(text="")

    def clear_answer(self):
        self.selected.clear()
        self.used.clear()
        self._build_pool()
        self._update_result()
        self.message_label.configure(text="")

    def check_answer(self):
        user = " ".join(self.selected)
        if norm(user) == norm(self.sentence):
            self.correct_count += 1
            self.question_count += 1
            correctsound.play()   # 鳴る
            self.wrong_attempts = 0
            
            self.correct_sentence_label.configure(text=f"CORRECT!\n{self.sentence}")
            if self.round_start_time:
                self.solve_times.append(time.time() - self.round_start_time)
            self.reset_round()
        else:
            self.wrong_attempts += 1
            wrongsound.play()
            self.correct_sentence_label.configure(text="")
            if self.wrong_attempts >= 3:
                self.give_up()
                self.message_label.configure(text="")
            
            else:
                self.shuffle_words()
                self.message_label.configure(text=f"WRONG! TRY AGAIN ({self.wrong_attempts}/3)", text_color="#C0392B")


    


    def give_up(self):
        self.message_label.configure(text="", text_color="#5BE1BE")
        self.give_up_count += 1
        giveupsound.play()
        
        self.correct_sentence_label.configure(text=f"THE ANSWER IS\n{self.sentence}")
        self.question_count += 1
        if self.give_up_count >= 5:
            self._force_end_by_giveup()
        else:
            self.reset_round()
        

    




    def _force_end_by_giveup(self):
        self.stop_timer()
        self.end_game()

    def new_game(self, first=False):
        startsound.play()
        pygame.mixer.music.play(-1) # 同じ曲をずっとループ
        self.answer_btn.configure(state="normal")   # ← 追加（Game Over 後の再開用）
        self.give_up_count = 0
        self.game_has_ended = False
        self.wrong_attempts = 0

                      # ▼答え表示 / GAME OVER 表示をクリア
        if hasattr(self, "correct_sentence_label"):
           self.correct_sentence_label.configure(text="")
        if hasattr(self, "message_label"):
           self.message_label.configure(text="")

# ★正解数をリセット
        self.correct_count = 0
               # （必要なら他もリセット）
        self.question_count = 0
        self.solve_times.clear()
    
                  # ラベルがある場合は表示も初期化（存在チェック付き）
        
        if hasattr(self, "avg_time_label"):
           self.avg_time_label.configure(text="CORRECT: 0 AVG: 0.00s")


        self.solve_times.clear()
        self.reset_round()
        self.stop_timer()
        self.start_timer()

    def reset_round(self):
        self.message_label.configure(text="", text_color="#5BE1BE")
        self.selected.clear()
        self.used.clear()
        self._pick_sentence()
        self._build_pool()
        self._update_result()
        self.wrong_attempts = 0        # ← ここで毎ラウンド初期化
        self.round_start_time = time.time()

    def _pick_sentence(self):
        mode = self.mode_var.get()
        if mode == "sequential":
            self.sentence_index += 1
            if self.sentence_index >= len(self.sentences):
                self.end_game()
                return
            self.sentence = self.sentences[self.sentence_index]
        else:
            self.sentence = random.choice(self.sentences)
        self.words = self.sentence.split()
        self.shuffled = self.words[:]
        random.shuffle(self.shuffled)
        self.question_label.configure(text="MAKE THE CORRECT SENTENCES!")

    def start_timer(self):
        self.timer_running = True
        self.game_start_time = time.time()
        self.timer_label.configure(text=f"TIME: {self.total_time_limit//60:02d}:00")
        self._tick()

    def _tick(self):
        if not self.timer_running:
            return
        elapsed = int(time.time() - self.game_start_time)
        remaining = max(0, self.total_time_limit - elapsed)
        m, s = divmod(remaining, 60)
        self.timer_label.configure(text=f"TIME: {m:02d}:{s:02d}")
        if remaining > 0:
            self.timer_job = self.after(1000, self._tick)
        else:
            self.stop_timer()
            gameendsound.play()
            self.theend_game2()


    def stop_timer(self):
        self.timer_running = False
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None

    def end_game(self):
        if self.game_has_ended:
            return
        self.game_has_ended = True
        self.stop_timer()
        self.correct_sentence_label.configure(
            text=f"THE ANSWER IS\n{self.sentence}\nGAME OVER! PRESS NEW GAME TO RESTART."
        )
        self.answer_btn.configure(state="disabled")

        pygame.mixer.music.stop()
        
        gameoversound.play()



    def theend_game2(self):
        if self.game_has_ended:
            return
        self.game_has_ended = True
        self.stop_timer()
        self.correct_sentence_label.configure(
            text=f"THE ANSWER IS\n{self.sentence}\nGAME OVER"
        )
        self.answer_btn.configure(state="disabled")

        pygame.mixer.music.stop()
        
        



    def on_close(self):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            pygame.quit()
        except:
            pass
        self.destroy()


            
ESBApp().mainloop()