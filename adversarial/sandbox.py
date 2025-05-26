from utils.code_utils import ensure_python_code_prompt
from models_openrouter.model_caller import ModelCaller
from models_openrouter import get_model

model_names = ["openai", "anthropic", "google", "deepseek", "meta"]
prompt = """
Given two arrays nums1 and nums2 of size m and n respectively, return the medians of
the two arrays. The overall run time complexity should be.
Constraints:
0 <= m <= 1000
0 <= n <= 1000
1 <= m + n <= 2000
-106 <= nums1[i], nums[2] <= 106
"""
for model_name in model_names:
    model = get_model(model_name)
    model_caller = ModelCaller(model, prompt_transform=ensure_python_code_prompt)
    answer = model_caller.get_code(prompt=prompt)
    print(model_name, answer)