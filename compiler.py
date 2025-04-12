import subprocess
import sys
import os
from werkzeug.utils import secure_filename


def run_code(code, language="python"):
    """
    Execute code and return the output.

    Args:
        code (str): The code to execute
        language (str): The programming language (currently only Python is supported)

    Returns:
        dict: Dictionary containing output and/or error
    """
    if language.lower() != "python":
        return {"output": None, "error": "Only Python language is currently supported"}

    if not code:
        return {"output": None, "error": "No code provided!"}

    # Secure filename
    filename = "temp_code.py"
    safe_filename = secure_filename(filename)

    try:
        # Save code in a temporary file
        with open(safe_filename, 'w') as file:
            file.write(code)

        # Execute the code safely with a timeout
        result = subprocess.run(
            [sys.executable, safe_filename],
            capture_output=True, text=True, timeout=10
        )

        output = result.stdout if result.returncode == 0 else None
        error = result.stderr if result.returncode != 0 else None

    except subprocess.TimeoutExpired:
        output = None
        error = "Error: Timeout exceeded while executing the code."
    except Exception as e:
        output = None
        error = f"An unexpected error occurred: {str(e)}"
    finally:
        # Remove the temporary file after execution
        if os.path.exists(safe_filename):
            os.remove(safe_filename)

    return {
        "output": output if output else None,
        "error": error if error else None
    }