import multiprocessing
import os
import json
import csv
from utils import code_execute
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

def calculate_metrics_to_csv(data_dir="./augmented_datasets_llm_responses/", out_dir="./augmented_datasets_metrics/", partial=False):
    for model in os.listdir(data_dir):
        model_dir = os.path.join(data_dir, model)
        for method in os.listdir(model_dir):
            method_dir = os.path.join(model_dir, method)
            for dataset in os.listdir(method_dir):
                dataset_dir = os.path.join(method_dir, dataset)

                for item_file in os.listdir(dataset_dir):
                    changed = False

                    task = item_file.replace(".json", "")
                    rel_dir = os.path.join(model, method, dataset)
                    out_subdir = os.path.join(out_dir, rel_dir)
                    os.makedirs(out_subdir, exist_ok=True)
                    out_csv = os.path.join(out_subdir, f"{task}.csv")

                    item_path = os.path.join(dataset_dir, item_file)
                    with open(item_path, "r", encoding="utf-8") as f:
                        item = json.load(f)

                    method_responses = item.get("llm_responses", {}).get(model, {}).get(method, {})
                    original_codes = method_responses.get("0.0", [])
                    if not original_codes:
                        continue

                    # original_prompt = item.get("question", "")
                    original_prompt = item.get("solution", "")

                    # Regenerate all rows fresh from the JSON
                    existing_rows = []
                    for rate_str, responses in sorted(method_responses.items(), key=lambda x: float(x[0])):
                        for _ in responses:
                            existing_rows.append({
                                "model": model,
                                "method": method,
                                "dataset": dataset,
                                "task": task,
                                "augmentation_rate": rate_str,
                                "eval_score": ""
                            })
                    changed = True

                    updated_rows = []
                    aug_counts = {}

                    for i, row in enumerate(existing_rows):
                        try:
                            aug_rate = row["augmentation_rate"]
                            rate_responses = method_responses.get(aug_rate, [])
                            index_within_rate = aug_counts.get(aug_rate, 0)

                            code = rate_responses[index_within_rate]
                            aug_counts[aug_rate] = index_within_rate + 1

                            if code and not code.startswith("ERROR"):
                                # score = code_execute.evaluate_solution(code, original_prompt)
                                score = code_execute.evaluate_math(code, original_prompt)
                                row["eval_score"] = score
                                changed = True
                                print(f"{model} {method} {dataset} {task} [EVAL] @ {aug_rate} #{index_within_rate}: {score}")
                        except Exception as e:
                            print(f"[ERROR] {item_path} – {e}")
                        updated_rows.append(row)

                    if updated_rows and changed:
                        with open(out_csv, "w", newline='', encoding="utf-8") as f:
                            writer = csv.DictWriter(f, fieldnames=["model", "method", "dataset", "task", "augmentation_rate", "eval_score"])
                            writer.writeheader()
                            writer.writerows(updated_rows)
                        print(f"[SAVED] {out_csv}")

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    calculate_metrics_to_csv(partial=True)
