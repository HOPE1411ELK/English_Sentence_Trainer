import tkinter as tk
from tkinter import messagebox
import random
import time
import pygame
import os

# Pygameの初期化
pygame.init()
pygame.mixer.init()


# 効果音の読み込み
start_sound = pygame.mixer.Sound("startsound.wav")
correct_sound = pygame.mixer.Sound("correctsound.wav")
wrong_sound = pygame.mixer.Sound("wrongsound.wav")
giveup_sound = pygame.mixer.Sound("giveupsound.wav")
gameover_sound = pygame.mixer.Sound("gameoversound.wav")
gameend_sound = pygame.mixer.Sound("gameendsound.wav")
shuffle_sound = pygame.mixer.Sound("shufflesound.wav")

start_sound.set_volume(0.5)  # 30% の音量
correct_sound.set_volume(0.5)  # 30% の音量
wrong_sound.set_volume(0.5)  # 30% の音量
giveup_sound.set_volume(0.5)  # 30% の音量
gameover_sound.set_volume(0.4)  # 30% の音量
gameend_sound.set_volume(0.5)  # 30% の音量
shuffle_sound.set_volume(0.5)  # 30% の音量


# 音楽ファイルのリスト
bgm_files = ["battlebgm1.mp3", "battlebgm2.mp3", "battlebgm3.mp3", "battlebgm4.mp3"]
bgm_file = random.choice(bgm_files)  # ランダムに選択
pygame.mixer.music.load(bgm_file)
pygame.mixer.music.play(-1)  # -1 はループ再生
# 音量調節（0.5は50%の音量）
pygame.mixer.music.set_volume(0.07)

def play_bgm():
    bgm_file = random.choice(bgm_files)  # ランダムに選択
    pygame.mixer.music.load(bgm_file)
    pygame.mixer.music.play(-1)  # 無限ループ
    pygame.mixer.music.set_volume(0.07)

def stop_bgm():
    pygame.mixer.music.stop()

def start_app():
    create_buttons()       # ボタン作成
    start_new_game()       # 最初のゲームスタート
    start_timer()  # ←これを追加　タイマーが発動

# Function to load sentences from a file
def load_sentences_from_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            sentences = [line.strip() for line in file.readlines() if line.strip()]
            if not sentences:
                raise ValueError("File is empty")
            random.shuffle(sentences)
        return sentences
    except (FileNotFoundError, ValueError) as e:
        messagebox.showerror("ERROR", f"File read error: {e}")
        return []


# Load sentences
filename = "sentences.txt"
sentences = load_sentences_from_file(filename)

# Exit if no sentences loaded
if not sentences:
    messagebox.showwarning("WARNING", "The sentence list is empty. Please check your file.")
    exit()

# Game state variables
sentence_index = 0
sentence = ""
words = []
shuffled_words = []
selected_words = []
button_references = {}
used_indices = set()

game_start_time = time.time()
question_count = 0
correct_count = 0

# Create the main window
root = tk.Tk()
root.title("ENGLISH SENTENCE BUILDER")
root.geometry("1000x800")
root.configure(bg="lightgreen")

main_game_frame = tk.Frame(root, bg="lightgreen")
main_game_frame.pack(fill="both", expand=True)

# Frames for layout
top_frame = tk.Frame(main_game_frame, bg="lightgreen")
top_frame.pack(side=tk.TOP, fill=tk.X)

word_buttons_frame = tk.Frame(main_game_frame, bg="lightgreen")
word_buttons_frame.pack(expand=True)



# UI update functions
def update_result(update_ui=True):
    if selected_words:
        result_label.config(text=" ".join(selected_words))
    else:
        result_label.config(text="HERE IS YOUR ANSWER")

    # Show accuracy and correct/total count
    accuracy = (correct_count / question_count * 100) if question_count > 0 else 0
    accuracy_label.config(text=f"RATE: {accuracy:.2f}%")
    


# Game logic functions
def on_word_click(word, button_id):
    if button_id not in used_indices:
        selected_words.append(word)
        button = button_references[button_id]
        button.config(state=tk.DISABLED, bg="lightgray")
        used_indices.add(button_id)
        update_result()
    else:
        button_references[button_id].config(bg="lightgray")




def next_question():
    global sentence_index, question_count, used_indices, selected_words
    
    # 次の問題に進むための処理
    sentence_index += 1
    
def play_correct_sound():
    correct_sound.play()

def play_wrong_sound():
    wrong_sound.play()



