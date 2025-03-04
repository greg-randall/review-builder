import os
import sys
from collections import Counter

import nltk
from nltk.tokenize import word_tokenize

from .cost_calculator import CostCalculator
from .epub_extractor import EpubExtractor
from .llm_core import GPT4O, GPT4oMini, LLMClient

# Ensure necessary NLTK resources are downloaded
nltk.download("punkt")


class BookAnalyzer:
    def __init__(self, epub_path: str):
        self.epub_path = epub_path
        self.extractor = EpubExtractor(epub_path)
        self.chapters = self.extractor._get_chapters()
        self.tokenized_chapters = [word_tokenize(chapter) for chapter in self.chapters]

    def _default_save_path(self) -> str:
        return os.path.splitext(self.epub_path)[0] + "_stats.md"

    def word_counts(self) -> tuple[int, list[int]]:
        total_word_count = sum(len(tokens) for tokens in self.tokenized_chapters)
        chapter_word_counts = [len(tokens) for tokens in self.tokenized_chapters]
        return total_word_count, chapter_word_counts

    def token_counts(self) -> dict[str, tuple[int, list[int]]]:
        token_counts = {}
        models = [GPT4oMini(), GPT4O()]
        for model in models:
            calculator = CostCalculator(model)
            total_token_count = sum(len(calculator.encoding.encode(chapter)) for chapter in self.chapters)
            chapter_token_counts = [len(calculator.encoding.encode(chapter)) for chapter in self.chapters]
            token_counts[model.model_name] = (total_token_count, chapter_token_counts)
        return token_counts

    def word_frequencies(self) -> dict[str, int]:
        all_tokens = [token for tokens in self.tokenized_chapters for token in tokens]
        frequency = Counter(all_tokens)
        return dict(frequency.most_common())

    def calculate_cost(self, model_client: LLMClient) -> float:
        full_text = " ".join([" ".join(chapter) for chapter in self.tokenized_chapters])
        calculator = CostCalculator(model_client)
        return calculator.calculate_cost(full_text)

    def write_statistics(self, save_path: str = None) -> None:
        save_path = save_path or self._default_save_path()
        total_word_count, chapter_word_counts = self.word_counts()
        token_counts = self.token_counts()
        word_frequencies = self.word_frequencies()

        models = list(token_counts.keys())

        with open(save_path, "w") as file:
            file.write("# Book Statistics\n\n")
            file.write("## Overview\n\n")
            file.write(f"Total Word Count: {total_word_count:,}\n\n")

            file.write("| Model | Cost |\n")
            file.write("|-------|------|\n")
            for model in [GPT4oMini(), GPT4O()]:
                cost = self.calculate_cost(model)
                file.write(f"| {model.model_name} | ${cost:.2f} |\n")
            file.write("\n")

            file.write("## Word and Token Counts per Chapter\n\n")
            file.write("| Chapter | Words |" + " | ".join(f"{model} Tokens" for model in models) + " |\n")
            file.write("|---------|-------|" + " | ".join(["--------"] * len(models)) + "|\n")
            for i, word_count in enumerate(chapter_word_counts):
                token_counts_row = " | ".join(f"{token_counts[model][1][i]:,}" for model in models)
                file.write(f"| {i+1} | {word_count:,} | {token_counts_row} |\n")

            file.write("## Word Frequencies (First 200 Words)\n\n")
            file.write("| Word | Frequency |\n")
            file.write("|------|-----------|\n")
            for i, (word, frequency) in enumerate(word_frequencies.items()):
                if i >= 200:
                    break
                file.write(f"| {word} | {frequency} |\n")
            file.write("\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python epub_word_analyzer.py <epub_path>")
        sys.exit(1)

    epub_path = sys.argv[1]

    try:
        analyzer = BookAnalyzer(epub_path)
        output_file = os.path.splitext(epub_path)[0] + "_word_stats.md"
        analyzer.write_statistics(output_file)
        print(f"Word statistics extracted and saved to {output_file}")
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
