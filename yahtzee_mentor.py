import random
import openai

openai.api_key = "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"

class YahtzeeMentor:

    def _init_(self):
        pass

    def get_dice_advice(self, dice, rolls_left):
        from collections import Counter
        dice_counts = Counter(dice)

        # 1) 3+ de un fel => pastram
        for val, cnt in dice_counts.items():
            if cnt >= 3:
                keep_indices = [i for i, d in enumerate(dice) if d == val]
                return keep_indices, (
                    f"Avem {cnt} de {val}, e bine sa le pastram pentru a incerca un 4-of-a-kind sau full house."
                )

        # 2) potential straight (small/large)
        sorted_dice = sorted(set(dice))
        small_straights = [[1,2,3,4], [2,3,4,5], [3,4,5,6]]
        for sst in small_straights:
            if all(x in sorted_dice for x in sst):
                keep_indices = []
                for i, d in enumerate(dice):
                    if d in sst:
                        keep_indices.append(i)
                return (keep_indices,
                        "Pare ca avem potential de small straight, pastram zarurile din secventa respectiva.")

        # 3) altfel, daca avem un pair, pastram
        for val, cnt in dice_counts.items():
            if cnt == 2:
                keep_indices = [i for i, d in enumerate(dice) if d == val]
                return (keep_indices,
                        f"Avem un pair de {val}, poate incercam sa-l transformam intr-un 3-of-a-kind sau mai mult.")

        # 4) nimic semnificativ => aruncam tot
        return ([], "Nu avem nimic special, poate e mai bine sa aruncam tot pentru sanse noi.")

    def get_category_advice(self, dice, available_categories):
        from collections import Counter
        dice_counts = Counter(dice)

        # verificam daca e Yahtzee
        if any(c == 5 for c in dice_counts.values()):
            if "yahtzee" in available_categories:
                return "yahtzee", "Ai un Yahtzee! 50 de puncte, e maximul."

        # large straight
        sorted_dice = sorted(set(dice))
        if len(sorted_dice) == 5:
            if sorted_dice in ([1,2,3,4,5], [2,3,4,5,6]) and "large_straight" in available_categories:
                return "large_straight", "Ai un Large Straight - 40 de puncte!"

        # small straight
        small_straights = [[1,2,3,4], [2,3,4,5], [3,4,5,6]]
        for sst in small_straights:
            if all(x in sorted_dice for x in sst):
                if "small_straight" in available_categories:
                    return "small_straight", "Ai un Small Straight - 30 de puncte!"

        # full house (3+2)
        if sorted(dice_counts.values()) == [2, 3] and "full_house" in available_categories:
            return "full_house", "Ai Full House - 25 de puncte!"

        # four of a kind
        if any(c >= 4 for c in dice_counts.values()):
            if "four_of_a_kind" in available_categories:
                return "four_of_a_kind", "Ai 4 of a Kind, se puncteaza cu suma zarurilor."

        # three of a kind
        if any(c >= 3 for c in dice_counts.values()):
            if "three_of_a_kind" in available_categories:
                return "three_of_a_kind", "Ai 3 of a Kind, se puncteaza cu suma zarurilor."

        # verificam categoriile simple (1-6)
        most_common_val, most_common_count = dice_counts.most_common(1)[0]
        category_map = {1: "ones", 2: "twos", 3: "threes", 4: "fours", 5: "fives", 6: "sixes"}
        if category_map.get(most_common_val) in available_categories:
            return (category_map[most_common_val],
                    f"Poti inscrie la {category_map[most_common_val]} (ai {most_common_count} zaruri de {most_common_val}).")

        # chance
        if "chance" in available_categories:
            return "chance", "Nu se potriveste nimic special, dar poti merge pe Chance (suma zarurilor)."

        return None, "Nu mai e nimic disponibil, alege o categorie libera."

# ===================== Partea cu Q&A local =====================

