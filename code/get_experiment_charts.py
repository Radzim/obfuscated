import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from collections import defaultdict

metrics_dir = "./augmented_datasets_metrics"
charts_dir = "./augmented_dataset_charts"
multi_model_dir = os.path.join(charts_dir, "aggregated", "multi_model")
combined_method_dir = os.path.join(charts_dir, "aggregated", "combined_methods")
os.makedirs(multi_model_dir, exist_ok=True)
os.makedirs(combined_method_dir, exist_ok=True)

colors = {
    'anthropic': '#E67E22',
    'deepseek': '#9B59B6',
    'google': '#C0392B',
    'meta': '#5DADE2',
    'openai': '#58D68D'
}

names = {
    'anthropic': 'Claude 3.5',
    'deepseek': 'DeepSeek V3',
    'google': 'Gemini 2.0',
    'meta': 'Llama 3.3',
    'openai': 'GPT-4o-mini'
}

dataset_names = {
    'oldleetcode.json': 'LeetCode (Old)',
    'newleetcode.json': 'LeetCode (New)',
    'math.json': 'MATH',
}

augmentation_names = {
    'cut': '(Truncation)',
    'random': '(Deletions)',
    'synonym': '(Synonyms)',
    'keyboard': '(Typos)',
}

mpl.rcParams.update({
    "font.size": 14,
    "font.family": "serif",
    "font.serif": ["cmr10"],
})

def plot_multi_model_chart(group_key, model_data, save_dir):
    fig, ax = plt.subplots()

    for model, series in model_data.items():
        if series.empty:
            continue
        ax.plot(
            series.index,
            series.values,
            label=names.get(model, model),
            marker='o',
            color=colors.get(model, None)
        )

    if "__" in group_key:
        dataset, method = group_key.split("__")
        dataset_label = dataset_names.get(dataset, dataset)
        method_label = augmentation_names.get(method, method)
        title = f"{dataset_label} {method_label}"
    else:
        title = dataset_names.get(group_key, group_key)

    ax.set_title(title)
    ax.set_xlabel("Augmentation Rate")
    ax.set_ylabel("Eval Score")
    ax.set_ylim(0, 1)
    ax.grid(True)
    ax.legend(title="Model")

    fig.tight_layout()
    save_path = os.path.join(save_dir, f"{group_key}_multi_model.png")
    plt.savefig(save_path)
    plt.close()

    df = pd.DataFrame({ names.get(m, m): s for m, s in model_data.items() })
    df.index.name = "Augmentation Rate"
    csv_path = os.path.join(save_dir, f"{group_key}_multi_model.csv")
    df.to_csv(csv_path)

def collect_data(metrics_dir, methods_to_include=None):
    double_grouped = defaultdict(lambda: defaultdict(list))
    combined_methods = defaultdict(lambda: defaultdict(list))

    for root, _, files in os.walk(metrics_dir):
        for file in files:
            if not file.endswith(".csv"):
                continue

            file_path = os.path.join(root, file)
            df = pd.read_csv(file_path)

            if df.empty or "augmentation_rate" not in df.columns or "eval_score" not in df.columns:
                continue

            df["augmentation_rate"] = df["augmentation_rate"].astype(float)
            df["eval_score"] = pd.to_numeric(df["eval_score"], errors="coerce")
            if df.empty:
                continue

            path_parts = os.path.normpath(file_path).split(os.sep)
            model, method, dataset = path_parts[-4:-1]

            if methods_to_include is not None and method not in methods_to_include:
                continue

            method_key = f"{dataset}__{method}"
            grouped = df.groupby("augmentation_rate")["eval_score"].mean().reset_index()

            double_grouped[method_key][model].append(grouped)
            combined_methods[dataset][model].append(grouped)

    return double_grouped, combined_methods



def generate_multi_model_charts(methods_to_include=None):
    double_grouped, combined_methods = collect_data(metrics_dir, methods_to_include)

    for group_key, model_data in double_grouped.items():
        if methods_to_include is not None:
            dataset, method = group_key.split("__")
            if method not in methods_to_include:
                continue

        agg_per_model = {}
        for model, frames in model_data.items():
            combined_df = pd.concat(frames)
            agg = combined_df.groupby("augmentation_rate")["eval_score"].apply(lambda x: x.fillna(0).mean())

            if method in ["random", "keyboard", "synonym"] and 0.0 in agg.index:
                values = []
                for m in ["cut"]:
                    alt_key = f"{dataset}__{m}"
                    alt_frames = double_grouped.get(alt_key, {}).get(model, [])
                    if alt_frames:
                        alt_df = pd.concat(alt_frames)
                        alt_agg = alt_df.groupby("augmentation_rate")["eval_score"].apply(lambda x: x.fillna(0).mean())
                        if 0.0 in alt_agg.index:
                            values.append(alt_agg.loc[0.0])
                if values:
                    agg.loc[0.0] = sum(values) / len(values)
                else:
                    agg = agg.drop(index=0.0)

            agg_per_model[model] = agg

        if any(not s.empty for s in agg_per_model.values()):
            plot_multi_model_chart(group_key, agg_per_model, multi_model_dir)

    #  grouped by dataset (combined over methods)
    for dataset_key, model_data in combined_methods.items():
        agg_per_model = {}
        for model, frames in model_data.items():
            combined_df = pd.concat(frames)
            agg = combined_df.groupby("augmentation_rate")["eval_score"].apply(lambda x: x.fillna(0).mean())

            cut_key = f"{dataset_key}__cut"
            cut_frames = double_grouped.get(cut_key, {}).get(model, [])
            if cut_frames:
                cut_df = pd.concat(cut_frames)
                cut_agg = cut_df.groupby("augmentation_rate")["eval_score"].apply(lambda x: x.fillna(0).mean())
                if 0.0 in agg.index:
                    if 0.0 in cut_agg.index:
                        agg.loc[0.0] = cut_agg.loc[0.0]
                    else:
                        agg = agg.drop(index=0.0)

            agg_per_model[model] = agg

        if any(not s.empty for s in agg_per_model.values()):
            plot_multi_model_chart(dataset_key, agg_per_model, combined_method_dir)


if __name__ == "__main__":
    generate_multi_model_charts(methods_to_include=["cut", "random", "keyboard"])
