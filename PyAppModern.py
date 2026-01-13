import os, sys, time, random
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import pygame
import string

start_time = None


# -------------------- util --------------------
def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def norm(s: str) -> str:
    return s.replace("’", "'").replace("‘", "'").replace("`", "'").strip()

# -------------------- sounds --------------------
try:
    # buffer を既定より大きくして音声処理を安定させる
    pygame.mixer.init(buffer=4096)
    pygame.mixer.set_num_channels(32)  # 同時再生チャンネル数も増やす（任意）
except pygame.error as e:
    print(f"[AUDIO] mixer init error: {e}")

def _load_wav(path, vol=0.5):
    try:
        snd = pygame.mixer.Sound(path)
        snd.set_volume(vol)
        return snd
    except pygame.error:
        class _Dummy:
            def play(self): pass
            def set_volume(self, v): pass
        return _Dummy()


startsound    = _load_wav(resource_path("startsound.wav"), 0.9)
correctsound  = _load_wav(resource_path("correctsound.wav"), 0.9)
wrongsound    = _load_wav(resource_path("wrongsound.wav"), 0.9)
giveupsound   = _load_wav(resource_path("giveupsound.wav"), 0.9)
gameoversound = _load_wav(resource_path("gameoversound.wav"), 0.9)
gameendsound  = _load_wav(resource_path("gameendsound.wav"), 0.9)
shufflesound  = _load_wav(resource_path("shufflesound.wav"), 0.9)

# --- BGM 候補（曲のロードは再生時に行う） ---
bgm_candidates = [
    resource_path("battlebgm1.mp3"),
    resource_path("battlebgm1.mp3"),
    resource_path("battlebgm1.mp3"),
    resource_path("battlebgm1.mp3"),
]
bgm_files = [p for p in bgm_candidates if os.path.exists(p)]
if not bgm_files:
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

            

# 難易度のデフォルト閾値（実装仕様）
EASY_MAX = 5       # <= 6 語 → easy
BEGINNER_MAX = 8       # <= 8 語 → Beginner
HIGH_BEGINNER_MIN = 8       # <= 10 語 → High_Beginner
HIGH_BEGINNER_MAX = 10       # <= 10 語 → High_Beginner
INTERMEDIATE_MIN = 10  # <= 10 語 → Intermediate
INTERMEDIATE_MAX = 14  # <= 14 語 → Intermediate
ADVANCED_MIN = 14          # >= 14 語 → Advanced

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

# ------- 一括フォントスケール（ここだけ変えれば大きさが全体調整できます） -------
UI_SCALE = 1.0
def sz(base):  # baseに倍率を掛ける
    return max(10, int(base * UI_SCALE))

class ESBApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ENGLISH SENTENCE BUILDER")
        self.geometry("1150x760")

        # ① Tkが初期化された後 ← ここが重要
        self.challenge_mode = tk.IntVar(value=0)

        self.configure(fg_color=BG)
        # 追加: クラスの __init__ で
        self._in_tick = False
        # __init__ 冒頭のラベル作成前あたりに
        self.timer_text = tk.StringVar(value="TIME: 15:00")

        


        # ---- fonts（主要ラベルはCTkFontで統一） ----
        self.font_title     = ctk.CTkFont(family="Yu Gothic UI", size=sz(20), weight="bold")
        self.font_timer     = ctk.CTkFont(family="Segoe UI",     size=sz(20), weight="bold")
        self.tile_font      = ctk.CTkFont(family="Yu Gothic UI", size=sz(28), weight="bold")  # タイル
        self.font_q_small   = ctk.CTkFont(family="Segoe UI",     size=sz(18))
        self.font_result    = ctk.CTkFont(family="Segoe UI",     size=sz(28), weight="bold")  # 回答欄（大）
        self.font_status    = ctk.CTkFont(family="Segoe UI",     size=sz(18), weight="bold")  # メッセージ
        self.font_correct   = ctk.CTkFont(family="Segoe UI",     size=sz(24))                 # 正解文（大）
        self.font_avg       = ctk.CTkFont(family="Segoe UI",     size=sz(20), weight="bold")  # AVG/正答率（大）
        self.font_score     = ctk.CTkFont(family="Segoe UI",     size=sz(22), weight="bold")  # SCORE（大）
        self.font_count     = ctk.CTkFont(family="Segoe UI",     size=sz(20), weight="bold")  # COUNT（大）
        self.font_button    = ctk.CTkFont(family="Segoe UI",     size=sz(18), weight="bold")
        self.font_section   = ctk.CTkFont(family="Yu Gothic UI", size=sz(16), weight="bold")
        self.font_hint      = ctk.CTkFont(family="Segoe UI",     size=sz(16))

        # ---- state ----
        self.sentences = SENTENCES
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

        # strike（ミス×3 or GIVE UP）合算。5で終了
        self.strike_count = 0

        # 語数
        self.word_counts = [len(s.split()) for s in self.sentences]

        # 出題順管理
        
        self.last_candidates = None
        self.last_level = None

        self.last_seed = None
        self.current_seed = None
        self.order = []
        self.order_pos = 0

        # BGM ON/OFF
        self.bgm_on = ctk.StringVar(value="on")

        # 出題モード & 難易度
        self.mode_var = ctk.StringVar(value="random")     # "same"/"random"
        self.level_var = ctk.StringVar(value="random")    # "beginner"/"intermediate"/"normal"/"advanced"


        # ---- time-limit state (new_game で使うので先に作る) ----
        self.game_minutes = tk.IntVar(master=self, value=15)  # 既定15分
        self.time_rbs = []
        self.time_left = self.game_minutes.get() * 60
        self.timer_job = None






        # scoring
        self.score = 0
        self.last_gain = 0

        self._build_ui()
        self.new_game(first=True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # __init__ の最後あたりで
        self.configure(cursor="arrow")

        # スリープ・最小化復帰対策
        self.bind("<FocusIn>", self.reset_audio)


# ---------- audio reset (sleep / focus restore) ----------
    def reset_audio(self, event=None):
        try:
            # いったん完全停止
            try:
                pygame.mixer.music.stop()
            except:
                pass

            pygame.mixer.quit()
            pygame.mixer.init(buffer=4096)
            pygame.mixer.set_num_channels(32)

            # BGM が ON なら再開
            if self.bgm_on.get() == "on" and not self.game_has_ended:
                self.play_bgm(restart=True)

        except Exception as e:
            print("[AUDIO] reset error:", e)





    # ---------- BGM helper ----------
    def play_bgm(self, restart=False):
        if getattr(self, "game_has_ended", False):
            return
        if self.bgm_on.get() != "on" or not bgm_files:
            return
        try:
            if pygame.mixer.music.get_busy():
                if restart:
                    pygame.mixer.music.stop()
                else:
                    return
            track = random.choice(bgm_files)
            pygame.mixer.music.load(track)
            pygame.mixer.music.set_volume(0.2)
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"[BGM] play error: {e}")

    def stop_bgm(self):
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass

    def on_bgm_toggle(self):
        if getattr(self, "game_has_ended", False):
            self.stop_bgm()
            return
        if self.bgm_on.get() == "on":
            self.play_bgm(restart=True)
        else:
            self.stop_bgm()





    # ---------- 難易度フィルタ ----------
    def _candidate_indices_by_level(self):
        level = self.level_var.get()

        if level == "easy":
            return [i for i, wc in enumerate(self.word_counts) if wc <= EASY_MAX]
        elif level == "beginner":
            return [i for i, wc in enumerate(self.word_counts) if wc <= BEGINNER_MAX]
        
        elif level == "high_beginner":
            return [ i for i, wc in enumerate(self.word_counts)
        if HIGH_BEGINNER_MIN <= wc <= HIGH_BEGINNER_MAX]
        
        
        elif level == "intermediate":
            return [ i for i, wc in enumerate(self.word_counts)
        if INTERMEDIATE_MIN <= wc <= INTERMEDIATE_MAX]


        elif level == "advanced":
            return [i for i, wc in enumerate(self.word_counts) if wc >= ADVANCED_MIN]
        else:
            return list(range(len(self.sentences)))

    # ---------- scoring helpers ----------
    def _time_bonus(self, dur):
        if dur <= 2:  return 24
        if dur <= 3:  return 21
        if dur <= 4:  return 18
        if dur <= 5:  return 15
        if dur <= 6:  return 12
        if dur <= 7:  return 10
        if dur <= 8:  return 9
        if dur <= 9:  return 8
        if dur <= 10: return 7
        if dur <= 15: return 6
        if dur <= 20: return 5
        if dur <= 25: return 4
        if dur <= 30: return 3
        if dur <= 35: return 2
        if dur <= 40: return 1

        return 0   # 30秒超を含め、それ以降は0
    

    def _base_points_on_success(self, wrongs):
        return 5 if wrongs == 0 else 3 if wrongs == 1 else 1

    def _update_score_ui(self):
        sign = "+" if self.last_gain >= 0 else ""
        self.score_label.configure(text=f"SCORE: {self.score} ({sign}{self.last_gain} pts)")
        self.strike_label.configure(text=f"COUNT: {self.strike_count}/5")



    def _length_multiplier(self, word_count: int) -> float:
     
        if word_count <= 2:
            return 0.50
        if word_count <= 3:
            return 0.60
        if word_count <= 4:
            return 0.80
        if word_count <= 5:
            return 1.00
        if word_count <= 7:
            return 1.20
        if word_count <= 9:
            return 1.50
        if word_count <= 11:
            return 1.90
        if word_count <= 13:
            return 2.40
        if word_count <= 14:
            return 3.00
        if word_count <= 15:
            return 3.70
        if word_count <= 16:
            return 4.50
        if word_count <= 17:
            return 5.40
        if word_count <= 18:
            return 6.40
        if word_count <= 19:
            return 7.50
        if word_count <= 20:
            return 8.70
        return 8.70


    # ---------- UI ----------
    def _build_ui(self):
        # Header
        top = ctk.CTkFrame(self, corner_radius=0, fg_color="#D4ECD9")
        top.pack(fill="x")
        ctk.CTkLabel(top, text="ENGLISH SENTENCE BUILDER",
                     font=self.font_title).pack(side="left", padx=16, pady=12)
       
        # _build_ui のラベルをこれに差し替え
        self.timer_label = ctk.CTkLabel(top, textvariable=self.timer_text, font=self.font_timer)


        self.timer_label.pack(side="right", padx=16)

        self.timer_default_color = self.timer_label.cget("text_color") or None

        # Body
        body = ctk.CTkFrame(self, fg_color=BG)
        body.pack(fill="both", expand=True, padx=PAD, pady=PAD)

        # Left panel (game area)
        left = ctk.CTkFrame(body, fg_color=CARD, corner_radius=RADIUS)
        left.pack(side="left", fill="both", expand=True, padx=(0, PAD))

        self.question_label = ctk.CTkLabel(
            left, text="MAKE THE CORRECT SENTENCES!", font=self.font_q_small, text_color="#2E2E2E"
        )
        self.question_label.pack(anchor="w", padx=18, pady=(0, 6))

        self.result_label = ctk.CTkLabel(
            left, text="HERE IS YOUR ANSWER", font=self.font_result, text_color="#2E2E2E"
        )
        self.result_label.pack(fill="x", padx=18, pady=(0, 8))

        # Word pool
        self.pool = ctk.CTkFrame(left, fg_color=CARD)
        self.pool.pack(fill="x", padx=18, pady=(4, 4))

        # Buttons row (Answer / Shuffle / Clear)
        btns = ctk.CTkFrame(left, fg_color=CARD)
        btns.pack(fill="x", padx=18, pady=(10, 18))
        self.answer_btn = ctk.CTkButton(
            btns, text="ANSWER", font=self.font_button, width=180, height=56,
            fg_color=PRIMARY, hover_color=PRIMARY_HOVER, command=self.check_answer
        )
        self.answer_btn.pack(side="right")
        ctk.CTkButton(btns, text="SHUFFLE", font=self.font_button, command=self.shuffle_words).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text="CLEAR",   font=self.font_button, command=self.clear_answer).pack(side="left", padx=(0, 8))

        # Status
        self.message_label = ctk.CTkLabel(left, text="", text_color="#C0392B", font=self.font_status)
        self.message_label.pack(anchor="w", padx=18, pady=(0, 4))
        self.correct_sentence_label = ctk.CTkLabel(left, text="", text_color="#1B7A33", font=self.font_correct)
        self.correct_sentence_label.pack(anchor="w", padx=18, pady=(0, 2))

        # 正答率＆平均
        self.avg_time_label = ctk.CTkLabel(
            left, text="CORRECT: 0/0 | AVG: 0.0 sec | 0%", text_color="#1B4F72", font=self.font_avg
        )
        self.avg_time_label.pack(anchor="w", padx=18, pady=(0, 6))

        # スコア表示（合計と直近得点）
        self.score_label = ctk.CTkLabel(
            left, text="SCORE: 0 (+0 pts)", text_color="#2C3E50", font=self.font_score
        )
        self.score_label.pack(anchor="w", padx=18, pady=(0, 6))

        # 失敗カウント表示
        self.strike_label = ctk.CTkLabel(
            left, text="COUNT: 0/5", text_color="#7D3C98", font=self.font_count
        )
        self.strike_label.pack(anchor="w", padx=18, pady=(0, 10))

        self.praise_label = ctk.CTkLabel(
        left, text="", text_color="#1B7A33", font=self.font_status
        )
        self.praise_label.pack(anchor="w", padx=18, pady=(0, 8))



        # Right panel (controls)
        right = ctk.CTkFrame(body, fg_color=CARD, corner_radius=RADIUS, width=320)
        right.pack(side="right", fill="y")

        # --- TIME LIMIT ---
        ctk.CTkLabel(right, text="TIME LIMIT", font=self.font_section).pack(anchor="w", padx=16, pady=(12, 4))

        time_wrap = ctk.CTkFrame(right, fg_color=CARD)
        time_wrap.pack(anchor="w", padx=12, pady=(0, 10))

