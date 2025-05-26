import ast
import re
import unicodedata
import multiprocessing


def code_warning_detector(text_code):
    normalized_code = unicodedata.normalize("NFKC", text_code)
    # comments are safe
    normalized_code = "\n".join(line for line in normalized_code.split("\n") if not line.strip().startswith("#"))

    blocked_list = {
        "exec", "eval", "compile", "globals", "locals", "vars",
        "getattr", "setattr", "delattr", "os", "subprocess", "shutil",
        "sys", "ctypes", "cffi", "threading", "multiprocessing", "fcntl",
        "open", "write", "read", "delete", "unlink", "rename",
        "rmdir", "mkdir", "rmtree", "pathlib", "socket", "requests",
        "urllib", "http", "ftplib", "paramiko", "telnetlib", "asyncio",
        "twisted", "base64", "marshal", "pickle", "cryptography",
        "pycryptodome", "hashlib", "zlib", "memoryview", "buffer", "super",
        "execfile", "id", "object", "gc", "inspect", "breakpoint", "help"
    }
    # past blocked list: "remove", "del"

    # Use regex to ensure only full words (not substrings) are matched
    found_unsafe = set()
    for word in blocked_list:
        pattern = rf"\b{re.escape(word)}\b|\b{re.escape(word)}[.\//]"
        if re.search(pattern, normalized_code):
            found_unsafe.add(word)

    # If any unsafe keywords are found, warn the user
    if found_unsafe:
        raise RuntimeError("🚨 Unsafe code detected! Halting execution.")
        print(text_code, flush=True)  # Show the detected code
        print(f"⚠️ Potentially unsafe code detected: {', '.join(found_unsafe)}", flush=True)
        response = input("Do you confirm this code is safe? (Type 'safe' to continue): ").strip().lower()
        if response[:4] != "safe":
            raise RuntimeError("🚨 Unsafe code detected! Halting execution.")

    return text_code


import ast
import re

def safe_eval(val):
    replacements = {"true": "True", "false": "False", "null": "None"}
    val = val.strip()
    for k, v in replacements.items():
        val = re.sub(rf"\b{k}\b", v, val, flags=re.IGNORECASE)
    return ast.literal_eval(val)

def generate_test_cases(task_desc):
    test_cases = []
    lines = task_desc.strip().splitlines()
    in_code_block = False
    buffer = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Toggle code block
        if line.startswith("```"):
            in_code_block = not in_code_block
            if not in_code_block:
                # We're done collecting a code block
                input_line = output_line = ""
                for l in buffer:
                    l = l.strip()
                    if l.lower().startswith("input:"):
                        input_line = l.split(":", 1)[1].strip()
                    elif l.lower().startswith("output:"):
                        output_line = l.split(":", 1)[1].strip()

                if input_line and output_line:
                    try:
                        inputs = []
                        for part in re.split(r",\s*(?=\w+\s*=)", input_line):
                            if "=" in part:
                                _, val = part.split("=", 1)
                                inputs.append(safe_eval(val.strip()))
                            else:
                                inputs.append(safe_eval(part.strip()))
                        output = safe_eval(output_line)
                        test_cases.append((inputs, output))
                    except Exception:
                        pass
                buffer = []
            i += 1
            continue

        if in_code_block:
            buffer.append(line)
        else:
            # Handle inline format: Example + Input + Output
            if line.lower().startswith("example") and i + 2 < len(lines):
                l1 = lines[i + 1].strip()
                l2 = lines[i + 2].strip()
                if l1.lower().startswith("input:") and l2.lower().startswith("output:"):
                    input_line = l1.split(":", 1)[1].strip()
                    output_line = l2.split(":", 1)[1].strip()
                    try:
                        inputs = []
                        for part in re.split(r",\s*(?=\w+\s*=)", input_line):
                            if "=" in part:
                                _, val = part.split("=", 1)
                                inputs.append(safe_eval(val.strip()))
                            else:
                                inputs.append(safe_eval(part.strip()))
                        output = safe_eval(output_line)
                        test_cases.append((inputs, output))
                    except Exception:
                        pass
                    i += 2
            # Continue walking line by line
        i += 1

    return test_cases



