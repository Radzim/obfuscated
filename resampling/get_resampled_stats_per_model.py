import os
import pandas as pd
import numpy as np

def interpolate_half_max(x, y):
    for i in range(1, len(y)):
        if y[i] < 0.5 <= y[i - 1]:
            x1, x2 = x[i - 1], x[i]
            y1, y2 = y[i - 1], y[i]
            return x1 + (0.5 - y1) * (x2 - x1) / (y2 - y1)
    return np.nan

def process_file(filepath):
    df = pd.read_csv(filepath)
    n_trials = 60
    n_resamples = 200
    x = df["Augmentation Rate"]
    models = df.columns[1:]

    results = []

    for model in models:
        original = df[model]
        baseline = original.iloc[0]
        original_rel = (original / baseline).clip(upper=1.0)
        point = interpolate_half_max(x, original_rel)

        resampled_halfmax = []
        resampled_zero = []

        for _ in range(n_resamples):
            sampled = [np.random.binomial(n_trials, p) / n_trials for p in original]
            sampled = pd.Series(sampled)
            rel = (sampled / sampled.iloc[0]).clip(upper=1.0)
            resampled_halfmax.append(interpolate_half_max(x, rel))
            resampled_zero.append(sampled.iloc[0])  # value at 0.0 aug

        sorted_halfmax = np.sort(resampled_halfmax)
        sorted_zero = np.sort(resampled_zero)
        ci_halfmax = (sorted_halfmax[-6] - sorted_halfmax[5]) / 2
        ci_zero = (sorted_zero[-6] - sorted_zero[5]) / 2
        baseline_mean = np.mean(resampled_zero)

        results.append((
            model,
            round(point, 2),
            f"± {round(ci_halfmax, 2)}",
            round(baseline_mean, 2),
            f"± {round(ci_zero, 2)}"
        ))

    return results


data_dir = "data"
for fname in os.listdir(data_dir):
    if fname.endswith(".csv"):
        path = os.path.join(data_dir, fname)
        print(f"\nFile: {fname}")
        result = process_file(path)
        for model, decay, decay_ci, base, base_ci in result:
            print(f"{model:<15}  50% Decay: {decay} {decay_ci} | Baseline (0.0): {base} {base_ci}")
