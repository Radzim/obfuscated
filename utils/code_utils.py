def ensure_python_code_prompt(prompt: str):
    prefix = "Write Python code."
    postfix = "Output only Python code and nothing else. CRITICAL:Do not include any markdown _or_ code block indicators."
    prompt = "\n".join([prefix, prompt, postfix])

    return prompt


def ensure_math_prompt(prompt: str):
    prefix = "Solve this math question."
    postfix = "Conclude your answer by saying: The final answer is $\\boxed{answer}$."
    prompt = "\n".join([prefix, prompt, postfix])

    return prompt

import re

def remove_comments_and_docstrings(code: str) -> str:
    # Remove all single-line comments
    code_no_single_line_comments = re.sub(r'#.*', '', code)
    
    # Remove all docstrings (both single and double quotes)
    code_no_docstrings = re.sub(r'""".*?"""', '', code_no_single_line_comments, flags=re.DOTALL)
    code_no_docstrings = re.sub(r"'''.*?'''", '', code_no_docstrings, flags=re.DOTALL)
    
    return code_no_docstrings