EXTENDED_RULES_QA = {
    "cum se joaca yahtzee?": (
        "Obiectivul jocului este sa obtii cele mai multe puncte, alegand 13 categorii. "
        "De fiecare data poti arunca zarurile de pana la 3 ori, pastrand ce vrei. "
        "Dupa a treia aruncare, trebuie sa alegi o categorie in care sa inscrii scorul."
    ),
    "ce e upper section?": (
        "Upper Section contine categoriile de la ones la sixes. "
        "in aceste categorii insumezi zarurile care au valoarea respectiva. "
        "Daca insumezi cel putin 63 de puncte total la Upper Section, primesti un bonus de 35 de puncte."
    ),
    "ce e lower section?": (
        "Lower Section contine categoriile: three_of_a_kind, four_of_a_kind, full_house, small_straight, "
        "large_straight, yahtzee si chance. Acestea se puncteaza diferit, dupa combinatii specifice."
    ),
    "ce strategie recomandata?": (
        "Strategia PROVEN: \n"
        "- Prioritize the Upper Section Bonus (incearca sa obtii 63 de puncte in categoriile 1-6). \n"
        "- Remain Adaptive (fii flexibil la ce-ti cade). \n"
        "- Organize (nu rata categoriile deja completate, fii atent la ce-ti lipseste). \n"
        "- Value the Yahtzee (nu-l taia prea devreme). \n"
        "- Embrace Eventualities (foloseste chance/ones ca fallback). \n"
        "- Never Back Down (nu renunta, o aruncare norocoasa poate schimba tot)."
    ),
    "ce inseamna full house?": (
        "Un full house este 3 zaruri de o valoare + 2 zaruri de alta valoare, ex: (3,3,3,5,5)."
    ),
    "cum se calculeaza small straight?": (
        "Small straight e o secventa de 4 numere consecutive (1-2-3-4, 2-3-4-5 sau 3-4-5-6) "
        "si valoreaza 30 de puncte."
    ),
    "cum se calculeaza large straight?": (
        "Large straight e o secventa de 5 numere consecutive (1-2-3-4-5 sau 2-3-4-5-6) si valoreaza 40 de puncte."
    ),
    "ce este yahtzee?": (
        "Yahtzee inseamna 5 zaruri de aceeasi valoare, valoreaza 50 de puncte. "
        "Daca faci din nou Yahtzee, primesti 100 de puncte bonus (daca n-ai taiat categoria)."
    ),
    "cum se acorda punctele la categoriile 1-6?": (
        "Pur si simplu se aduna zarurile care au acea valoare. Ex: daca ai 3 de '4', primesti 12 puncte la 'fours'."
    ),
    "cum pot primi sfaturi practice?": (
        "Poti sa ceri un hint despre zaruri sau despre ce categorie sa alegi. "
        "Programul iti va recomanda ce sa pastrezi si ce categorie e mai avantajoasa momentan."
    ),
    "care sunt regulile bonus la yahtzee?": (
        "Daca dai un al doilea Yahtzee si ai deja 50 la rubrica Yahtzee, primesti un bonus de 100 de puncte. "
        "Trebuie apoi sa folosesti combinatia drept joker in alta categorie libera."
    ),
    "cand se termina jocul?": (
        "Jocul se termina dupa ce fiecare jucator a completat toate cele 13 categorii."
    ),
}

def answer_question_local(question_text):
    q = question_text.strip().lower()
    for key in EXTENDED_RULES_QA:
        if key in q:
            return EXTENDED_RULES_QA[key]

    return (
        "Nu am un raspuns specific pentru intrebarea ta. "
        "Poti incerca alta formulare sau sa citesti regulile detaliate."
    )

# ===================== Partea cu GPT =====================
def answer_question_gpt(question_text):
    if not question_text.strip():
        return "Nu am primit nicio intrebare."

    try:
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant specialized in Yahtzee."},
            {"role": "user", "content": question_text}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.5,
            max_tokens=500
        )
        answer = response["choices"][0]["message"]["content"]
        return answer.strip()
    except Exception as e:
        return f"Eroare la apelul GPT: {e}"