def check_answer():
    global correct_count, question_count, sentence_index, used_indices, wrong_attempts
    user_answer = " ".join(selected_words)

    if user_answer == sentence:
        play_correct_sound()
        correct_sound.play()
        correct_count += 1
        question_count += 1  # 正解したときだけカウントを増やす
        wrong_attempts = 0  # 間違い回数リセット
# TRY AGAINメッセージを消す
        message_label.config(text="")

        update_result(update_ui=True)
        correct_sentence_label.config(text=f"CORRECT！\n" + sentence)  # 正解時は緑色


# 平均時間表示
        elapsed_total = int(time.time() - game_start_time)
        avg_time_per_question = elapsed_total / correct_count
        avg_time_label.config(text=f"CORRECT: {correct_count}/{question_count} | AVG: {avg_time_per_question:.1f} sec")


        start_new_game()
        
    else:
        play_wrong_sound()
        wrong_attempts += 1
# ✅ TRY AGAIN表示 → CORRECT！を消す
        correct_sentence_label.config(text="")


        if wrong_attempts >= 3:
            give_up()
            # ▼ここを追加：3回目でメッセージを消す
            message_label.config(text="")
        else:
            shuffle_words()
            show_message(f"WRONG！ TRY AGAIN (Attempts: {wrong_attempts}/3)", "red")  # 不正解時は赤色
        update_result(update_ui=True)

wrong_attempts = 0  # 不正解カウント初期化
        
        
    

def show_message(text, color="black"):
    # 画面上のメッセージラベルに色付きで表示
    message_label.config(text=text, fg=color)


def shuffle_words():
    global shuffled_words, selected_words, used_indices
    random.shuffle(shuffled_words)
    selected_words = []
    used_indices.clear()
    restore_buttons()
    update_result()
    shuffle_sound.play()


# ウィンドウとフレーム作成

root.configure(bg="lightgreen")
button_frame = tk.Frame(root, bg="lightgreen", height=300)
button_frame.config(bg="lightgreen")
button_frame.pack()

# メッセージ表示用のラベル
message_label = tk.Label(root, text="", fg="black")
message_label.pack()

# ボタンの初期化
answer_btn = None
shuffle_btn = None
give_up_btn = None
new_game_btn = None

# カウント変数初期化
give_up_count = 0

def new_game():
    global give_up_count, game_has_ended, timer_running, game_start_time
    give_up_count = 0    # GIVE UPカウントをリセット！
    game_has_ended = False   # ★これを必ずリセットする
    timer_running = False
    stop_timer()             # ★既存タイマーを止める
    game_start_time = time.time()  # ★新しいゲームの時間をセット
    start_timer()            # ★新しいタイマーを開始
    reset_game()         # ゲームリセット
    start_new_game()     # 新しいゲーム開始
    show_message("NEW GAME STARTED!", "blue")
    enable_buttons()     # ボタンを再有効化
    update_timer()
    play_bgm()
    # ★ 成績カウンターをリセット
    correct_count = 0
    question_count = 0
    avg_time_label.config(text="CORRECT: 0/0 | AVG: 0.0 sec")

def enable_buttons():
    # 全ボタンを復活させる関数
    global answer_btn, shuffle_btn, give_up_btn, new_game_btn

    # 各ボタンが存在するか確認してから有効化
    if answer_btn is not None:
        answer_btn.config(state="normal")
    if shuffle_btn is not None:
        shuffle_btn.config(state="normal")
    if give_up_btn is not None:
        give_up_btn.config(state="normal")
    if new_game_btn is not None:
        new_game_btn.config(state="normal")

    # GUIを即座に更新
    button_frame.update_idletasks()
    root.update_idletasks()



def reset_game():
    global give_up_count
    give_up_count = 0
    
    # フレーム内の全ウィジェット削除して再作成
    for widget in button_frame.winfo_children():
        widget.destroy()
        
    create_buttons()   # ボタン再作成
    start_new_game()   # 新ゲーム開始
    root.update_idletasks()
    global question_count, correct_count, game_start_time, sentence_index
    question_count = 0
    correct_count = 0
    sentence_index = -1
    game_start_time = time.time()

    



def show_message(text, color="black"):
    message_label.config(text=text, fg=color)

timer_running = False
game_has_ended = False
timer_job = None  # after()のIDを保持

def start_timer():
    global timer_running, game_start_time
    timer_running = True
    game_start_time = time.time()
    # 初期値を即表示
    timer_label.config(text=f"TIME: {total_time_limit//60:02d}:00")
    update_timer()

