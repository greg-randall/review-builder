import nltk
from nltk.tokenize import word_tokenize
from collections import Counter
from typing import List, Dict, Tuple
import sys
import os
from epub_extractor import EpubExtractor
from cost_calculator import (
    CostCalculator,
)

# Ensure necessary NLTK resources are downloaded
nltk.download("punkt")


class EpubWordAnalyzer:
    def __init__(self, epub_file: str):
        self.extractor = EpubExtractor(epub_file)
        self.chapters = self.extractor._get_chapters()
        self.tokenized_chapters = [word_tokenize(chapter) for chapter in self.chapters]

    def get_word_counts(self) -> Tuple[int, List[int]]:
        total_word_count = sum(len(tokens) for tokens in self.tokenized_chapters)
        chapter_word_counts = [len(tokens) for tokens in self.tokenized_chapters]
        return total_word_count, chapter_word_counts

    def get_word_frequency(self) -> Dict[str, int]:
        all_tokens = [token for tokens in self.tokenized_chapters for token in tokens]
        frequency = Counter(all_tokens)
        sorted_frequency = dict(frequency.most_common())
        return sorted_frequency

    def calculate_book_cost(self, model_name: str) -> float:
        full_text = " ".join([" ".join(chapter) for chapter in self.chapters])
        calculator = CostCalculator(model_name)
        return calculator.calculate_cost(full_text)

    def write_word_statistics(self, output_file: str) -> None:
        total_word_count, chapter_word_counts = self.get_word_counts()
        word_frequencies = self.get_word_frequency()

        with open(output_file, "w") as file:
            file.write(f"Total Word Count: {total_word_count}\n\n")

            for i, count in enumerate(chapter_word_counts):
                file.write(f"Chapter {i+1} Word Count: {count}\n")

            file.write("\nCost Calculations for each model:\n")
            for model in CostCalculator.model_costs:
                cost = self.calculate_book_cost(model)
                file.write(f"Cost for {model}: {cost:.6f}\n")

            file.write("\nWord Frequencies (entire book):\n")
            for word, frequency in word_frequencies.items():
                file.write(f"{word}: {frequency}\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python epub_word_analyzer.py <epub_file>")
        sys.exit(1)

    epub_file = sys.argv[1]

    try:
        analyzer = EpubWordAnalyzer(epub_file)
        output_file = os.path.splitext(epub_file)[0] + "_word_stats.txt"
        analyzer.write_word_statistics(output_file)
        print(f"Word statistics extracted and saved to {output_file}")
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
