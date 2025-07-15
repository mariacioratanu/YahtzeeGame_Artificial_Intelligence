import random
from ai_strategies import MCTSAISimpler, RandomAIStrategy, HeuristicAIStrategy, MCTSAIBest

class YahtzeeGameState:
    def __init__(self, strategy_class=MCTSAISimpler):
        self.dice_player = [0, 0, 0, 0, 0]
        self.dice_ai = [0, 0, 0, 0, 0]
        self.rolls_left = 3

        self.player_scorecard = {
            "ones": None,
            "twos": None,
            "threes": None,
            "fours": None,
            "fives": None,
            "sixes": None,
            "three_of_a_kind": None,
            "four_of_a_kind": None,
            "full_house": None,
            "small_straight": None,
            "large_straight": None,
            "yahtzee": None,
            "chance": None
        }

        self.ai_scorecard = {
            "ones": None,
            "twos": None,
            "threes": None,
            "fours": None,
            "fives": None,
            "sixes": None,
            "three_of_a_kind": None,
            "four_of_a_kind": None,
            "full_house": None,
            "small_straight": None,
            "large_straight": None,
            "yahtzee": None,
            "chance": None
        }

        self.current_player = "human"
        # facem o instanta a strategiei alese
        self.ai_strategy = strategy_class()

    def get_available_categories(self, player_type):
        scorecard = self.player_scorecard if player_type == "human" else self.ai_scorecard
        return [category for category in scorecard if scorecard[category] is None]

    def initialize_game(self):
        self.dice_player = [0, 0, 0, 0, 0]
        self.dice_ai = [0, 0, 0, 0, 0]
        self.rolls_left = 3

        for category in self.player_scorecard:
            self.player_scorecard[category] = None
        for category in self.ai_scorecard:
            self.ai_scorecard[category] = None

        self.current_player = "human"
        print("Jocul a fost initializat.")

    def is_final_state(self):
        all_player_categories_completed = all(score is not None for score in self.player_scorecard.values())
        all_ai_categories_completed = all(score is not None for score in self.ai_scorecard.values())
        return (all_player_categories_completed and all_ai_categories_completed)

    def roll_dice(self, dice_to_keep=None, player_type="human"):
        if dice_to_keep is None:
            dice_to_keep = []
        dice = self.dice_player if player_type == "human" else self.dice_ai

        if self.rolls_left > 0:
            for i in range(5):
                if i not in dice_to_keep:
                    dice[i] = random.randint(1, 6)
        else:
            print("Nu mai ai aruncari disponibile.")

    def reset_rolls(self):
        self.rolls_left = 3

    def calculate_total_score_player(self):
        return sum(score for score in self.player_scorecard.values() if score is not None)

    def calculate_total_score_ai(self):
        return sum(score for score in self.ai_scorecard.values() if score is not None)

    def calculate_player_score(self, category):
        return self._calculate_score(self.dice_player, category)

    def calculate_ai_score(self, category):
        return self._calculate_score(self.dice_ai, category)

    def _calculate_score(self, dice_list, category):
        from collections import Counter
        dice_counts = Counter(dice_list)

        if category == "ones":
            return sum(d for d in dice_list if d == 1)
        elif category == "twos":
            return sum(d for d in dice_list if d == 2)
        elif category == "threes":
            return sum(d for d in dice_list if d == 3)
        elif category == "fours":
            return sum(d for d in dice_list if d == 4)
        elif category == "fives":
            return sum(d for d in dice_list if d == 5)
        elif category == "sixes":
            return sum(d for d in dice_list if d == 6)
        elif category == "three_of_a_kind":
            if any(cnt >= 3 for cnt in dice_counts.values()):
                return sum(dice_list)
            return 0
        elif category == "four_of_a_kind":
            if any(cnt >= 4 for cnt in dice_counts.values()):
                return sum(dice_list)
            return 0
        elif category == "full_house":
            if sorted(dice_counts.values()) == [2,3]:
                return 25
            return 0
        elif category == "small_straight":
            unique_dice = sorted(set(dice_list))
            if (1 in unique_dice and 2 in unique_dice and 3 in unique_dice and 4 in unique_dice) or \
               (2 in unique_dice and 3 in unique_dice and 4 in unique_dice and 5 in unique_dice) or \
               (3 in unique_dice and 4 in unique_dice and 5 in unique_dice and 6 in unique_dice):
                return 30
            return 0
        elif category == "large_straight":
            unique_dice = sorted(set(dice_list))
            if unique_dice == [1,2,3,4,5] or unique_dice == [2,3,4,5,6]:
                return 40
            return 0
        elif category == "yahtzee":
            if any(cnt == 5 for cnt in dice_counts.values()):
                return 50
            return 0
        elif category == "chance":
            return sum(dice_list)
        return 0

    def update_score(self, category, score, player_type):
        scorecard = self.player_scorecard if player_type == "human" else self.ai_scorecard
        if scorecard[category] is None:
            scorecard[category] = score
        else:
            print(f"Categoria {category} deja completata de {player_type}.")

    def play_mcts_turn(self):
        ai_messages = []
        self.reset_rolls()
        ai_messages.append("AI incepe tura.")

        # prima aruncare
        self.roll_dice(dice_to_keep=[], player_type="ai")
        ai_messages.append(f" - Aruncare initiala: {self.dice_ai}")
        self.rolls_left -= 1

        while self.rolls_left > 0:
            dice_to_keep = self.ai_strategy.choose_dice_to_keep(self.dice_ai, self.rolls_left, self.ai_scorecard)
            ai_messages.append(f" - Alege sa pastreze indicele: {dice_to_keep}")
            self.roll_dice(dice_to_keep, player_type="ai")
            ai_messages.append(f" - Rezultat aruncare: {self.dice_ai}")
            self.rolls_left -= 1

        # alege categoria
        chosen_cat = self.ai_strategy.choose_category(self.dice_ai, self.ai_scorecard)
        if chosen_cat is not None:
            ai_messages.append(f" - Alege categoria: {chosen_cat}")
            sc = self.calculate_ai_score(chosen_cat)
            self.update_score(chosen_cat, sc, "ai")
            ai_messages.append(f" - Scor obtinut: {sc}")
        else:
            ai_messages.append(" - Nu mai are categorii disponibile, nimic de facut.")

        return "\n".join(ai_messages)


def simulate_game():
    game = YahtzeeGameState(strategy_class=MCTSAIBest)
    game.initialize_game()
    while not game.is_final_state():
        ai_report = game.play_mcts_turn()
        print(ai_report)
        if game.is_final_state():
            break

    print("Final de joc!")
    print(f"Scor final jucator: {game.calculate_total_score_player()}, AI: {game.calculate_total_score_ai()}")

if __name__ == "__main__":
    simulate_game()
