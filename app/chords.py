
ROOTS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

CHORD_TYPES = [
    "", "m", "maj", "dim", "aug", "5",
    "sus2", "sus4",
    "6", "m6",
    "7", "maj7", "m7", "mMaj7",
    "dim7", "m7b5",
    "9", "maj9", "m9",
    "11", "13",
    "add9", "add11",
    "7b9", "7#9", "7b5", "7#5"
]

ALL_CHORDS = [root + chord for root in ROOTS for chord in CHORD_TYPES]

if __name__ == "__main__":
    print(ALL_CHORDS)