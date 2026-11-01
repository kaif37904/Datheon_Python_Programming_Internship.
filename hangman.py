"""Hangman Word Guessing Game (Console)

Run with:  python hangman.py

Optional: put a file named 'words.txt' (one word per line) in the same folder
to use the downloaded English word list. If it is missing, a built-in list is used.
"""

import os
import random

MAX_MISTAKES = 6

DEFAULT_WORDS = [
    "python", "keyboard", "monitor", "program", "variable", "function",
    "network", "computer", "internet", "database", "developer", "library",
    "terminal", "algorithm", "software", "hardware", "browser", "student",
    "project", "challenge", "elephant", "mountain", "chocolate", "umbrella",
]

# ASCII gallows art: index = number of wrong guesses (0 to 6)
STAGES = [
    """
   +---+
   |   |
       |
       |
       |
       |
=========""",
    """
   +---+
   |   |
   O   |
       |
       |
       |
=========""",
    """
   +---+
   |   |
   O   |
   |   |
       |
       |
=========""",
    """
   +---+
   |   |
   O   |
  /|   |
       |
       |
=========""",
    """
   +---+
   |   |
   O   |
  /|\\  |
       |
       |
=========""",
    """
   +---+
   |   |
   O   |
  /|\\  |
  /    |
       |
=========""",
    """
   +---+
   |   |
   O   |
  /|\\  |
  / \\  |
       |
=========""",
]


def load_words(filename="words.txt"):
    """Load words from a text file if present, otherwise use the default list."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            words = [w.strip().lower() for w in f if w.strip().isalpha() and len(w.strip()) >= 4]
        if words:
            return words
    return DEFAULT_WORDS


def choose_word(words):
    return random.choice(words).lower()


def masked_word(secret, guessed):
    """Return the word with unguessed letters shown as '_'."""
    return " ".join(ch.upper() if ch in guessed else "_" for ch in secret)


def get_guess(guessed, wrong):
    """Ask for a valid single letter. Repeated guesses do not cost an attempt."""
    while True:
        guess = input("Guess a letter: ").strip().lower()
        if len(guess) != 1 or not guess.isalpha():
            print("Please enter a single letter (A-Z).")
        elif guess in guessed or guess in wrong:
            print(f"You already guessed '{guess.upper()}'. Try a different letter.")
        else:
            return guess


def show_status(secret, guessed, wrong):
    print(STAGES[len(wrong)])
    print(f"\nWord:   {masked_word(secret, guessed)}")
    print(f"Wrong:  {' '.join(sorted(l.upper() for l in wrong)) or '-'}")
    print(f"Attempts left: {MAX_MISTAKES - len(wrong)}\n")


def play_round(words):
    secret = choose_word(words)
    guessed = set()  # correct letters
    wrong = set()    # incorrect letters

    print("\n" + "=" * 40)
    print("        HANGMAN - Guess the word!")
    print("=" * 40)
    print(f"The word has {len(secret)} letters. You get {MAX_MISTAKES} mistakes.")

    while len(wrong) < MAX_MISTAKES and not set(secret) <= guessed:
        show_status(secret, guessed, wrong)
        guess = get_guess(guessed, wrong)
        if guess in secret:
            guessed.add(guess)
            print(f"Good job! '{guess.upper()}' is in the word.")
        else:
            wrong.add(guess)
            print(f"Sorry, '{guess.upper()}' is not in the word.")

    show_status(secret, guessed, wrong)
    if set(secret) <= guessed:
        print("*" * 40)
        print("  CONGRATULATIONS! YOU WON!")
        print(f"  The word was: {secret.upper()}")
        print("*" * 40)
    else:
        print("#" * 40)
        print("  GAME OVER! YOU LOST.")
        print(f"  The word was: {secret.upper()}")
        print("#" * 40)


def main():
    words = load_words()
    while True:
        play_round(words)
        again = input("\nPlay again? (y/n): ").strip().lower()
        if again != "y":
            print("Thanks for playing. Goodbye!")
            break


if __name__ == "__main__":
    main()
