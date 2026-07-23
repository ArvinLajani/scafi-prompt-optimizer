"""
ScaFi Compiler-in-the-Loop Script

This script accepts ScaFi/Scala code, writes it to a temporary file,
compiles it using SBT, and returns compilation status with error messages.
"""

import subprocess
import os
import sys
import shutil
import re
from pathlib import Path
from typing import Tuple


TEMP_FILE_PATH = "src/main/scala/it/unibo/scafi/test/TempScaFiApp.scala"

_SBT_NOISE_PATTERNS = [
    re.compile(r"welcome to sbt", re.IGNORECASE),
    re.compile(r"loading project definition", re.IGNORECASE),
    re.compile(r"loading settings for project", re.IGNORECASE),
    re.compile(r"set current project", re.IGNORECASE),
]

SCALA_WRAPPER_TEMPLATE = """package it.unibo.scafi.test

import it.unibo.scafi.test.FunctionalTestIncarnation.*

object TempScaFiApp:
  class TempProgram extends AggregateProgram with StandardSensors with BlockC with BlockG with BlockS:
    override def main(): Any =
  {user_code}
"""


def find_sbt_executable() -> str:
    """
    Find the SBT executable in the system PATH.
    
    Returns:
        Path to SBT executable if found.
        Raises FileNotFoundError if not found.
    """
    # Try standard 'sbt' command
    sbt_path = shutil.which("sbt")
    if sbt_path:
        return sbt_path
    
    # Try 'sbt.bat' on Windows
    sbt_bat = shutil.which("sbt.bat")
    if sbt_bat:
        return sbt_bat
    
    # Try 'sbt.cmd' on Windows
    sbt_cmd = shutil.which("sbt.cmd")
    if sbt_cmd:
        return sbt_cmd
    
    raise FileNotFoundError(
        "SBT not found in system PATH.\n"
        "Please install SBT: https://www.scala-sbt.org/download.html\n"
        "On Windows with Chocolatey: choco install sbt\n"
        "On macOS with Homebrew: brew install sbt\n"
        "On Linux: Follow instructions at https://www.scala-sbt.org/download.html"
    )


def extract_scafi_code(response: str) -> str:
    """
    Extract ScaFi/Scala code from an LLM response.
    
    Handles:
    - Markdown code fences (```scala ... ``` or ``` ... ```)
    - Falls back to entire response if no fences found
    - Strips dangling backticks and whitespace
    
    Args:
        response: Raw response from LLM, possibly with markdown formatting.
    
    Returns:
        Clean Scala code ready for compilation.
    """
    # First, try to extract code from markdown fences
    # Pattern 1: ```scala...``` (most specific)
    scala_fence_match = re.search(r"```scala\s*(.*?)\s*```", response, re.DOTALL)
    if scala_fence_match:
        return scala_fence_match.group(1).strip()
    
    # Pattern 2: ```...``` (generic code fence)
    generic_fence_match = re.search(r"```\s*(.*?)\s*```", response, re.DOTALL)
    if generic_fence_match:
        return generic_fence_match.group(1).strip()
    
    # Fallback: use entire response, but strip dangling backticks and trim
    code = response.strip()
    # Remove any leading/trailing backticks
    code = re.sub(r"^`+\s*", "", code)
    code = re.sub(r"\s*`+$", "", code)
    
    return code.strip()


def indent_code_block(code: str, indent_spaces: int = 4) -> str:
    """
    Indent a code block by the specified number of spaces.
    
    Indents every non-empty line, preserving relative indentation.
    
    Args:
        code: The code block to indent.
        indent_spaces: Number of spaces to indent (default: 4).
    
    Returns:
        Indented code block.
    """
    lines = code.split("\n")
    indented_lines = []
    indent_str = " " * indent_spaces
    
    for line in lines:
        if line.strip():  # Non-empty line
            indented_lines.append(indent_str + line)
        else:  # Empty line
            indented_lines.append("")
    
    return "\n".join(indented_lines)


def parse_compilation_errors(output: str) -> str:
    """
    Extract Scala compiler errors from raw SBT stdout/stderr.

    Filters sbt initialization noise, then returns lines starting with
    ``[error]``. Falls back to the last 15 non-noise lines if none found.
    """
    lines = output.splitlines()

    filtered_lines = [
        line
        for line in lines
        if not any(pattern.search(line) for pattern in _SBT_NOISE_PATTERNS)
    ]

    error_lines = [
        line for line in filtered_lines if line.strip().startswith("[error]")
    ]
    if error_lines:
        return "\n".join(error_lines)

    tail_source = filtered_lines if filtered_lines else lines
    return "\n".join(tail_source[-15:]).strip() or output.strip()


