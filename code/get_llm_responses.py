import os
import json
import concurrent.futures
import time
import random
from utils.code_utils import ensure_python_code_prompt
from models.model_caller import ModelCaller
from models_openrouter.all_openrouter import get_model_openrouter as get_model


def call_with_retry(model_caller, prompt, retries=3, timeout=30):
    time.sleep(random.uniform(0, 3))
    for attempt in range(retries):
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(model_caller.get_code, prompt)
                return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            if attempt == retries - 1:
                return f"ERROR: Timeout after {retries} attempts"
            time.sleep(1)
        except Exception as e:
            return f"ERROR: {str(e)}"


def get_output_path(base_dir, model, method, filename, item_idx):
    return os.path.join(base_dir, model, method, filename, f"Q{item_idx:05d}.json")


def load_existing_rate(output_path, model, method, rate_str):
    if not os.path.exists(output_path):
        return []
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            item = json.load(f)
        return item.get("llm_responses", {}).get(model, {}).get(method, {}).get(rate_str, [])
    except Exception:
        return []


def save_response(output_path, original_item, model, method, rate_str, responses, n_repeats):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            item = json.load(f)
    else:
        item = dict(original_item)
        item["llm_responses"] = {}

    item.setdefault("llm_responses", {}).setdefault(model, {}).setdefault(method, {})[rate_str] = responses[:n_repeats]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(item, f, indent=2)


def main():
    input_dir = "augmented_datasets"
    output_base = "augmented_datasets_llm_responses"
    os.makedirs(output_base, exist_ok=True)

    model_names = ["openai", "anthropic", "google", "deepseek", "meta"]
    n_repeats = 1

    for filename in os.listdir(input_dir):
        if not filename.endswith(".json"):
            continue

        input_path = os.path.join(input_dir, filename)
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for model_name in model_names:
            model = get_model(model_name)
            model_caller = ModelCaller(model, prompt_transform=ensure_python_code_prompt)

            for item_idx, item in enumerate(data):
                augmented = item.get("augmented_questions", {})

                for method, versions in augmented.items():
                    tasks = []
                    for rate, prompt in versions.items():
                        rate_str = str(rate)
                        output_path = get_output_path(output_base, model_name, method, filename, item_idx)
                        existing = load_existing_rate(output_path, model_name, method, rate_str)

                        if isinstance(existing, list) and len(existing) >= n_repeats:
                            print("[SKIP]", model_name, filename, item_idx, method, rate_str)
                            continue

                        tasks.append((rate, rate_str, prompt, output_path))

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = {
                            executor.submit(call_with_retry, model_caller, prompt): (rate, rate_str, output_path)
                            for rate, rate_str, prompt, output_path in tasks
                        }

                        results = []
                        for future in concurrent.futures.as_completed(futures):
                            rate, rate_str, output_path = futures[future]
                            try:
                                result = future.result()
                            except Exception as e:
                                result = f"ERROR: {str(e)}"
                            results.append((rate, rate_str, result))

                    results.sort()
                    for rate, rate_str, response in results:
                        output_path = get_output_path(output_base, model_name, method, filename, item_idx)
                        save_response(output_path, item, model_name, method, rate_str, [response], n_repeats)
                    print("[SAVED]", model_name, filename, item_idx, method,)


if __name__ == "__main__":
    main()