def stop_timer():
    global timer_running
    timer_running = False
if timer_job:
        root.after_cancel(timer_job)  # 予約をキャンセル
        timer_job = None

def force_end_game_due_to_giveup():
    stop_timer()      # ここでタイマーを止める
    end_game()        # 直接終了処理を呼ぶ


def give_up():
    global question_count, give_up_count,game_start_time
    give_up_count += 1
    giveup_sound.play()
# TRY AGAINメッセージを消す
    message_label.config(text="")
    if give_up_count >= 5:
        
        
        disable_buttons()  # 他のボタン無効化
        pygame.mixer.music.stop()
        gameover_sound.play()
        force_end_game_due_to_giveup()  # 修正: 直接終了処理
 
    else:
        correct_sentence_label.config(text=f"THE ANSWER IS \n" + sentence)
        question_count += 1
        start_new_game()

game_has_ended = False

def end_game():
    global game_has_ended, timer_running
    if game_has_ended:
        return  # すでに実行済みなら何もしない
    game_has_ended = True
    timer_running = False  # タイマーを止める
    try:
        gameend_sound.play()
    except:
        pass  # 音が重複しても落ちないよう保険
    correct_sentence_label.config(text=f"THE ANSWER IS \n" + sentence + "\n GAME OVER! PRESS NEW GAME TO RESTART.")  # ギブアップ時に答えを表示
    
    answer_btn.config(state='disabled')
    shuffle_btn.config(state='disabled')
    give_up_btn.config(state='disabled')
    stop_bgm()


timer_job = None  # グローバルで管理

def update_timer():
    global timer_running, game_start_time
    if not timer_running:
        return  # タイマー停止中なら何もしない

    elapsed_time = int(time.time() - game_start_time)
    remaining_time = max(0, total_time_limit - elapsed_time)
    minutes, seconds = divmod(remaining_time, 60)
    
    timer_label.config(text=f"TIME: {minutes:02d}:{seconds:02d}", bg="lightgreen")

    if remaining_time > 0:
        root.after(1000, update_timer)
    else:
        stop_timer()
        end_game()

def stop_timer():
    global timer_running, timer_job
    timer_running = False
    if timer_job:
        root.after_cancel(timer_job)
        timer_job = None







def disable_buttons():
    # ボタンが作成されているか確認してから無効化
    global answer_btn, shuffle_btn, give_up_btn, new_game_btn
    
    if answer_btn is not None:
        answer_btn.config(state="disabled")
    if shuffle_btn is not None:
        shuffle_btn.config(state="disabled")
    if give_up_btn is not None:
        give_up_btn.config(state="disabled")
    if new_game_btn is not None:
        new_game_btn.config(state="normal")
        
    # 明示的に更新して反映させる
    button_frame.update_idletasks()
    root.update_idletasks()

def reset_buttons():
    for widget in button_frame.winfo_children():
        widget.destroy()
    create_buttons()

def new_game_action():
    start_new_game()
    reset_buttons() 
    
def create_buttons():
    global answer_btn, shuffle_btn, give_up_btn, new_game_btn
    
    button_frame.pack(expand=False)

    answer_btn = tk.Button(button_frame, text="ANSWER", command=check_answer, font=("Helvetica", 25, "bold"), width=10,  bg="green", fg="white", relief="raised", bd=5)
    answer_btn.grid(row=0, column=1, padx=0, pady=(10, 0))

    shuffle_btn = tk.Button(button_frame, text="SHUFFLE", command=shuffle_words, font=("Helvetica", 16), width=10)
    shuffle_btn.grid(row=1, column=0, padx=10, pady=(10, 0))

    give_up_btn = tk.Button(button_frame, text="GIVE UP", command=give_up, font=("Helvetica", 16), width=10)
    give_up_btn.grid(row=1, column=1, padx=10, pady=(10, 0))

    new_game_btn = tk.Button(button_frame, text="NEW GAME", command=new_game, font=("Helvetica", 16), width=10)
    new_game_btn.grid(row=1, column=2, padx=10, pady=(10, 0))

    
    






    

