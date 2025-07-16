# 🎲 Yahtzee AI – Intelligent Dice Game with GUI, Strategies, and GPT Integration

Interactive Yahtzee game in Python that pairs a Tkinter GUI with multiple AI strategies (Random, Heuristic, MCTS, Minimax), real-time GPT coaching and built-in performance tracking.

## 👩‍💻 Team

- Ciorâțanu Maria
- Pâncă Aida-Gabriela
- Varzar Alina-Miruna  

## 🧠 Architecture

This project follows a *modular and extensible architecture*, including:

- *AI Strategy Layer* – Supports plug-and-play strategies (Random, Heuristic, MCTS, Minimax).
- *Game Engine* – Manages player turns, dice logic, scoring, and category selection.
- *GUI Layer (Tkinter)* – Interactive board with dice images, scorecards, hint buttons, and GPT integration.
- *Mentor System* – Offers both predefined advice and GPT-based responses to natural language questions.
- *Performance Tracker* – Stores and summarizes all game results for skill improvement analysis.



## 🧩 AI Strategies

Implemented strategies are fully encapsulated and interchangeable:

| Strategy         | Description |
|------------------|-------------|
| RandomAIStrategy | Chooses dice and categories randomly |
| HeuristicAIStrategy | Greedy rule-based logic |
| MCTSAISimpler | Monte Carlo Tree Search with rollout |
| MCTSAIBest | MCTS with higher simulations and deeper lookahead |
| MinimaxAIStrategy | Classic adversarial decision making using minimax |



## 🎮 Features

- Interactive GUI (Tkinter + PIL) with dice visuals and clickable interface
- Human vs. AI gameplay (turn-based)
- Local advice system (heuristics-based)
- GPT-4 powered advice with real-time prompts
- Natural language Q&A about Yahtzee rules and strategy
- Post-game performance report with actionable feedback
- Statistics tracking across all sessions (victories, averages, etc.)

## 🎮 Tech Stack

| Layer            | Tech                             |
| ---------------- | -------------------------------- |
| Language         | Python 3.10+                     |
| GUI              | Tkinter + Pillow                 |
| AI / Algorithms  | Random, Heuristic, MCTS, Minimax |
| Cloud            | OpenAI ChatCompletion API        |
| Data Persistence | JSON (for game stats)            |

### 🎮 Architecture

1. GUI asks the player which AI strategy to face, then spins up `YahtzeeGameState` with that strategy.
2. Player and AI alternate turns; the AI delegates its choices to the injected strategy class.
3. At any point the Mentor can be summoned for hints (local or GPT).
4. When the scorecard is filled, the tracker writes a row to **yahtzee\_stats.json** and the GUI shows feedback.

