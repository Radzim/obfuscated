import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

# colors
dark_blue = '#00008B'  # LLMs
dark_red = '#8B0000'   # Humans

# mappings for titles
dataset_names = {
    'oldleetcode.json': 'LeetCode (Old)',
    'newleetcode.json': 'LeetCode (New)',
    'math.json': 'MATH',
    'code.json': 'LeetCode',
}

augmentation_names = {
    'cut': '(Truncation)',
    'random': '(Deletions)',
    'synonym': '(Synonyms)',
    'keyboard': '(Typos)',
}

# Matplotlib styling
mpl.rcParams.update({
    "font.size": 14,
    "font.family": "serif",
    "font.serif": ["cmr10"],
})

# plotting shaded areas for each model or average
def plot_shaded_chart(title, x, series_list, count_label, color, save_path):
    fig, ax = plt.subplots()
    for y in series_list:
        ax.fill_between(x, y.values, alpha=0.25, color=color)
    ax.set_title(title)
    ax.set_xlabel("Augmentation Rate")
    ax.set_ylabel("Relative Eval Score")
    ax.set_ylim(0, 1)
    ax.grid(True)
    ax.legend([count_label], title="Models")
    fig.tight_layout()
    plt.savefig(save_path)
    plt.close()

# main processing
def main():
    input_dirs = ['llm', 'human']  # renamed folder
    output_dir = 'plots'
    os.makedirs(output_dir, exist_ok=True)

    # storage for normalized DataFrames per dataset
    avg_data = {d: {} for d in input_dirs}

    for input_dir in input_dirs:
        is_human = (input_dir == 'human')
        color = dark_red if is_human else dark_blue
        for fname in os.listdir(input_dir):
            if not fname.endswith('.csv'):
                continue

            # derive key and strip suffixes
            base = os.path.splitext(fname)[0]
            key = base.replace('_multi_model', '').replace('_human', '')

            # parse dataset and augmentation method
            if '__' in key:
                dataset_key, method_key = key.split('__', 1)
            else:
                dataset_key, method_key = key, None

            # build title for method-level plot
            dataset_label = dataset_names.get(dataset_key, dataset_key)
            title = f"{dataset_label} {augmentation_names.get(method_key, '')}".strip()

            # read, interpolate, normalize
            path = os.path.join(input_dir, fname)
            df = pd.read_csv(path, index_col=0)
            df = df.interpolate(method='linear', axis=0, limit_direction='both')
            norm = df.div(df.iloc[0]).clip(upper=1)

            # individual model/human series
            series_list = [norm[col] for col in norm.columns]
            count_label = f"{len(series_list)} Humans" if is_human else f"{len(series_list)} LLMs"

            # plot file-level shaded areas
            out_name = f"{input_dir}_{key}_shaded.png"
            plot_shaded_chart(title, norm.index, series_list, count_label, color,
                               os.path.join(output_dir, out_name))

            # save normalized CSV
            norm.to_csv(os.path.join(output_dir, f"{input_dir}_{key}_shaded.csv"))

            # store normalized DF for dataset-level aggregation
            avg_data[input_dir].setdefault(dataset_key, []).append(norm)

    # plot dataset-level averages per folder
    for input_dir, datasets in avg_data.items():
        is_human = (input_dir == 'human')
        color = dark_red if is_human else dark_blue
        for dataset_key, dfs in datasets.items():
            # compute per-model/human average over methods
            df_sum = sum(dfs)
            df_avg = df_sum.div(len(dfs))  # average across methods
            df_avg.index.name = 'Augmentation Rate'

            # prepare series list: one per model/human
            series_list = [df_avg[col] for col in df_avg.columns]
            count_label = f"{len(series_list)} Humans" if is_human else f"{len(series_list)} LLMs"

            dataset_label = dataset_names.get(dataset_key, dataset_key)
            title = f"{dataset_label} (Average Over Methods)"

            # plot dataset-level shaded curves
            out_name = f"{input_dir}_{dataset_key}_average_shaded.png"
            plot_shaded_chart(title, df_avg.index, series_list, count_label, color,
                               os.path.join(output_dir, out_name))

            # save average CSV with proper headers
            csv_out = os.path.join(output_dir, f"{input_dir}_{dataset_key}_average.csv")
            df_avg.to_csv(csv_out)

    print(f"Plotting complete. Outputs in '{output_dir}'.")

if __name__ == '__main__':
    main()