def restore_buttons():
    global button_references
    button_references = {}
    for widget in word_buttons_frame.winfo_children():
        widget.destroy()

    def create_button(word, index, row, col):
        btn = tk.Button(word_buttons_frame, text=word, font=("Helvetica", 20))
        btn.config(command=lambda w=word, i=index: on_word_click(w, i))
        btn.grid(row=row, column=col, padx=5, pady=5)
        button_references[index] = btn

    for i, word in enumerate(shuffled_words):
        create_button(word, i, i // 4, i % 4)





def start_new_game():
    global sentence_index, sentence, words, shuffled_words, selected_words, used_indices, wrong_attempts
    wrong_attempts = 0  # 新しいゲーム開始時に間違いカウントをリセット

    mode = mode_var.get()

    if mode == "sequential":
        sentence_index += 1
        if sentence_index >= len(sentences):
            end_game()
            return  # ← 関数内、インデントもOK
        sentence = sentences[sentence_index]

    elif mode == "random":
        sentence = random.choice(sentences)

    words = sentence.split()
    shuffled_words = words[:]
    random.shuffle(shuffled_words)
    selected_words = []
    used_indices.clear()
    question_label.config(text="MAKE THE CORRECT SENTENCES!")
    
    restore_buttons()
    update_result()
    update_timer()

   
   
mode_var = tk.StringVar(value="sequential")

mode_frame = tk.Frame(root, bg="lightgreen")
mode_frame.pack(side="top", fill="y", pady=0)

# グリッドの列幅を均等にする
mode_frame.columnconfigure(0, weight=1)
mode_frame.columnconfigure(1, weight=1)
mode_frame.columnconfigure(2, weight=1)

# モードラベル
mode_label = tk.Label(
    mode_frame,
    text="QUESTION STYLE:",
    font=("Helvetica", 15),
    bg="lightgreen"
)
mode_label.grid(row=0, column=0, padx=0, pady=0, sticky="e")

# SAMEボタン
sequential_radio = tk.Radiobutton(
    mode_frame,
    text="SAME",
    variable=mode_var,
    value="sequential",
    font=("Helvetica", 15),
    bg="lightgreen",
    selectcolor="white",
    indicatoron=1
)
sequential_radio.grid(row=0, column=1, padx=0, pady=0, ipady=0, ipadx=0, sticky="")

# RANDOMボタン
random_radio = tk.Radiobutton(
    mode_frame,
    text="RANDOM",
    variable=mode_var,
    value="random",
    font=("Helvetica", 15),
    bg="lightgreen",
    selectcolor="white",
    indicatoron=1
)
random_radio.grid(row=0, column=2, padx=0, pady=0, ipady=0, ipadx=0, sticky="")

   
   


 
    

# タイマーラベルを画面の一番下に配置

question_label = tk.Label(top_frame, text="", font=("Helvetica", 20), bg="lightgreen",
    bd=0, highlightthickness=0)
question_label.pack(pady=0)

correct_sentence_label = tk.Label(root, text="", font=("Helvetica", 20), fg="green", bg="lightgreen",
    bd=0, highlightthickness=0)
correct_sentence_label.pack(pady=0)

message_label = tk.Label(root, text="", font=("Helvetica", 20), fg="red", bg="lightgreen",
    bd=0, highlightthickness=0)
message_label.pack(pady=0)

correct_count = 0
question_count = 0

avg_time_label = tk.Label(
    root,
    text=f"CORRECT: {correct_count}/{question_count} | AVG: 0.0 sec",
    font=("Helvetica", 20),
    fg="blue",
    bg="lightgreen",
    bd=0,
    highlightthickness=0
)
avg_time_label.pack(pady=0)


result_label = tk.Label(top_frame, text="YOUR ANSWER WILL APPEAR HERE", font=("Helvetica", 20), bg="lightgreen",
    bd=0, highlightthickness=0)
result_label.pack(pady=0)

accuracy_label = tk.Label(root, text="", font=("Helvetica", 20), fg="blue", bg="lightgreen",
    bd=0, highlightthickness=0)
accuracy_label.pack(pady=0)

total_time_limit = 15 * 60  # 15分
timer_label = tk.Label(root,
                       text=f"TIME: {total_time_limit//60:02d}:00",
                       font=("Helvetica", 20),
                       fg="blue",
                       bg="lightgreen",
    bd=0, highlightthickness=0)
timer_label.pack(pady=0)

music_label = tk.Label(root, text="Music：MaouDamashii", font=("Helvetica", 20), fg="black", bg="lightgreen",
    bd=0, highlightthickness=0)
music_label.pack(pady=0)



# Start game
# 最後に実行
start_app()
create_buttons()
start_new_game()
root.mainloop()


def on_close():
    stop_bgm()
    pygame.mixer.quit()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)