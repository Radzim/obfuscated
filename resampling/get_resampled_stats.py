import os
import pandas as pd
import numpy as np
from scipy.stats import linregress

def interpolate_half_max(x, y):
    for i in range(1, len(y)):
        if y[i] < 0.5 <= y[i - 1]:
            x1, x2 = x[i - 1], x[i]
            y1, y2 = y[i - 1], y[i]
            return x1 + (0.5 - y1) * (x2 - x1) / (y2 - y1)
    return np.nan

def truncate_at_last_nonzero(x, y):
    nonzero_indices = y.to_numpy().nonzero()[0]
    if len(nonzero_indices) == 0:
        return x, y
    last_idx = nonzero_indices[-1]
    return x.iloc[:last_idx + 1], y.iloc[:last_idx + 1]

def process_file(filepath):
    df = pd.read_csv(filepath)
    n_trials = 60
    n_resamples = 200

    df["LLM Average (Original)"] = df.iloc[:, 1:].mean(axis=1)
    baseline_original = df.loc[0, "LLM Average (Original)"]
    df["Relative (Original)"] = (df["LLM Average (Original)"] / baseline_original).clip(upper=1.0)

    x = df["Augmentation Rate"]
    resampled_metrics = {"Average": [], "Gradient (Slope)": [], "50% Interpolation Point": [], "Last Non-Zero Point": []}

    for _ in range(n_resamples):
        resampled_data = {}
        for col in df.columns[1:-2]:
            resampled_data[col] = [
                np.random.binomial(n_trials, p) / n_trials for p in df[col]
            ]
        resampled_df = pd.DataFrame({
            "Augmentation Rate": df["Augmentation Rate"],
            **resampled_data
        })
        resampled_df["LLM Average (Resampled)"] = resampled_df.iloc[:, 1:].mean(axis=1)
        baseline_resampled = resampled_df.loc[0, "LLM Average (Resampled)"]
        resampled_df["Relative (Resampled)"] = (resampled_df["LLM Average (Resampled)"] / baseline_resampled).clip(upper=1.0)
        y = resampled_df["Relative (Resampled)"]

        avg = y.mean()
        x_trimmed, y_trimmed = truncate_at_last_nonzero(x, y)
        slope, _, _, _, _ = linregress(x_trimmed, y_trimmed)
        half_max = interpolate_half_max(x, y)
        last_non_zero = np.nan if all(y > 0) else x[y.gt(0)].max()

        resampled_metrics["Average"].append(avg)
        resampled_metrics["Gradient (Slope)"].append(slope)
        resampled_metrics["50% Interpolation Point"].append(half_max)
        resampled_metrics["Last Non-Zero Point"].append(last_non_zero)

    def ci(values):
        sorted_vals = np.sort(values)
        return (sorted_vals[-6] - sorted_vals[5]) / 2

    x_trimmed, y_trimmed = truncate_at_last_nonzero(x, df["Relative (Original)"])
    results = {
        "Value": {
            "Average": df["Relative (Original)"].mean(),
            "Gradient (Slope)": linregress(x_trimmed, y_trimmed)[0],
            "50% Interpolation Point": interpolate_half_max(x, df["Relative (Original)"]),
            "Last Non-Zero Point": np.nan if all(df["Relative (Original)"] > 0) else x[df["Relative (Original)"].gt(0)].max()
        },
        "+-": {metric: ci(vals) for metric, vals in resampled_metrics.items()}
    }

    return pd.DataFrame(results)

def main():
    data_dir = "data"
    output = {}

    for filename in os.listdir(data_dir):
        if filename.endswith(".csv"):
            path = os.path.join(data_dir, filename)
            metrics = process_file(path)
            output[filename] = metrics

    for fname, df in output.items():
        print(f"Metrics for {fname}")
        print(df)
        print()

if __name__ == "__main__":
    main()