def has_input_calls(code):
    """Check if the function contains any calls to input()."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input":
                return True
    except Exception as e:
        pass
        # print(f"AST Parsing Error: {e}", flush=True)
    return False



def worker_func(func_str_, test_cases_, queue):
    try:
        global_scope = {}
        exec(func_str_, global_scope)

        func_names = re.findall(r"def (\w+)\(", func_str_)
        if not func_names:
            queue.put(0)
            return

        best_score = 0
        for func_name in func_names:
            if func_name in global_scope:
                func = global_scope[func_name]
                correct = 0
                for inputs, expected in test_cases_:
                    # if not isinstance(inputs, tuple):
                    #     inputs = (inputs,)
                    try:
                        result = func(*inputs)
                        if result == expected:
                            correct += 1
                    except Exception as e:
                        print(e)
                        pass
                score = int(correct == len(test_cases_))  # 1 or 0
                best_score = max(best_score, score)

        queue.put(best_score)
    except:
        queue.put(0)

def evaluate_function(func_str_, test_cases_, timeout=5):
    if has_input_calls(func_str_):
        return 0

    queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=worker_func, args=(func_str_, test_cases_, queue))
    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        p.join()
        return 0

    return queue.get()


# def evaluate_function(func_str_, test_cases_):
#     if has_input_calls(func_str_):
#         # print("Function contains input() calls. Skipping execution.", flush=True)
#         return 0  # Consider input-blocking functions as failed
#
#     global_scope = {}  # Shared scope to execute the entire script
#
#     try:
#         exec(func_str_, global_scope)  # Execute the entire function string
#
#         func_names = re.findall(r"def (\w+)\(", func_str_)
#         if not func_names:
#             # print("No functions found!", flush=True)
#             return 0
#
#         best_score = 0
#
#         for func_name in func_names:
#             if func_name in global_scope:
#                 func = global_scope[func_name]  # Get function from global scope
#                 correct = 0
#
#                 for inputs, expected in test_cases_:
#                     if not isinstance(inputs, tuple):
#                         inputs = (inputs,)
#                     try:
#                         result = func(*inputs)
#                         # print(f"Function: {func_name}, Result: {result}, Expected: {expected}", flush=True)
#                         if result == expected:
#                             correct += 1
#                     except Exception as e:
#                         pass
#                         # print(f"Error in function '{func_name}' with input {inputs}: {e}", flush=True)
#
#                 score = correct / len(test_cases_)
#                 if score > best_score:
#                     best_score = score
#
#         # print(f"Best function: {best_func} with score: {best_score}", flush=True)
#         return best_score
#
#     except Exception as e:
#         print(f"Execution Error: {e}", flush=True)
#         return 0


def remove_type_annotations(func_str):
    lines = func_str.split("\n")
    for i, line in enumerate(lines):
        if line.strip().startswith("def "):
            # Remove return type annotations
            line = re.sub(r"\s*->\s*[^:]+:", ":", line)
            # Remove parameter type annotations
            line = re.sub(r"(\w+)\s*:\s*[^,)=]+", r"\1", line)
            lines[i] = line

    return "\n".join(lines)


def evaluate_solution(func_def_, task_desc_):
    try:
        func_def_ = remove_type_annotations(func_def_)
        func_def = code_warning_detector(func_def_)
        test_cases = generate_test_cases(task_desc_)
        # if len(test_cases) == 0:
        #     if 'spreadsheet' not in task_desc_ and 'hierarchy' not in task_desc_ and 'sample_id' not in task_desc_ and 'nums1 and nums2, both of length n' not in task_desc_:
        #         print(task_desc_)
        print(test_cases)
        if len(test_cases):
            return evaluate_function(func_def, test_cases)
        else:
            return 0
    except Exception as e:
        # print(func_def_, e, flush=True)
        print('FAILED EVAL: score 0.0', flush=True)
        return 0.0


def evaluate_math(func_def_, task_desc_):
    def extract_first_boxed(text):
        match = re.search(r'\\boxed\{(.*?)\}', text)
        print(match)
        if match:
            return re.sub(r'\s+', '', match.group(1))
        return None
    try:
        task_box = extract_first_boxed(task_desc_)
        func_box = extract_first_boxed(func_def_)
        if task_box is None or func_box is None:
            return 0.0
        return 1.0 if task_box == func_box else 0.0
    except Exception:
        return 0.0