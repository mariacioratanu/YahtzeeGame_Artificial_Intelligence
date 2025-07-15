import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk

from main import YahtzeeGameState
from yahtzee_mentor import YahtzeeMentor, answer_question_local, answer_question_gpt
from performance_tracker import record_result, get_performance_summary

from ai_strategies import (
    MCTSAISimpler,
    MCTSAIBest,
    RandomAIStrategy,
    HeuristicAIStrategy
)

PASTEL_GREEN = "#c3e6cb"
PASTEL_BLUE = "#d2e1f0"
PASTEL_YELLOW = "#fff8b5"
PASTEL_WHITE = "#f8f8ff"

IMAGES_PATH = "images"

RULES_TEXT = (
    "1. Fiecare jucator are 13 categorii de completat.\n"
    "2. in fiecare tura, poti arunca zarurile de pana la 3 ori.\n"
    "3. Poti alege ce zaruri sa pastrezi si pe care sa le arunci din nou.\n"
    "4. Dupa ultima aruncare, alegi categoria unde inscrii scorul.\n"
    "5. Jocul se termina dupa completarea tuturor categoriilor.\n"
)

class YahtzeeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Yahtzee - Enhanced GUI with GPT Real-Time Advice (Images + Selection)")

        self.root.configure(bg=PASTEL_BLUE)

        # ========== STRATEGIA AI ==========
        strategy_name = simpledialog.askstring(
            "Alege Strategia AI",
            "Introdu una dintre: 'random', 'heuristic', 'mcts_simpler', 'mcts_best', 'minimax'\n"
            "(Default: 'mcts_simpler')"
        )
        if not strategy_name:
            strategy_name = 'mcts_simpler'
        if strategy_name and strategy_name.lower() == 'random':
            chosen_strategy = RandomAIStrategy
        elif strategy_name and strategy_name.lower() == 'heuristic':
            chosen_strategy = HeuristicAIStrategy
        elif strategy_name and strategy_name.lower() == 'mcts_best':
            chosen_strategy = MCTSAIBest
        elif strategy_name and strategy_name.lower() == 'minimax':
            from ai_strategies import MinimaxAIStrategy
            chosen_strategy = MinimaxAIStrategy
        else:
            chosen_strategy = MCTSAISimpler

        self.game = YahtzeeGameState(strategy_class=chosen_strategy)
        self.game.initialize_game()

        self.mentor = YahtzeeMentor()

        # ========== incarcam imaginile de zaruri ==========
        self.dice_images = []
        for i in range(1, 7):
            path = f"{IMAGES_PATH}/dice_{i}.png"
            pil_img = Image.open(path)
            pil_img = pil_img.resize((64, 64), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(pil_img)
            self.dice_images.append(tk_img)

        self.selected_dice = []
        self.player_moves = []

        self.create_main_frames()
        self.update_scorecard_player()
        self.update_scorecard_ai()

    def _best_cat_for_current_dice(self, dice, available_cats):
        best_cat = None
        best_score = -1
        for cat in available_cats:
            sc = self.game._calculate_score(dice, cat)
            if sc > best_score:
                best_score = sc
                best_cat = cat
        return best_cat, best_score

    def generate_performance_feedback(self):
        if not self.player_moves:
            return "Nu exista date despre deciziile jucatorului."

        total_rounds = len(self.player_moves)
        same_as_best = 0
        total_diff = 0
        largest_diff = 0
        largest_diff_round = 0

        for i, mv in enumerate(self.player_moves, start=1):
            diff = mv["score_best"] - mv["score_chosen"]
            total_diff += diff
            if diff == 0:
                same_as_best += 1
            if diff > largest_diff:
                largest_diff = diff
                largest_diff_round = i

        feedback_lines = []
        feedback_lines.append(f"in total au fost {total_rounds} runde in care ai inscris.\n")
        feedback_lines.append(f"- in {same_as_best} dintre acestea, ai ales exact cea mai buna categorie posibila.\n")

        if total_rounds - same_as_best > 0:
            feedback_lines.append(f"- in celelalte {total_rounds - same_as_best} runde, ")
            feedback_lines.append(f"ai pierdut un total de {total_diff} puncte fata de ce puteai obtine.\n")
            if largest_diff_round > 0 and largest_diff > 0:
                feedback_lines.append(f"  Cea mai mare diferenta a fost la runda #{largest_diff_round}, ")
                feedback_lines.append(f"unde puteai obtine cu {largest_diff} puncte mai mult.\n")
        else:
            feedback_lines.append("Excelent! Ai ales mereu categoriile optime.\n")

        feedback_lines.append("\nContinua sa exersezi si vei obtine scoruri si mai mari!")
        return "".join(feedback_lines)

    def create_main_frames(self):
        # zarurile (sus)
        self.dice_frame = tk.Frame(self.root, bg=PASTEL_GREEN, bd=2, relief=tk.RIDGE)
        self.dice_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.dice_buttons = []
        for i in range(5):
            btn = tk.Button(
                self.dice_frame,
                image=self.dice_images[0],  # default: dice_1
                bg=PASTEL_WHITE,
                # pt a avea un chenar de selectie
                highlightthickness=0,
                highlightbackground=PASTEL_WHITE,
                relief=tk.RAISED,
                command=lambda idx=i: self.toggle_dice(idx)
            )
            btn.pack(side=tk.LEFT, padx=5)
            self.dice_buttons.append(btn)

        # scoreboard jucator
        self.player_score_frame = tk.Frame(self.root, bg=PASTEL_YELLOW, bd=2, relief=tk.SUNKEN)
        self.player_score_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        tk.Label(self.player_score_frame, text="Player Scoreboard", bg=PASTEL_YELLOW,
                 font=("Helvetica", 14, "bold")).pack(pady=5)
        self.upper_labels_p = {}
        self.bonus_label_p = None
        self.lower_labels_p = {}

        self.progress_label_p = None
        self.total_score_label_p = None

        self.build_scoreboard(self.player_score_frame, self.upper_labels_p, self.lower_labels_p, "player")

        # scoreboard AI
        self.ai_score_frame = tk.Frame(self.root, bg=PASTEL_YELLOW, bd=2, relief=tk.SUNKEN)
        self.ai_score_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        tk.Label(self.ai_score_frame, text="AI Scoreboard", bg=PASTEL_YELLOW,
                 font=("Helvetica", 14, "bold")).pack(pady=5)
        self.upper_labels_ai = {}
        self.bonus_label_ai = None
        self.lower_labels_ai = {}

        self.progress_label_ai = None
        self.total_score_label_ai = None

        self.build_scoreboard(self.ai_score_frame, self.upper_labels_ai, self.lower_labels_ai, "ai")

        self.center_frame = tk.Frame(self.root, bd=2, bg=PASTEL_BLUE)
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.create_buttons_panel()
        self.create_chat_panel()

    def build_scoreboard(self, parent_frame, upper_dict, lower_dict, user_type):
        upper_frame = tk.Frame(parent_frame, bg=PASTEL_WHITE)
        upper_frame.pack(pady=5, fill=tk.X)

        tk.Label(upper_frame, text=f"Upper Section ({user_type})",
                 bg=PASTEL_WHITE, font=("Helvetica", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")

        cat_upper = ["ones", "twos", "threes", "fours", "fives", "sixes"]
        for i, cat in enumerate(cat_upper, start=1):
            tk.Label(upper_frame, text=cat.capitalize(), bg=PASTEL_WHITE).grid(row=i, column=0, sticky="w")
            lbl_val = tk.Label(upper_frame, text="-", bg="white", width=5)
            lbl_val.grid(row=i, column=1)
            upper_dict[cat] = lbl_val

        tk.Label(upper_frame, text="Bonus(63+):", bg=PASTEL_WHITE).grid(row=len(cat_upper)+1, column=0, sticky="w")
        bonus_label = tk.Label(upper_frame, text="-", bg="white", width=5)
        bonus_label.grid(row=len(cat_upper)+1, column=1)
        if user_type == "player":
            self.bonus_label_p = bonus_label
        else:
            self.bonus_label_ai = bonus_label

        lower_frame = tk.Frame(parent_frame, bg=PASTEL_WHITE)
        lower_frame.pack(pady=5, fill=tk.X)

        tk.Label(lower_frame, text=f"Lower Section ({user_type})", bg=PASTEL_WHITE,
                 font=("Helvetica", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")

        cat_lower = ["three_of_a_kind", "four_of_a_kind", "full_house",
                     "small_straight", "large_straight", "yahtzee", "chance"]
        for i, cat in enumerate(cat_lower, start=1):
            tk.Label(lower_frame, text=cat.replace("_", " ").title(), bg=PASTEL_WHITE).grid(row=i, column=0, sticky="w")
            lbl_val = tk.Label(lower_frame, text="-", bg="white", width=5)
            lbl_val.grid(row=i, column=1)
            lower_dict[cat] = lbl_val

        row_idx = len(cat_lower) + 1
        tk.Label(lower_frame, text="Progress:", bg=PASTEL_WHITE).grid(row=row_idx, column=0, sticky="w")
        progress_lbl = tk.Label(lower_frame, text="0/13", bg="white", width=5)
        progress_lbl.grid(row=row_idx, column=1)
        row_idx += 1

        tk.Label(lower_frame, text="Total Score:", bg=PASTEL_WHITE).grid(row=row_idx, column=0, sticky="w")
        total_lbl = tk.Label(lower_frame, text="0", bg="white", width=5)
        total_lbl.grid(row=row_idx, column=1)

        if user_type == "player":
            self.progress_label_p = progress_lbl
            self.total_score_label_p = total_lbl
        else:
            self.progress_label_ai = progress_lbl
            self.total_score_label_ai = total_lbl

    def create_buttons_panel(self):
        btn_frame = tk.Frame(self.center_frame, bg=PASTEL_BLUE)
        btn_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        btn_style = dict(bg=PASTEL_GREEN, fg="black", font=("Helvetica", 10, "bold"), relief=tk.RAISED)

        self.roll_button = tk.Button(btn_frame, text="Roll Dice", command=self.roll_dice, **btn_style)
        self.roll_button.pack(side=tk.LEFT, padx=3)

        self.submit_score_btn = tk.Button(btn_frame, text="Submit Score", state=tk.DISABLED,
                                          command=self.submit_score, **btn_style)
        self.submit_score_btn.pack(side=tk.LEFT, padx=3)

        self.hint_dice_btn = tk.Button(btn_frame, text="Dice Hint", command=self.ask_for_dice_hint, **btn_style)
        self.hint_dice_btn.pack(side=tk.LEFT, padx=3)

        self.hint_category_btn = tk.Button(btn_frame, text="Category Hint", command=self.ask_for_category_hint, **btn_style)
        self.hint_category_btn.pack(side=tk.LEFT, padx=3)

        self.stats_btn = tk.Button(btn_frame, text="Show Stats", command=self.show_stats, **btn_style)
        self.stats_btn.pack(side=tk.LEFT, padx=3)

        self.show_rules_button = tk.Button(btn_frame, text="Show Rules", command=self.show_rules, **btn_style)
        self.show_rules_button.pack(side=tk.LEFT, padx=3)

        self.realtime_advice_button = tk.Button(btn_frame, text="Real-Time Advice", command=self.get_realtime_advice, **btn_style)
        self.realtime_advice_button.pack(side=tk.LEFT, padx=3)

    def create_chat_panel(self):
        chat_frame = tk.Frame(self.center_frame, bd=2, relief=tk.GROOVE, bg=PASTEL_BLUE)
        chat_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(chat_frame, text="Q&A / Chat", font=("Helvetica", 12, "bold"), bg=PASTEL_BLUE).pack()

        self.chat_display = tk.Text(chat_frame, height=10, state=tk.DISABLED, wrap=tk.WORD, bg=PASTEL_WHITE)
        self.chat_display.pack(pady=5, fill=tk.BOTH, expand=True)

        entry_frame = tk.Frame(chat_frame, bg=PASTEL_BLUE)
        entry_frame.pack(fill=tk.X)

        self.question_entry = tk.Entry(entry_frame, bg="white", fg="black")
        self.question_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_local = tk.Button(entry_frame, text="Ask Local", command=self.ask_question_local,
                              bg=PASTEL_GREEN, fg="black")
        btn_local.pack(side=tk.LEFT, padx=2)

        btn_gpt = tk.Button(entry_frame, text="Ask GPT", command=self.ask_question_gpt,
                            bg=PASTEL_GREEN, fg="black")
        btn_gpt.pack(side=tk.RIGHT, padx=2)

    def show_rules(self):
        messagebox.showinfo("Yahtzee Rules", RULES_TEXT)

    def show_stats(self):
        summary = get_performance_summary()
        messagebox.showinfo("Stats", summary)

    def get_realtime_advice(self):
        dice_player = self.game.dice_player
        rolls_left = self.game.rolls_left
        avail_cats = self.game.get_available_categories("human")
        total_score = self.game.calculate_total_score_player()

        prompt = (
            "You are a helpful AI assistant specialized in Yahtzee.\n"
            "I'm playing Yahtzee right now, and here is my current situation:\n"
            f"- Dice: {dice_player}\n"
            f"- Rolls left: {rolls_left}\n"
            f"- Available categories for me: {avail_cats}\n"
            f"- Current total score: {total_score}\n\n"
            "Please give me real-time advice on what dice I should keep (or re-roll) and "
            "which category might be best to target, based on standard Yahtzee rules. "
            "Explain your reasoning briefly."
        )

        advice = answer_question_gpt(prompt)
        messagebox.showinfo("Real-Time Advice", advice)

    def toggle_dice(self, index):
        if index in self.selected_dice:
            self.selected_dice.remove(index)
            self.dice_buttons[index].config(highlightthickness=0,
                                            highlightbackground=PASTEL_WHITE,
                                            relief=tk.RAISED)
        else:
            self.selected_dice.append(index)
            self.dice_buttons[index].config(highlightthickness=3,
                                            highlightbackground="#b3d9ff",
                                            relief=tk.SOLID)

    def roll_dice(self):
        if self.game.rolls_left > 0:
            self.game.roll_dice(self.selected_dice, player_type="human")
            for i in range(5):
                val = self.game.dice_player[i]
                self.dice_buttons[i].config(image=self.dice_images[val - 1])
            self.game.rolls_left -= 1
            if self.game.rolls_left == 0:
                self.submit_score_btn.config(state=tk.NORMAL)
            self.update_interface()
        else:
            messagebox.showinfo("Info", "Nu mai ai aruncari disponibile.")
            self.submit_score_btn.config(state=tk.NORMAL)

    def submit_score(self):
        avail_cats = self.game.get_available_categories("human")
        if not avail_cats:
            messagebox.showwarning("Atentie", "Nu mai exista categorii disponibile!")
            return

        cat = simpledialog.askstring("Alege categoria", f"Categorii disponibile: {', '.join(avail_cats)}")
        if cat and cat in avail_cats:
            sc = self.game.calculate_player_score(cat)

            best_cat, best_score = self._best_cat_for_current_dice(self.game.dice_player, avail_cats)
            diff = best_score - sc

            self.player_moves.append({
                "dice": self.game.dice_player[:],
                "cat_chosen": cat,
                "score_chosen": sc,
                "cat_best": best_cat,
                "score_best": best_score,
                "difference": diff
            })

            self.game.update_score(cat, sc, "human")
            self.update_scorecard_player()
            self.run_ai_turn()
        else:
            messagebox.showwarning("Invalid", "Categoria introdusa nu este valida sau deja ocupata.")

        self.reset_dice_for_new_round()

    def run_ai_turn(self):
        ai_report = self.game.play_mcts_turn()
        self.add_chat_message("AI TURN:\n" + ai_report)
        self.update_scorecard_ai()
        self.update_interface()

    def reset_dice_for_new_round(self):
        self.selected_dice = []
        for btn in self.dice_buttons:
            btn.config(image=self.dice_images[0],
                       highlightthickness=0,
                       highlightbackground=PASTEL_WHITE,
                       relief=tk.RAISED)
        self.game.reset_rolls()
        self.roll_button.config(state=tk.NORMAL)
        self.submit_score_btn.config(state=tk.DISABLED)

    def ask_for_dice_hint(self):
        advice_indices, reason = self.mentor.get_dice_advice(self.game.dice_player, self.game.rolls_left)
        if advice_indices:
            msg = f"Hint zaruri: tine index {advice_indices}, motiv: {reason}"
        else:
            msg = f"Hint zaruri: {reason}"
        messagebox.showinfo("Dice Hint", msg)

    def ask_for_category_hint(self):
        avail_cats = self.game.get_available_categories("human")
        cat, reason = self.mentor.get_category_advice(self.game.dice_player, avail_cats)
        if cat:
            msg = f"Hint categorie: {cat}, motiv: {reason}"
        else:
            msg = f"Nu sunt categorii disponibile: {reason}"
        messagebox.showinfo("Category Hint", msg)

    def ask_question_local(self):
        q = self.question_entry.get().strip()
        if not q:
            return
        self.question_entry.delete(0, tk.END)

        self.add_chat_message(f"TU (local): {q}")
        ans = answer_question_local(q)
        self.add_chat_message(f"SISTEM (local): {ans}")

    def ask_question_gpt(self):
        q = self.question_entry.get().strip()
        if not q:
            return
        self.question_entry.delete(0, tk.END)

        self.add_chat_message(f"TU (GPT): {q}")
        ans = answer_question_gpt(q)
        self.add_chat_message(f"GPT: {ans}")

    def add_chat_message(self, msg):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, msg + "\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def update_interface(self):
        if self.game.is_final_state():
            ps = self.game.calculate_total_score_player()
            ais = self.game.calculate_total_score_ai()
            if ps > ais:
                winner = "Felicitari! Ai castigat!"
            elif ais > ps:
                winner = "AI-ul a castigat!"
            else:
                winner = "Egalitate!"

            feedback_text = self.generate_performance_feedback()
            final_msg = (
                f"Scor final: Jucator={ps}, AI={ais}. {winner}\n\n"
                "=== FEEDBACK DESPRE JOCUL TaU ===\n"
                f"{feedback_text}"
            )
            messagebox.showinfo("Final & Feedback", final_msg)
            record_result(ps, ais, winner)

            self.roll_button.config(state=tk.DISABLED)
            self.submit_score_btn.config(state=tk.DISABLED)

    def update_scorecard_player(self):
        cat_upper = ["ones","twos","threes","fours","fives","sixes"]
        total_upper = 0
        for cat in cat_upper:
            val = self.game.player_scorecard[cat]
            self.upper_labels_p[cat].config(text=str(val) if val is not None else "-")
            if val is not None:
                total_upper += val
        bonus = 35 if total_upper >= 63 else 0
        self.bonus_label_p.config(text=bonus if bonus else "-")

        cat_lower = ["three_of_a_kind","four_of_a_kind","full_house","small_straight",
                     "large_straight","yahtzee","chance"]
        for cat in cat_lower:
            val = self.game.player_scorecard[cat]
            self.lower_labels_p[cat].config(text=str(val) if val is not None else "-")

        completed_cats = sum(1 for v in self.game.player_scorecard.values() if v is not None)
        self.progress_label_p.config(text=f"{completed_cats}/13")
        total_score = self.game.calculate_total_score_player()
        self.total_score_label_p.config(text=str(total_score))

    def update_scorecard_ai(self):
        cat_upper = ["ones","twos","threes","fours","fives","sixes"]
        total_upper = 0
        for cat in cat_upper:
            val = self.game.ai_scorecard[cat]
            self.upper_labels_ai[cat].config(text=str(val) if val is not None else "-")
            if val is not None:
                total_upper += val
        bonus = 35 if total_upper >= 63 else 0
        self.bonus_label_ai.config(text=bonus if bonus else "-")

        cat_lower = ["three_of_a_kind","four_of_a_kind","full_house","small_straight",
                     "large_straight","yahtzee","chance"]
        for cat in cat_lower:
            val = self.game.ai_scorecard[cat]
            self.lower_labels_ai[cat].config(text=str(val) if val is not None else "-")

        completed_cats = sum(1 for v in self.game.ai_scorecard.values() if v is not None)
        self.progress_label_ai.config(text=f"{completed_cats}/13")
        total_score = self.game.calculate_total_score_ai()
        self.total_score_label_ai.config(text=str(total_score))


if __name__ == "__main__":
    root = tk.Tk()
    app = YahtzeeGUI(root)
    root.mainloop()
