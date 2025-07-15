import random
import math
import copy
from collections import Counter

# =============== 1) STRATEGIA RANDOM ==================
class RandomAIStrategy:

    def choose_dice_to_keep(self, dice, rolls_left, ai_scorecard):
        indices = [0,1,2,3,4]
        how_many_to_keep = random.randint(0, 5)
        chosen = random.sample(indices, how_many_to_keep)
        return chosen

    def choose_category(self, dice, ai_scorecard):
        avail_cats = [c for c,v in ai_scorecard.items() if v is None]
        if not avail_cats:
            return None
        return random.choice(avail_cats)


# =============== 2) STRATEGIA HEURISTICa SIMPLa ==================
class HeuristicAIStrategy:
    def choose_dice_to_keep(self, dice, rolls_left, ai_scorecard):
        c = Counter(dice)
        # cauta 4+ of a kind
        for val, cnt in c.items():
            if cnt >= 4:
                return [i for i, d in enumerate(dice) if d == val]

        # cauta 3+ of a kind
        for val, cnt in c.items():
            if cnt >= 3:
                return [i for i, d in enumerate(dice) if d == val]

        # cauta small straight
        sorted_dice = sorted(set(dice))
        small_straights = [[1,2,3,4], [2,3,4,5], [3,4,5,6]]
        for sst in small_straights:
            if all(x in sorted_dice for x in sst):
                return [i for i, d in enumerate(dice) if d in sst]

        # daca nu e nimic special, pastram un pair (daca exista)
        for val, cnt in c.items():
            if cnt == 2:
                return [i for i, d in enumerate(dice) if d == val]

        return []

    def choose_category(self, dice, ai_scorecard):
        avail_cats = [c for c,v in ai_scorecard.items() if v is None]
        if not avail_cats:
            return None

        best_cat = None
        best_score = -1
        for cat in avail_cats:
            sc = self._calculate_score(dice, cat)
            if sc > best_score:
                best_score = sc
                best_cat = cat
        return best_cat

    def _calculate_score(self, dice, category):
        c = Counter(dice)
        if not category:
            return 0

        if category == "ones":
            return sum(d for d in dice if d == 1)
        elif category == "twos":
            return sum(d for d in dice if d == 2)
        elif category == "threes":
            return sum(d for d in dice if d == 3)
        elif category == "fours":
            return sum(d for d in dice if d == 4)
        elif category == "fives":
            return sum(d for d in dice if d == 5)
        elif category == "sixes":
            return sum(d for d in dice if d == 6)
        elif category == "three_of_a_kind":
            if any(cnt >= 3 for cnt in c.values()):
                return sum(dice)
            return 0
        elif category == "four_of_a_kind":
            if any(cnt >= 4 for cnt in c.values()):
                return sum(dice)
            return 0
        elif category == "full_house":
            if sorted(c.values()) == [2,3]:
                return 25
            return 0
        elif category == "small_straight":
            s = sorted(set(dice))
            if ([1,2,3,4] == s[:4] or [2,3,4,5] == s[1:5] or [3,4,5,6] == s[2:6]):
                return 30
            return 0
        elif category == "large_straight":
            s = sorted(set(dice))
            if s == [1,2,3,4,5] or s == [2,3,4,5,6]:
                return 40
            return 0
        elif category == "yahtzee":
            if any(cnt == 5 for cnt in c.values()):
                return 50
            return 0
        elif category == "chance":
            return sum(dice)
        return 0