# 2x2 のグリッドで配置（横幅が狭くても崩れない）
        values = [(5, "5 min"), (10, "10 min"), (15, "15 min"), (20, "20 min")]
        for i, (val, text) in enumerate(values):
            r, c = divmod(i, 2)  # row 0-1, col 0-1
            rb = ctk.CTkRadioButton(
            time_wrap,
            text=text,
            variable=self.game_minutes,
            value=val,
            command=self._on_time_changed
            )
            rb.grid(row=r, column=c, padx=6, pady=4, sticky="w")
            self.time_rbs.append(rb)

# 列幅調整（任意）
        time_wrap.grid_columnconfigure(0, weight=1)
        time_wrap.grid_columnconfigure(1, weight=1)


        ctk.CTkLabel(right, text="CAPITAL LETTER HINT", font=self.font_section).pack(anchor="w", padx=16, pady=(12, 4))

        self.setting_frame = ctk.CTkFrame(right, fg_color=CARD)
        self.setting_frame.pack(anchor="w", padx=12, pady=(0, 10))

        ctk.CTkRadioButton(
            self.setting_frame,
            text="ON",
            variable=self.challenge_mode,
            value=0
        ).pack(side="left", padx=8, pady=2)

        ctk.CTkRadioButton(
            self.setting_frame,
            text="OFF",
            variable=self.challenge_mode,
            value=1
        ).pack(side="left", padx=8, pady=2)




        ctk.CTkLabel(right, text="QUESTION STYLE", font=self.font_section).pack(anchor="w", padx=16, pady=(16, 6))
        style_row = ctk.CTkFrame(right, fg_color=CARD)
        style_row.pack(anchor="w", padx=12, pady=(0, 10))
        ctk.CTkRadioButton(style_row, text="SAME SEQUENCE",   variable=self.mode_var, value="same").pack(anchor="w", pady=(0, 8))
        ctk.CTkRadioButton(style_row, text="RANDOM SEQUENCE", variable=self.mode_var, value="random").pack(anchor="w")

        ctk.CTkLabel(right, text="BGM", font=self.font_section).pack(anchor="w", padx=16, pady=(12, 4))
        bgm_row = ctk.CTkFrame(right, fg_color=CARD)
        bgm_row.pack(anchor="w", padx=12, pady=(0, 10))
        ctk.CTkRadioButton(bgm_row, text="ON",  variable=self.bgm_on, value="on",
                           command=self.on_bgm_toggle).pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(bgm_row, text="OFF", variable=self.bgm_on, value="off",
                           command=self.on_bgm_toggle).pack(side="left")

        # --- LEVEL (Easy を最上段に分離) ---
        ctk.CTkLabel(right, text="LEVEL", font=self.font_section).pack(anchor="w", padx=16, pady=(12, 4))
        level_wrap = ctk.CTkFrame(right, fg_color=CARD)
        level_wrap.pack(anchor="w", padx=12, pady=(0, 10), fill="x")

        # Easy 用フレーム（最上段）
        row_easy = ctk.CTkFrame(level_wrap, fg_color=CARD)
        row_easy.pack(fill="x", pady=2)
        ctk.CTkRadioButton(row_easy, text="Easy", variable=self.level_var, value="easy").pack(side="left", padx=6)
        ctk.CTkRadioButton(row_easy, text= "High_Beginner", variable=self.level_var, value="high_beginner").pack(side="left", padx=6)

        # その下に2段（Beginner〜Advanced）
        row1 = ctk.CTkFrame(level_wrap, fg_color=CARD)
        row1.pack(fill="x", pady=2)
        row2 = ctk.CTkFrame(level_wrap, fg_color=CARD)
        row2.pack(fill="x", pady=2)

        ctk.CTkRadioButton(row1, text="Beginner",     variable=self.level_var, value="beginner").pack(side="left", padx=6)
        ctk.CTkRadioButton(row1, text="Intermediate", variable=self.level_var, value="intermediate").pack(side="left", padx=6)
        ctk.CTkRadioButton(row2, text="Random",       variable=self.level_var, value="random").pack(side="left", padx=6)
        ctk.CTkRadioButton(row2, text="Advanced",         variable=self.level_var, value="advanced").pack(side="left", padx=6)
        

        ctrl = ctk.CTkFrame(right, fg_color=CARD)
        ctrl.pack(fill="x", padx=12, pady=(20, 10))

        # ★ self.giveup_btn に代入
        self.giveup_btn = ctk.CTkButton(
        ctrl, text="GIVE UP", font=self.font_button, command=self.give_up
)
        self.giveup_btn.pack(fill="x", pady=(0, 8))

        # NEW GAME ボタンはそのまま
        ctk.CTkButton(
        ctrl, text="NEW GAME", font=self.font_button, command=self.new_game
).pack(fill="x")

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
        self.result_label.configure(text=" ".join(self.selected) if self.selected else "HERE IS YOUR CHALLENGE")
        pct = (self.correct_count / self.question_count * 100) if self.question_count else 0.0
        self.avg_time_label.configure(
            text=f"CORRECT: {self.correct_count}/{self.question_count} | AVG: {self._avg_time():.1f} sec | {pct:.0f}%"
        )
        self._update_score_ui()

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

    def _count_strike_and_next(self, reason_text=""):
        self.strike_count += 1
        if reason_text:
            self.message_label.configure(text=f"{reason_text} → COUNT {self.strike_count}/5", text_color="#C0392B")
        self._update_score_ui()
        if self.strike_count >= 5:
            self.end_game()
        else:
            self.reset_round()

    def _fail_current_round(self):
        self.last_gain = -15
        self.score += -15
        self.question_count += 1
        self.correct_sentence_label.configure(text=f"THE ANSWER IS\n{self.sentence}")
        self._update_score_ui()
        self._count_strike_and_next("MISS x3 → -15 pts")

    
    def get_sound_count(self,elapsed):
        if elapsed < 4.0:
            return 3      # かなり速い
        elif elapsed < 7.0:
            return 2      # 少し速い
        else:
            return 1      # 通常

    def play_correct_sound(self, count):

        if count >= 1:
            correctsound.play()
            pygame.time.delay(100)

        if count >= 2:
            correctsound.play()
            pygame.time.delay(100)

        if count >= 3:
            correctsound.play()
            pygame.time.delay(100)
       

    def normalize_sentence(self, s: str) -> str:
        s = s.lower()
        
        return s


    def _get_answer_for_check(self):
        """
        正解判定用の文を返す
        """
        s = self.sentence

        if self.challenge_mode.get() == 1:  # NO HINTS / Challenge
            s = s.lower()
            
        return s



    def check_answer(self):

        user = " ".join(self.selected)

        answer = self._get_answer_for_check()

        if norm(user) == norm(answer):

        
        # ── 正解 ────────────────────────────────

            solve_time = time.perf_counter() - self.round_start_time

            
            count = self.get_sound_count(solve_time)
            self.play_correct_sound(count)


            self.correct_count += 1
            self.question_count += 1
         

            dur = solve_time
            base = self._base_points_on_success(self.wrong_attempts)  # 既存
            bonus = self._time_bonus(dur)                              # 既存

            wc = len(self.words)                                       # 語数
            mult = self._length_multiplier(wc)                         # 倍率

            raw = base + bonus
            gained = int(round(raw * mult))

            self.last_gain = gained
            self.score += gained

            self.message_label.configure(
            text=f"+{gained} pts  (base {base}, time +{bonus}, len {wc} ×{mult:.2f}, {dur:.1f}s, wrong {self.wrong_attempts})",
            text_color="#16A085"
        )
            self.correct_sentence_label.configure(text=f"CORRECT!  Solve Time: {solve_time:.2f} sec \n{self.sentence}")

            
        



            if self.round_start_time:
               self.solve_times.append(dur)

            self.wrong_attempts = 0
            self._update_score_ui()
            self.reset_round()
        else:
        # ── 不正解 ──────────────────────────────
            self.wrong_attempts += 1
            wrongsound.play()
            self.correct_sentence_label.configure(text="")

            if self.wrong_attempts >= 3:
               self._fail_current_round()
               self.message_label.configure(text="")
               giveupsound.play()
            else:
               self.shuffle_words()
               self.message_label.configure(
                text=f"WRONG! TRY AGAIN ({self.wrong_attempts}/3)",
                text_color="#C0392B"
            )
               
            

    def give_up(self):
            self.message_label.configure(text="", text_color="#5BE1BE")
            self.give_up_count += 1
            giveupsound.play()

            self.last_gain = -20
            self.score += -20
            self._update_score_ui()

            self.correct_sentence_label.configure(
        text=f"THE ANSWER IS\n{self.sentence}"
    )
            self.question_count += 1
            self._count_strike_and_next("GIVE UP → -20 pts")


    def _force_end_by_giveup(self):
         self.stop_timer()
         self.end_game()



    def new_game(self, first=False):
    # --- BGM/フラグ類 ---
        startsound.play()
        self.game_has_ended = False
        self.stop_bgm()
        self.play_bgm(restart=True)

        self.timer_label.configure(text_color=self.timer_default_color)
        self.praise_label.configure(text="")
                                    
    # --- ボタン/カウンタ初期化 ---
        self.answer_btn.configure(state="normal")
        self.giveup_btn.configure(state="normal")   # 再開時に有効化
        self.give_up_count = 0
        self.wrong_attempts = 0
        self.strike_count = 0

        self.correct_sentence_label.configure(text="")
        self.message_label.configure(text="")

        self.correct_count = 0
        self.question_count = 0
        self.solve_times.clear()
        self.score = 0
        self.last_gain = 0
        self._update_score_ui()

        self.avg_time_label.configure(text=f"CORRECT: 0/0 | AVG: 0.0 sec | 0%")


        current_level = self.level_var.get()

        if current_level != self.last_level:
            # レベルが変わったら same sequence をリセット
            self.last_seed = None
            self.last_candidates = None

        self.last_level = current_level




    # --- 出題候補の作成 ---
        candidates = self._candidate_indices_by_level()
        if not candidates:
           messagebox.showwarning("LEVEL FILTER", "No sentence matches the selected level. Back to Normal.")
           self.level_var.set("normal")
           candidates = list(range(len(self.sentences)))

        if self.mode_var.get() == "same" and (self.last_seed is not None):
           self.current_seed = self.last_seed
           candidates = self.last_candidates[:]   # ← 重要
        else:
           self.current_seed = random.randrange(2**31)
           self.last_seed = self.current_seed
           self.last_candidates = candidates[:]   # ← 保存

        rng = random.Random(self.current_seed)
        self.order = candidates[:]
        rng.shuffle(self.order)
        self.order_pos = 0



    # --- 制限時間の適用（★ここが今回の肝） ---
        self._set_time_controls_enabled(False)                # ゲーム中は変更不可
        self.time_left = self.game_minutes.get() * 60         # ラジオ選択分
        self._update_timer_label(self.time_left)
        self.stop_timer()                                     # 念のため二重起動防止
        self.start_timer()                                    # カウントダウン開始

    # --- 1問目のセット ---
        self.reset_round()

        



    
    def reset_round(self):
        self.message_label.configure(text="", text_color="#5BE1BE")
        self.selected.clear()
        self.used.clear()
        self._pick_sentence()
        self.wrong_attempts = 0

        self.round_start_time = time.perf_counter()
    # 重いUI再構築は idle に回す
        self.after_idle(self._rebuild_round)

    def _rebuild_round(self):
        self._build_pool()
        self._update_result()



    def _make_challenge_sentence(self, sentence):
        s = sentence.lower()                  # 全部小文字
        
        return s

    
        

    def _pick_sentence(self):
        if self.order_pos >= len(self.order):
            self.end_game()
            return
        idx = self.order[self.order_pos]
        self.order_pos += 1
        self.sentence = self.sentences[idx]

    # 表示用だけを切り替える
        if self.challenge_mode.get() == 1:
            display_sentence = self._make_challenge_sentence(self.sentence)
        else:
            display_sentence = self.sentence

        self.words = display_sentence.split()
        self.shuffled = self.words[:]
        random.shuffle(self.shuffled)
        self.question_label.configure(text="MAKE CORRECT SENTENCES!")

        
        self.round_start_time = time.perf_counter()

    def start_timer(self):
        """タイマー開始（New Game 時に呼ぶ）"""
        self.stop_timer()  # 二重起動防止
        self.timer_job = self.after(1000, self._tick)

    
    def _tick(self):
        """1秒ごとのカウントダウン処理"""
        if self._in_tick:
            # 何かの理由で再入しそうになったらスキップ
            self.timer_job = self.after(1000, self._tick)
            return

        self._in_tick = True
        try:
            if getattr(self, "game_has_ended", False):
                self.stop_timer()
                return

            self.time_left -= 1
            self._update_timer_label(self.time_left)
            
            # 60秒→オレンジ / 10秒→赤 / それ以外→元色
            if self.time_left <= 10:
               self.timer_label.configure(text_color="#DC0B0B")   # 赤
            elif self.time_left <= 60:
               self.timer_label.configure(text_color="#EDB90C")   # オレンジ
            else:
               self.timer_label.configure(text_color=self.timer_default_color)  # 元色

            
            if self.time_left <= 0:
               self.end_game(time_up=True)
               self.stop_timer()
               return

            # 次の tick を予約
            self.timer_job = self.after(1000, self._tick)
        finally:
            self._in_tick = False







    def stop_timer(self):
            """タイマー停止"""
            if self.timer_job is not None:
                try:
                    self.after_cancel(self.timer_job)
                except Exception:
                    pass
            self.timer_job = None

    

    def end_game(self, time_up: bool = False):
    # 重複終了ガード
        if self.game_has_ended:
           return
        self.game_has_ended = True

    # タイマー停止＆次回のために時間設定UIを戻す
        self.stop_timer()
        self._set_time_controls_enabled(True)

    # 乱数シード保存（sameモード再現用）
        self.last_seed = self.current_seed

    # UI・サウンド
        self.answer_btn.configure(state="disabled")
        self.giveup_btn.configure(state="disabled")
        self.stop_bgm()
        


        if time_up:
            gameendsound.play()
            praise = self._final_praise_en(self.score)
            self.correct_sentence_label.configure(
                text=(f"TIME UP!\n"
                  f"{praise}\n"
                  f"SCORE: {self.score}\n"
                  "PRESS NEW GAME TO RESTART.\n"
                  f"THE ANSWER IS\n{self.sentence}")
            )
        else:
            gameoversound.play()
            self.correct_sentence_label.configure(
                text=(f"SCORE: {self.score}\n"
                  "GAME OVER! PRESS NEW GAME TO RESTART.\n"
                  f"THE ANSWER IS\n{self.sentence}")
            )


   
    


    def theend_game2(self):
        if self.game_has_ended:
            return
        self.game_has_ended = True
        self.stop_timer()
        self.last_seed = self.current_seed

        self.correct_sentence_label.configure(
            text=(f"THE ANSWER IS\n{self.sentence}\n"
                  f"SCORE: {self.score}\n"
                  "GAME OVER")
        )
        self.answer_btn.configure(state="disabled")
        self.giveup_btn.configure(state="disabled")   # ★ 追加（時間切れ終了でも無効化）
        self.stop_bgm()




        # === 2) 制御系ユーティリティ ===
    def _set_time_controls_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for rb in self.time_rbs:
            rb.configure(state=state)

    def _on_time_changed(self):
    # ラジオを切り替えたとき（ゲーム開始前の想定）
        mins = self.game_minutes.get()
        self.time_left = mins * 60
        self._update_timer_label(self.time_left)

    

    def _update_timer_label(self, secs: int):
        if secs < 0:
           secs = 0
        m, s = divmod(secs, 60)
        self.timer_text.set(f"TIME: {m:02d}:{s:02d}")

    

    def _final_praise_en(self, score: int) -> str:
        """
        Time Up 専用：最終スコアに応じた英語の褒め言葉を返す。
        15分基準で正規化して判定。難易度ラジオボタンに応じて倍率を適用。
        Easy=1.0 / Beginner=1.25 / Intermediate=1.5 / Normal=1.75
        """
        # 制限時間（分）
        try:
            minutes = int(self.game_minutes.get())
        except Exception:
            minutes = 15
        minutes = max(1, minutes)

        # --- 難易度倍率（つづりゆらぎ対応）---
        try:
            lv = str(self.level_var.get()).strip().lower()
        except Exception:
            lv = "random"  # デフォルトをNormalに

        mult_table = {
            "easy": 1.00,
            "beginner": 1.25,
            "high_beginner": 1.375,
            "intermediate": 1.50,
            "random": 1.75,
            "advanced": 2.0,
        }
        mult = mult_table.get(lv, 1.00)  # 未定義は等倍

        # 倍率を掛けてから 15分換算
        adjusted = int(round(score * mult))
        norm_score = int(round(adjusted * 15 / minutes))

        # ランク判定
        if norm_score >= 1400:
            options = ["RANK: AAA  Legendary focus! Unstoppable!", "RANK: AAA  Incredible! You crushed it!"]
        elif norm_score >= 1100:
            options = ["RANK: AA  Outstanding performance!", "RANK: AA  Top-tier play!"]
        elif norm_score >= 800:
            options = ["RANK: A  Excellent run! You're on fire!", "RANK: A  Great momentum!"]
        elif norm_score >= 500:
            options = ["RANK: B  Nice work! Steady and sharp!", "RANK: B  Well played!"]
        elif norm_score >= 200:
            options = ["RANK: C  Good effort! Keep it up!", "RANK: C  Solid progress!"]
        elif norm_score > 0:
            options = ["RANK: D  Solid start! Build on this!", "RANK: D  You're getting there!"]
        else:
            options = ["RANK: F  Tough round—but you've got this next time!", "RANK: F  Shake it off and come back stronger!"]

        return random.choice(options)




    def _update_praise(self):
        msg, color = self._praise_for_score(self.score)
        self.praise_label.configure(text=msg, text_color=color)

    def on_close(self):
        try:
            self.stop_bgm()
            pygame.mixer.quit()
            pygame.quit()
        except:
            pass
        self.destroy()

if __name__ == "__main__":

    ESBApp().mainloop()
