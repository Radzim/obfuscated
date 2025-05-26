import time
import re
from typing import Callable
from .all_openrouter import BaseModel


def sanitise_response(response_string):
    # annoyingly, some LLMs seems wrap responses in ```python ... ```
    # here is a hacky way to remove these, so that we only deal with code itself
    # it will always be first line and either one or two last lines (it may also add an empty line)
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
    # verify that response from LLM is a valid Python code
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

    def __init__(
        self, model: BaseModel, n_retries: int = 10, prompt_transform: Callable = None
    ):
        self.model = model

        # Sometimes requests to Gemini seem to fail with a reason completely beyond user's control.
        ################
        #  ValueError: Invalid operation: The `response.text` quick accessor requires the response to contain a valid `Part`, but none were returned. The candidate's [finish_reason](https://ai.google.dev/api/generate-content#finishreason) is 4. Meaning that the model was reciting from copyrighted material.
        ################
        # Also LLMs may occasionally output invalid code
        # To account for it, we want to retry a few times
        # it normally works fine on first retry, but sometimes multiple retries are necesasary
        self.n_retries = n_retries

        # This is necessary to apply static changes to prompts
        # aka prompt engineering
        # for example, say something like "output only Python code"
        # which is important to keep the experiment clean
        # but clearly not something we want to augment in the experiment
        self.prompt_transform = prompt_transform

    def get_code(self, prompt):
        """
        Calls the wrapped model with the given prompt and returns the generated code.
        """
        if self.prompt_transform is not None:
            prompt = self.prompt_transform(prompt)

        no_codes = 0

        # see note in __init__ on retries
        for i in range(self.n_retries):
            time.sleep(i**2/10)
            # prompt = prompt + ' ' # in my experience hacks like this lowered the re-fail rate, but could be technically a reproducibility issue
            try:
                # if model requires delay between calls,
                # e.g. to stay under certain call rate,
                # do it right before we made a call
                time.sleep(self.model.call_timeout)
                response_string = self.model(prompt)
            except ValueError as e:
                print(f"Request failed, retrying. Error: {e}")
            else:
                code_string = sanitise_response(response_string)
                if is_valid_python_code(code_string):
                    # no more retries necessary
                    # break out of the retry loop
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