# =============== 3) STRATEGIA MCTS SIMPLA ==================
class MCTSAISimpler:
    def __init__(self, num_simulations=300, max_depth=1):
        self.num_simulations = num_simulations
        self.max_depth = max_depth

    def choose_dice_to_keep(self, dice, rolls_left, ai_scorecard):
        import math
        from itertools import combinations

        if rolls_left <= 0:
            return []

        indices = [0,1,2,3,4]
        all_subsets = []
        for r in range(6):
            for combo in combinations(indices, r):
                all_subsets.append(list(combo))

        best_subset = []
        best_value = -math.inf
        sims_per_subset = max(1, self.num_simulations // len(all_subsets))

        for subset in all_subsets:
            total_score = 0
            for _ in range(sims_per_subset):
                total_score += self._simulate_subset(dice, subset, rolls_left, ai_scorecard)
            avg_val = total_score / sims_per_subset
            if avg_val > best_value:
                best_value = avg_val
                best_subset = subset

        return list(best_subset)

    def _simulate_subset(self, dice, subset, rolls_left, ai_scorecard):
        import random
        import copy

        dice_copy = dice[:]
        for i in range(5):
            if i not in subset:
                dice_copy[i] = random.randint(1,6)

        next_rolls = rolls_left - 1
        if next_rolls <= 0:
            cat = self._choose_category_mcts(dice_copy, ai_scorecard, self.max_depth)
            sc = self._calculate_score(dice_copy, cat)
            new_sc = copy.deepcopy(ai_scorecard)
            new_sc[cat] = sc
            return sc + self._rollout_future_rounds(new_sc, depth=self.max_depth)
        else:
            final_dice = self._random_rollout_dice(dice_copy, next_rolls)
            cat = self._choose_category_mcts(final_dice, ai_scorecard, self.max_depth)
            sc = self._calculate_score(final_dice, cat)
            new_sc = copy.deepcopy(ai_scorecard)
            new_sc[cat] = sc
            return sc + self._rollout_future_rounds(new_sc, depth=self.max_depth)

    def _random_rollout_dice(self, dice, rolls_left):
        import random
        sim_d = dice[:]
        while rolls_left > 0:
            for i in range(5):
                if random.random() < 0.5:
                    sim_d[i] = random.randint(1,6)
            rolls_left -= 1
        return sim_d

    def _rollout_future_rounds(self, ai_scorecard, depth):
        import random
        import copy
        if depth <= 0:
            return 0

        available_cats = [c for c,v in ai_scorecard.items() if v is None]
        if not available_cats:
            return 0

        total_score = 0
        r = 0
        while r < depth and len(available_cats) > 0:
            d = [random.randint(1,6) for _ in range(5)]
            best_cat, best_sc = self._best_cat_for_dice(d, available_cats)
            total_score += best_sc
            ai_scorecard[best_cat] = best_sc
            available_cats.remove(best_cat)
            r += 1

        return total_score

    def _choose_category_mcts(self, dice, ai_scorecard, depth):
        import math
        import random
        import copy
        avail_cats = [c for c,v in ai_scorecard.items() if v is None]
        if not avail_cats:
            return None

        best_cat = None
        best_val = -math.inf
        sims_per_cat = max(1, self.num_simulations // len(avail_cats))

        for cat in avail_cats:
            total_v = 0
            for _ in range(sims_per_cat):
                sc = self._calculate_score(dice, cat)
                new_sc = copy.deepcopy(ai_scorecard)
                new_sc[cat] = sc
                future_v = self._rollout_future_rounds(new_sc, depth-1)
                total_v += (sc + future_v)
            avg_v = total_v / sims_per_cat
            if avg_v > best_val:
                best_val = avg_v
                best_cat = cat

        return best_cat

    def choose_category(self, dice, ai_scorecard):
        return self._choose_category_mcts(dice, ai_scorecard, self.max_depth)

    def _calculate_score(self, dice, category):
        c = Counter(dice)
        if not category:
            return 0

        if category == "ones":
            return sum(d for d in dice if d == 1)
        elif category == "twos":
            return sum(d for d in dice if d == 2)
        elif category == "threes":
            return sum(d for d in dice if d == 3)
        elif category == "fours":
            return sum(d for d in dice if d == 4)
        elif category == "fives":
            return sum(d for d in dice if d == 5)
        elif category == "sixes":
            return sum(d for d in dice if d == 6)
        elif category == "three_of_a_kind":
            if any(cnt >= 3 for cnt in c.values()):
                return sum(dice)
            return 0
        elif category == "four_of_a_kind":
            if any(cnt >= 4 for cnt in c.values()):
                return sum(dice)
            return 0
        elif category == "full_house":
            if sorted(c.values()) == [2,3]:
                return 25
            return 0
        elif category == "small_straight":
            s = sorted(set(dice))
            if ([1,2,3,4] == s[:4] or [2,3,4,5] == s[1:5] or [3,4,5,6] == s[2:6]):
                return 30
            return 0
        elif category == "large_straight":
            s = sorted(set(dice))
            if s == [1,2,3,4,5] or s == [2,3,4,5,6]:
                return 40
            return 0
        elif category == "yahtzee":
            if any(cnt == 5 for cnt in c.values()):
                return 50
            return 0
        elif category == "chance":
            return sum(dice)
        return 0

    def _best_cat_for_dice(self, dice, cat_list):
        best_cat = None
        best_score = -1
        for c in cat_list:
            sc = self._calculate_score(dice, c)
            if sc > best_score:
                best_score = sc
                best_cat = c
        return best_cat, best_score


# =============== 4) STRATEGIA MCTS BEST ==================
class MCTSAIBest(MCTSAISimpler):
    def __init__(self):
        super().__init__(num_simulations=1000, max_depth=2)


# =============== 5) STRATEGIA MINIMAX ==================
class MinimaxAIStrategy:

    def __init__(self, max_depth=2):
        self.max_depth = max_depth

    def choose_dice_to_keep(self, dice, rolls_left, ai_scorecard):
        if rolls_left <= 0:
            return []

        best_subset, best_val = self._minimax_dice(dice, rolls_left, ai_scorecard, depth=self.max_depth, maximizing_player=True)
        return best_subset

    def choose_category(self, dice, ai_scorecard):
        best_cat, best_val = self._minimax_category(dice, ai_scorecard, depth=self.max_depth, maximizing_player=True)
        return best_cat

    def _minimax_dice(self, dice, rolls_left, ai_scorecard, depth, maximizing_player):
        from itertools import combinations
        if depth <= 0 or rolls_left <= 0:
            cat, val = self._best_cat_for_dice(dice, ai_scorecard)
            return ([], val)

        indices = [0,1,2,3,4]
        all_subsets = []
        for r in range(6):
            for combo in combinations(indices, r):
                all_subsets.append(list(combo))

        best_subset = None
        if maximizing_player:
            best_value = -math.inf
        else:
            best_value = math.inf

        for subset in all_subsets:
            new_dice = dice[:]
            for i in range(5):
                if i not in subset:
                    new_dice[i] = random.randint(1,6)
            _, val = self._minimax_dice(new_dice, rolls_left - 1, ai_scorecard, depth-1, not maximizing_player)

            if maximizing_player:
                if val > best_value:
                    best_value = val
                    best_subset = subset
            else:
                if val < best_value:
                    best_value = val
                    best_subset = subset

        return (list(best_subset), best_value)

    def _minimax_category(self, dice, ai_scorecard, depth, maximizing_player):
        avail_cats = [c for c,v in ai_scorecard.items() if v is None]
        if not avail_cats or depth <= 0:
            cat, val = self._best_cat_for_dice(dice, ai_scorecard)
            return (cat, val)

        best_cat = None
        if maximizing_player:
            best_value = -math.inf
        else:
            best_value = math.inf

        for cat in avail_cats:
            sc = self._calculate_score(dice, cat)
            new_sc = copy.deepcopy(ai_scorecard)
            new_sc[cat] = sc
            opp_dice = [random.randint(1,6) for _ in range(5)]
            _, opp_val = self._minimax_category(opp_dice, new_sc, depth-1, not maximizing_player)
            if maximizing_player:
                total_val = sc - opp_val
                if total_val > best_value:
                    best_value = total_val
                    best_cat = cat
            else:
                total_val = sc - opp_val
                if total_val < best_value:
                    best_value = total_val
                    best_cat = cat

        return (best_cat, best_value)

    def _best_cat_for_dice(self, dice, scorecard):
        avail_cats = [c for c,v in scorecard.items() if v is None]
        if not avail_cats:
            return (None, 0)

        best_cat = None
        best_score = -1
        for cat in avail_cats:
            sc = self._calculate_score(dice, cat)
            if sc > best_score:
                best_score = sc
                best_cat = cat
        return (best_cat, best_score)

    def _calculate_score(self, dice, category):
        c = Counter(dice)
        if not category:
            return 0

        if category == "ones":
            return sum(d for d in dice if d == 1)
        elif category == "twos":
            return sum(d for d in dice if d == 2)
        elif category == "threes":
            return sum(d for d in dice if d == 3)
        elif category == "fours":
            return sum(d for d in dice if d == 4)
        elif category == "fives":
            return sum(d for d in dice if d == 5)
        elif category == "sixes":
            return sum(d for d in dice if d == 6)
        elif category == "three_of_a_kind":
            if any(cnt >= 3 for cnt in c.values()):
                return sum(dice)
            return 0
        elif category == "four_of_a_kind":
            if any(cnt >= 4 for cnt in c.values()):
                return sum(dice)
            return 0
        elif category == "full_house":
            if sorted(c.values()) == [2,3]:
                return 25
            return 0
        elif category == "small_straight":
            s = sorted(set(dice))
            if ([1,2,3,4] == s[:4] or [2,3,4,5] == s[1:5] or [3,4,5,6] == s[2:6]):
                return 30
            return 0
        elif category == "large_straight":
            s = sorted(set(dice))
            if s == [1,2,3,4,5] or s == [2,3,4,5,6]:
                return 40
            return 0
        elif category == "yahtzee":
            if any(cnt == 5 for cnt in c.values()):
                return 50
            return 0
        elif category == "chance":
            return sum(dice)
        return 0
