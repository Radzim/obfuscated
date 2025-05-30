import time
import re
from typing import Callable
from .all_openrouter import BaseModel


def sanitise_response(response_string):
    lines = response_string.split("\n")
    if len(lines[-1]) == 0:
        lines = lines[:-1]

    if "```" in lines[0]:
        lines = lines[1:]

    if "```" in lines[-1]:
        lines = lines[:-1]

    code_string = "\n".join(lines)
    return code_string


def is_valid_python_code(code_string):
    import ast

    try:
        ast.parse(code_string, filename="<unknown>", mode="exec")
    except (SyntaxError, ValueError) as _:
        return False

    return True


class ModelCaller:
    """A class to make calls the given LLM model.

    Args:
        n_retries: number of times to retry if model call fails for any reason
        prompt_transform: a function that can apply some tranformation to the prompt
    """
    def __init__(self, model: BaseModel, n_retries: int = 10, prompt_transform: Callable = None):
        self.model = model
        self.n_retries = n_retries
        self.prompt_transform = prompt_transform

    def get_code(self, prompt):
        """
        Calls the wrapped model with the given prompt and returns the generated code.
        """
        if self.prompt_transform is not None:
            prompt = self.prompt_transform(prompt)

        no_codes = 0

        for i in range(self.n_retries):
            time.sleep(i**2/10)
            try:
                time.sleep(self.model.call_timeout)
                response_string = self.model(prompt)
            except ValueError as e:
                print(f"Request failed, retrying. Error: {e}")
            else:
                code_string = sanitise_response(response_string)
                if is_valid_python_code(code_string):
                    break
                if no_codes > 1:
                    break
                else:
                    no_codes += 1
                    print("Request failed to produce valid code, retrying")
        else:
            raise RuntimeError(f"Failed to get valid code from {self.model.name}")

        return code_string


class ModelCallerMath:
    """
    A class to call the given LLM model and ensure the output contains a boxed answer.
    """

    def __init__(self, model: BaseModel, n_retries: int = 3, prompt_transform: Callable = None):
        self.model = model
        self.n_retries = n_retries
        self.prompt_transform = prompt_transform

    def get_code(self, prompt):
        if self.prompt_transform is not None:
            prompt = self.prompt_transform(prompt)

        no_boxed = 0

        for i in range(self.n_retries):
            time.sleep(i ** 2 / 10)
            try:
                time.sleep(self.model.call_timeout)
                response = self.model(prompt)
            except ValueError as e:
                print(f"Request failed, retrying. Error: {e}")
                continue
            if re.search(r"\\boxed\{.*?\}", response):
                return response
            else:
                no_boxed += 1
                if no_boxed > 1:
                    break
                print("No boxed answer found, retrying", no_boxed)

        raise RuntimeError(f"Failed to get boxed answer from {self.model.name}")
