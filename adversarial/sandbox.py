from utils.code_utils import ensure_python_code_prompt
from models_openrouter.model_caller import ModelCaller
from models_openrouter import get_model

model_names = ["openai", "anthropic", "google", "deepseek", "meta"]
prompt = """
Write Python code to solve the following problem:

Consider an array that consists of two concatenated sorted arrays of size m and n. Identify
which of two arrays has more elements. The overall run time complexity should be O(log (m+n)).

Constraints:
0 <= m <= 1000
0 <= n <= 1000
1 <= m + n <= 2000
-106 <= array[i] <= 106
"""
for model_name in model_names:
    model = get_model(model_name)
    model_caller = ModelCaller(model, prompt_transform=ensure_python_code_prompt)
    answer = model_caller.get_code(prompt=prompt)
    print(model_name)
    print(answer)
    print('-------------------------------------')