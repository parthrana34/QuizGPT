import argparse
import json
import sys

from .generator import QuizGPT


def main() -> None:
    parser = argparse.ArgumentParser(prog="quizgpt", description="Generate quizzes from text, URLs, or YouTube transcripts.")
    parser.add_argument("--input", required=True, help="Input text, web page URL, or YouTube URL.")
    parser.add_argument("--api-key", required=False, help="OpenAI API key.")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="medium", help="Quiz difficulty level.")
    parser.add_argument("--question-type", choices=["mcq"], default="mcq", help="Question type for the generated quiz.")
    parser.add_argument("--output", help="Path to write JSON output. If omitted, prints to stdout.")
    args = parser.parse_args()

    generator = QuizGPT(api_key=args.api_key)
    result = generator.generate_quiz(
        input_text=args.input,
        difficulty=args.difficulty,
        question_type=args.question_type,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as output_file:
            json.dump(result, output_file, indent=2, ensure_ascii=False)
        print(f"Quiz generated and saved to {args.output}")
    else:
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