def compile_scafi_code(code: str, verbose: bool = False) -> Tuple[bool, str]:
    """
    Compiles ScaFi/Scala code by writing it to a temporary file and running SBT.
    
    Args:
        code: The ScaFi/Scala code to compile (without package/object wrapper).
        verbose: If True, print intermediate steps.
    
    Returns:
        A tuple (success: bool, output: str) where:
        - success is True if compilation succeeded, False otherwise.
        - output contains error messages if compilation failed, or success message if it succeeded.
    """
    
    # Get the workspace root directory
    workspace_root = Path.cwd()
    temp_file_full_path = workspace_root / TEMP_FILE_PATH
    
    try:
        # Check if SBT is available
        try:
            sbt_executable = find_sbt_executable()
            if verbose:
                print(f"[DEBUG] Found SBT at: {sbt_executable}")
        except FileNotFoundError as e:
            error_msg = str(e)
            if verbose:
                print(f"[DEBUG] {error_msg}")
            return False, error_msg
        
        # Ensure the directory exists
        temp_file_full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Extract code from markdown fences if present
        if verbose:
            print("[DEBUG] Extracting code from response...")
        extracted_code = extract_scafi_code(code)
        if verbose:
            print(f"[DEBUG] Extracted {len(extracted_code)} chars of code")
        
        # Indent the extracted code by 4 spaces per line
        if verbose:
            print("[DEBUG] Indenting code by 4 spaces per line...")
        indented_code = indent_code_block(extracted_code, indent_spaces=4)
        
        # Join code lines with newline + 2 spaces (to account for template indentation)
        # This ensures multi-line code blocks have consistent final indentation
        code_lines = indented_code.split('\n')
        final_code = '\n  '.join(code_lines)
        
        # Wrap the code with proper Scala structure
        wrapped_code = SCALA_WRAPPER_TEMPLATE.format(user_code=final_code)
        
        if verbose:
            print(f"[DEBUG] Writing temporary Scala file to: {temp_file_full_path}")
        
        # Write the wrapped code to the temporary file
        with open(temp_file_full_path, "w", encoding="utf-8") as f:
            f.write(wrapped_code)
        
        if verbose:
            print(f"[DEBUG] Temporary file created. Content:\n{wrapped_code}\n")
        
        # Run SBT compile
        if verbose:
            print(f"[DEBUG] Running '{sbt_executable} compile'...")
        
        result = subprocess.run(
            [sbt_executable, "compile"],
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            timeout=120,  # 2-minute timeout
        )
        
        # Check if compilation was successful
        if result.returncode == 0:
            if verbose:
                print("[DEBUG] Compilation succeeded!")
            return True, "Compilation successful."
        else:
            raw_output = result.stderr + result.stdout
            error_output = parse_compilation_errors(raw_output)
            if verbose:
                print(f"[DEBUG] Compilation failed. Raw output:\n{raw_output}")
                print(f"[DEBUG] Parsed errors:\n{error_output}")
            return False, error_output
    
    except subprocess.TimeoutExpired:
        error_msg = "Compilation timed out after 120 seconds."
        if verbose:
            print(f"[DEBUG] {error_msg}")
        return False, error_msg
    
    except Exception as e:
        error_msg = f"Unexpected error during compilation: {str(e)}"
        if verbose:
            print(f"[DEBUG] {error_msg}")
        return False, error_msg
    
    finally:
        # Clean up the temporary file
        try:
            if temp_file_full_path.exists():
                temp_file_full_path.unlink()
                if verbose:
                    print(f"[DEBUG] Temporary file deleted: {temp_file_full_path}")
        except Exception as e:
            if verbose:
                print(f"[DEBUG] Warning: Could not delete temporary file: {str(e)}")


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        # Read code from command line argument
        code = sys.argv[1]
        verbose = "--verbose" in sys.argv or "-v" in sys.argv
    else:
        # Example: simple ScaFi code
        code = """
val isSource = mid() == 0
val distance = foldhood(Double.PositiveInfinity)(math.min)(
    mux(isSource) { 0.0 } { Double.PositiveInfinity }
)(nbr(distance) + 1)
distance
        """
        verbose = True
    
    print("=" * 80)
    print("ScaFi Compiler-in-the-Loop")
    print("=" * 80)
    print(f"\nInput code:\n{code}\n")
    
    success, output = compile_scafi_code(code, verbose=verbose)
    
    print("\n" + "=" * 80)
    if success:
        print("✓ COMPILATION SUCCESSFUL")
    else:
        print("✗ COMPILATION FAILED")
    print("=" * 80)
    print(f"\nOutput:\n{output}\n")
    
    if not success and "SBT not found" in output:
        print("\n" + "!" * 80)
        print("ACTION REQUIRED: Install SBT")
        print("!" * 80)
        print("\nWindows (with Chocolatey):")
        print("  choco install sbt")
        print("\nmacOS (with Homebrew):")
        print("  brew install sbt")
        print("\nLinux or Manual Installation:")
        print("  Visit: https://www.scala-sbt.org/download.html\n")
    
    sys.exit(0 if success else 1)
