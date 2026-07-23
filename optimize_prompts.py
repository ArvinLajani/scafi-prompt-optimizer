"""
ScaFi Prompt Optimization Loop

This script orchestrates an iterative prompt optimization process:
1. Load tasks from dataset JSON
2. Generate code using an LLM with a base system prompt
3. Compile the generated code
4. If compilation fails, route error to a critic LLM for prompt refinement
"""

import json
import os
import re
import time
import random
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple
from abc import ABC, abstractmethod

from compile_scafi import compile_scafi_code


_CRITIC_OUTPUT_DIRECTIVE = (
    "Output ONLY a 1-sentence correction rule to append to the system prompt. "
    "Do NOT explain or generate full code examples in the critic output."
)

_CANONICAL_SCAFI_EXAMPLES = (
    "CANONICAL SYNTAX EXAMPLES:\n"
    "- Hop Count (discrete network hops — MUST use `+ 1.0`, NOT `+ nbrRange()`):\n"
    '  `val hopCount = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("source")) { 0.0 } { minHoodPlus(nbr(d) + 1.0) })`\n'
    "- Gradient Distance (physical distance — use `+ nbrRange()`):\n"
    '  `rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("source")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })`'
)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Task:
    """Represents a task to optimize code for."""
    name: str
    description: str
    knowledge_file: str

    @staticmethod
    def from_json_entry(entry: dict) -> "Task":
        """Parse a task from a JSON entry in the dataset."""
        return Task(
            name=entry.get("testName", "Unnamed Task"),
            description=entry.get("testName", "No description"),
            knowledge_file=entry.get("knowledgeFile", "knowledge/no-knowledge.md"),
        )


@dataclass
class OptimizationResult:
    """Result of a single optimization attempt."""
    task: Task
    generated_code: str
    compilation_success: bool
    compilation_error: Optional[str]
    system_prompt: str
    iteration: int


# ============================================================================
# LLM Client Abstraction
# ============================================================================

class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate_code(self, system_prompt: str, user_prompt: str) -> str:
        """Generate ScaFi code given system and user prompts."""
        pass

    @abstractmethod
    def generate_critic_prompt(self, error_message: str, failed_code: str) -> str:
        """Generate prompt refinement suggestions based on compilation error."""
        pass


class OpenAIClient(LLMClient):
    """OpenAI GPT-4 LLM client."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. "
                "Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize the OpenAI client (lazy import)."""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "openai package not installed. "
                "Install it with: pip install openai"
            )

    def generate_code(self, system_prompt: str, user_prompt: str) -> str:
        """Generate code using GPT-4."""
        response = self.client.chat.completions.create(
            model="gpt-4",
            temperature=0.7,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content.strip()

    def generate_critic_prompt(self, error_message: str, failed_code: str) -> str:
        """Ask GPT-4 to suggest prompt refinements."""
        critic_system = (
            "You are a ScaFi code expert and prompt engineer. "
            "Analyze compilation errors and suggest how the prompt should be refined."
        )
        critic_user = f"""
The following ScaFi code failed to compile:

```scala
{failed_code}
```

Compilation error:
```
{error_message}
```

{_CRITIC_OUTPUT_DIRECTIVE}
"""
        response = self.client.chat.completions.create(
            model="gpt-4",
            temperature=0.5,
            max_tokens=512,
            messages=[
                {"role": "system", "content": critic_system},
                {"role": "user", "content": critic_user},
            ],
        )
        return response.choices[0].message.content.strip()


class AnthropicClient(LLMClient):
    """Anthropic Claude LLM client."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Anthropic client.

        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not found. "
                "Set ANTHROPIC_API_KEY environment variable or pass api_key parameter."
            )
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize the Anthropic client (lazy import)."""
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "anthropic package not installed. "
                "Install it with: pip install anthropic"
            )

    def generate_code(self, system_prompt: str, user_prompt: str) -> str:
        """Generate code using Claude."""
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            temperature=0.7,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text.strip()

    def generate_critic_prompt(self, error_message: str, failed_code: str) -> str:
        """Ask Claude to suggest prompt refinements."""
        critic_system = (
            "You are a ScaFi code expert and prompt engineer. "
            "Analyze compilation errors and suggest how the prompt should be refined."
        )
        critic_user = f"""
The following ScaFi code failed to compile:

```scala
{failed_code}
```

Compilation error:
```
{error_message}
```

{_CRITIC_OUTPUT_DIRECTIVE}
"""
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            temperature=0.5,
            system=critic_system,
            messages=[{"role": "user", "content": critic_user}],
        )
        return response.content[0].text.strip()


class GeminiClient(LLMClient):
    """Google Gemini LLM client (using google-genai SDK)."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.

        Args:
            api_key: Google API key. If None, auto-detects from GEMINI_API_KEY or GOOGLE_API_KEY env vars.
        """
        # If api_key is provided, set it; otherwise the SDK will auto-detect
        if api_key:
            os.environ["GEMINI_API_KEY"] = api_key
        
        # Check if API key is available (either passed or in environment)
        if not (api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
            raise ValueError(
                "Google API key not found. "
                "Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable or pass api_key parameter."
            )
        
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize the Gemini client using the new google-genai SDK."""
        try:
            from google import genai
            self.client = genai.Client()
        except ImportError:
            raise ImportError(
                "google-genai package not installed. "
                "Install it with: pip install google-genai"
            )

    def generate_code(self, system_prompt: str, user_prompt: str) -> str:
        """Generate code using Gemini with exponential backoff retry logic."""
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        max_retries = 4
        backoff = 2
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=full_prompt,
                    config={"temperature": 0.7, "max_output_tokens": 1024},
                )
                return response.text.strip()
            except Exception as e:
                error_str = str(e)
                # Check for rate limit, service unavailable, or resource exhausted errors
                if any(err_indicator in error_str for err_indicator in ["503", "429", "UNAVAILABLE", "ResourceExhausted", "DeadlineExceeded"]):
                    if attempt == max_retries - 1:
                        # Last attempt failed, re-raise the exception
                        raise e
                    sleep_time = backoff + random.uniform(0, 1)
                    print(f"⚠️  Google Gemini API rate limit/busy (attempt {attempt + 1}/{max_retries}). Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    backoff *= 2
                else:
                    # Non-retriable error, raise immediately
                    raise e

    def generate_critic_prompt(self, error_message: str, failed_code: str) -> str:
        """Ask Gemini to suggest prompt refinements with exponential backoff retry logic."""
        critic_prompt = f"""You are a ScaFi code expert and prompt engineer. 
Analyze compilation errors and suggest how the prompt should be refined.

The following ScaFi code failed to compile:

```scala
{failed_code}
```

Compilation error:
```
{error_message}
```

{_CRITIC_OUTPUT_DIRECTIVE}
"""
        
        max_retries = 4
        backoff = 2
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=critic_prompt,
                    config={"temperature": 0.5, "max_output_tokens": 512},
                )
                return response.text.strip()
            except Exception as e:
                error_str = str(e)
                # Check for rate limit, service unavailable, or resource exhausted errors
                if any(err_indicator in error_str for err_indicator in ["503", "429", "UNAVAILABLE", "ResourceExhausted", "DeadlineExceeded"]):
                    if attempt == max_retries - 1:
                        # Last attempt failed, re-raise the exception
                        raise e
                    sleep_time = backoff + random.uniform(0, 1)
                    print(f"⚠️  Google Gemini API rate limit/busy (attempt {attempt + 1}/{max_retries}). Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    backoff *= 2
                else:
                    # Non-retriable error, raise immediately
                    raise e


class OllamaClient(LLMClient):
    """Local Ollama LLM client (OpenAI-compatible API endpoint)."""

    def __init__(self, base_url: str = "http://localhost:11434/v1", model: str = "llama3.2", api_key: str = "ollama"):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama API base URL (default: http://localhost:11434/v1)
            model: Model name to use (default: llama3.2)
            api_key: API key for Ollama (any value works, default: ollama)
        """
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize the Ollama client using OpenAI SDK with custom base_url."""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError(
                "openai package not installed. "
                "Install it with: pip install openai"
            )

    def generate_code(self, system_prompt: str, user_prompt: str) -> str:
        """Generate code using local Ollama model."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.7,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {str(e)}\nMake sure Ollama is running at {self.base_url}")

    def generate_critic_prompt(self, error_message: str, failed_code: str) -> str:
        """Ask Ollama to suggest prompt refinements."""
        critic_system = (
            "You are a ScaFi code expert and prompt engineer. "
            "Analyze compilation errors and suggest how the prompt should be refined.\n\n"
            "IMPORTANT: ScaFi provides these built-in aggregate operators — they are already "
            "in scope and must NOT be redefined as helper functions or val/def declarations:\n"
            "  rep, mux, foldhood, nbr, minHoodPlus, sense\n"
            "If the error involves any of these names, instruct the prompt to use them directly "
            "as library primitives rather than defining custom wrappers or implementations.\n\n"
            "CRITICAL: The sbt compiler uses -Werror, treating any Scala warning as a fatal error. "
            "Ensure generated expressions contain no unused values, dead code, or type warnings."
        )
        critic_user = f"""
The following ScaFi code failed to compile:

```scala
{failed_code}
```

Compilation error:
```
{error_message}
```

{_CRITIC_OUTPUT_DIRECTIVE}

Remember: rep, mux, foldhood, nbr, minHoodPlus, and sense are ScaFi built-ins — never suggest defining them.
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.5,
                max_tokens=512,
                messages=[
                    {"role": "system", "content": critic_system},
                    {"role": "user", "content": critic_user},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {str(e)}\nMake sure Ollama is running at {self.base_url}")


# ============================================================================
# Data Loaders
# ============================================================================

def load_knowledge_prompt(knowledge_file_path: str = "src/main/resources/knowledge/no-knowledge.md") -> str:
    """Load the base system prompt from a knowledge file."""
    try:
        with open(knowledge_file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Knowledge file not found at {knowledge_file_path}")
        return "You are a ScaFi programmer. Generate Scala code for aggregate computing."


def load_tasks_from_json(json_file_path: str, limit: Optional[int] = None) -> list[Task]:
    """
    Load unique tasks from a JSON dataset.

    Args:
        json_file_path: Path to the JSON file.
        limit: Maximum number of unique tasks to load (None for all).

    Returns:
        List of unique Task objects.
    """
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract unique tasks by testName
    unique_tasks = {}
    for entry in data:
        test_name = entry.get("testName", "Unnamed")
        if test_name not in unique_tasks:
            unique_tasks[test_name] = Task.from_json_entry(entry)

    tasks = list(unique_tasks.values())
    if limit:
        tasks = tasks[:limit]

    return tasks


# ============================================================================
# Code Sanitizer
# ============================================================================

_PROSE_LINE_RE = re.compile(
    r'^(?:here(?:\'s| is)|note:|please |sure[,!]?|certainly[,!]?|'
    r'i(?:\'ll| will)|let me |below is|above is|the following|'
    r'this (?:code|expression|solution)|output:|result:)',
    re.IGNORECASE,
)


def clean_code_output(raw_code: str) -> str:
    """
    Strip markdown and prose from LLM output, keeping only Scala code.

    - Removes leading/trailing markdown fences (```scala, ```, etc.)
    - Filters markdown headers, bullet points, and conversational lines
    - Returns the remaining Scala expression body
    """
    text = raw_code.strip()
    if not text:
        return ""

    # Extract fenced code blocks when present; otherwise strip stray fences
    fence_blocks = re.findall(
        r"```(?:scala|java|python)?\s*\n(.*?)```",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if fence_blocks:
        text = "\n".join(block.strip() for block in fence_blocks)
    else:
        text = re.sub(r"^```(?:scala|java|python)?\s*\n?", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\n?```\s*$", "", text).strip()

    code_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            code_lines.append(line)
            continue
        if re.match(r"^#{1,6}\s", stripped):
            continue
        if re.match(r"^[-*•]\s", stripped):
            continue
        if re.match(r"^\d+\.\s+[A-Za-z]", stripped):
            continue
        if _PROSE_LINE_RE.match(stripped):
            continue
        # Skip plain English sentences with no Scala/code syntax
        if (
            re.search(r"[a-zA-Z]{4,}", stripped)
            and not re.search(r"[{}();=\[\]]|(?:^|\s)(?:val|def|var|if|else|mux|rep|nbr|foldhood|sense|import)\b", stripped)
            and stripped.endswith(".")
        ):
            continue
        code_lines.append(line)

    # Trim leading/trailing blank lines
    while code_lines and not code_lines[0].strip():
        code_lines.pop(0)
    while code_lines and not code_lines[-1].strip():
        code_lines.pop()

    return "\n".join(code_lines).strip()


# ============================================================================
# Optimization Loop
# ============================================================================

class PromptOptimizer:
    """Orchestrates the prompt optimization process."""

    def __init__(self, llm_client: LLMClient, verbose: bool = True):
        """
        Initialize the optimizer.

        Args:
            llm_client: LLM client to use for code generation and criticism.
            verbose: Whether to print intermediate steps.
        """
        self.llm_client = llm_client
        self.verbose = verbose
        self.results: list[OptimizationResult] = []

    def _log(self, message: str):
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(message)

    def optimize_task(
        self,
        task: Task,
        system_prompt: str,
        max_iterations: int = 3,
        verbose_compilation: bool = False,
    ) -> OptimizationResult:
        """
        Run the optimization loop for a single task.

        Args:
            task: The task to optimize for.
            system_prompt: Base system prompt for code generation.
            max_iterations: Maximum refinement iterations.
            verbose_compilation: Whether to pass verbose flag to compile_scafi_code.

        Returns:
            Final OptimizationResult object.
        """
        self._log(f"\n{'='*80}")
        self._log(f"Task: {task.description}")
        self._log(f"{'='*80}")

        current_system_prompt = system_prompt
        generated_code = None
        compilation_error = None
        result = None

        for iteration in range(max_iterations):
            self._log(f"\n[Iteration {iteration + 1}/{max_iterations}]")
            self._log(f"System Prompt ({len(current_system_prompt)} chars)")

            # Step 1: Generate code
            self._log("\n→ Generating code with LLM...")
            try:
                # Enhance system prompt with strict code-only instruction
                code_only_system_prompt = (
                    f"{current_system_prompt}\n\n"
                    "You are a pure Scala 3 compiler target generator for the ScaFi aggregate programming library.\n"
                    "Your output must contain ONLY the valid Scala expression/program body.\n\n"
                    "CRITICAL RULES:\n"
                    "1. Do NOT output markdown ticks or conversational text under any circumstances.\n"
                    "2. Do NOT write conversational filler, explanations, or comments.\n"
                    "3. Start directly with the ScaFi code/expression.\n"
                    "4. Keep indentation perfectly aligned (4 spaces) relative to the template.\n"
                    "5. Branch types in `mux` must match exactly (e.g., use `0.0` instead of `0` when the alternative branch returns a Double).\n"
                    "CRITICAL: Always write full, complete variable names in the final line (e.g., write `isChannel` completely, never cut off identifiers).\n"
                    "CRITICAL: Do NOT wrap output in markdown fences or append conversational prose.\n\n"
                    f"{_CANONICAL_SCAFI_EXAMPLES}"
                )
                user_prompt = f"Write ScaFi code for: {task.description}"
                generated_code = self.llm_client.generate_code(
                    code_only_system_prompt, user_prompt
                )
                generated_code = clean_code_output(generated_code)
                self._log(f"✓ Generated {len(generated_code)} chars of code")
                self._log(f"Code preview:\n{generated_code[:200]}...\n")
            except Exception as e:
                self._log(f"✗ Code generation failed: {str(e)}")
                continue

            # Step 2: Compile code
            self._log("→ Compiling code...")
            success, output = compile_scafi_code(generated_code, verbose=verbose_compilation)

            if success:
                self._log("✓ Compilation SUCCESSFUL!")
                result = OptimizationResult(
                    task=task,
                    generated_code=generated_code,
                    compilation_success=True,
                    compilation_error=None,
                    system_prompt=current_system_prompt,
                    iteration=iteration + 1,
                )
                self.results.append(result)
                return result

            else:
                compilation_error = output
                self._log(f"✗ Compilation FAILED")
                self._log(f"Error:\n{compilation_error[:300]}...\n")

                # Step 3: If final iteration, don't refine
                if iteration == max_iterations - 1:
                    self._log(f"\n[Final Iteration] Reached max iterations.")
                    result = OptimizationResult(
                        task=task,
                        generated_code=generated_code,
                        compilation_success=False,
                        compilation_error=compilation_error,
                        system_prompt=current_system_prompt,
                        iteration=iteration + 1,
                    )
                    self.results.append(result)
                    return result

                # Step 4: Use critic LLM to refine prompt
                self._log("→ Running critic LLM to suggest prompt refinements...")
                try:
                    critic_suggestions = self.llm_client.generate_critic_prompt(
                        compilation_error, generated_code
                    )
                    self._log(f"Critic suggestions:\n{critic_suggestions}\n")

                    # Refine the system prompt (simple approach: append critic suggestions)
                    current_system_prompt = (
                        f"{system_prompt}\n\n"
                        f"[ITERATION {iteration + 1} FEEDBACK]\n"
                        f"{critic_suggestions}"
                    )
                    self._log("→ Refined system prompt for next iteration\n")

                except Exception as e:
                    self._log(f"✗ Critic LLM failed: {str(e)}")
                    self._log("→ Retrying with original prompt...\n")
                    current_system_prompt = system_prompt

        # Fallback result (e.g. all code-generation attempts failed)
        fallback = result or OptimizationResult(
            task=task,
            generated_code=generated_code or "",
            compilation_success=False,
            compilation_error=compilation_error or "Unknown error",
            system_prompt=current_system_prompt,
            iteration=max_iterations,
        )
        if result is None:
            self.results.append(fallback)
        return fallback

    def optimize_batch(
        self,
        tasks: list[Task],
        system_prompt: str,
        max_iterations: int = 3,
    ) -> list[OptimizationResult]:
        """
        Run optimization for a batch of tasks.

        Args:
            tasks: List of tasks to optimize.
            system_prompt: Base system prompt.
            max_iterations: Max iterations per task.

        Returns:
            List of OptimizationResult objects.
        """
        self.results = []
        for task in tasks:
            self.optimize_task(task, system_prompt, max_iterations)

        return self.results

    def print_summary(self):
        """Print a summary of all optimization results."""
        if not self.results:
            print("No results to summarize.")
            return

        self._log(f"\n{'='*80}")
        self._log("OPTIMIZATION SUMMARY")
        self._log(f"{'='*80}")

        successful = sum(1 for r in self.results if r.compilation_success)
        total = len(self.results)

        self._log(f"Success Rate: {successful}/{total} ({100*successful//total}%)\n")

        for i, result in enumerate(self.results, 1):
            status = "✓ SUCCESS" if result.compilation_success else "✗ FAILED"
            self._log(f"[{i}] {status} - {result.task.description} (Iteration {result.iteration})")

        self._log(f"\n{'='*80}\n")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Example usage of the prompt optimizer."""
    print("ScaFi Prompt Optimization Loop - Phase 3\n")

    # Step 1: Configuration
    print("Step 1: Configuring LLM client...")
    print("  Available LLM options:")
    print("  - Local Ollama (http://localhost:11434/v1)")
    print("  - Anthropic Claude (set ANTHROPIC_API_KEY)")
    print("  - OpenAI (set OPENAI_API_KEY)")
    print("  - Google Gemini (set GOOGLE_API_KEY)")

    # Choose LLM (try Ollama first, then others)
    llm_client = None
    
    # Try local Ollama first (always available if running)
    try:
        llm_client = OllamaClient(
            base_url="http://localhost:11434/v1",
            model="llama3.2",
            api_key="ollama"
        )
        print(f"✓ Using OllamaClient (llama3.2)\n")
    except Exception as e:
        print(f"  Info: OllamaClient not available: {e}\n")
        
        # Fall back to other providers
        for ClientClass, env_var in [
            (AnthropicClient, "ANTHROPIC_API_KEY"),
            (OpenAIClient, "OPENAI_API_KEY"),
            (GeminiClient, "GOOGLE_API_KEY"),
        ]:
            if os.getenv(env_var):
                try:
                    llm_client = ClientClass()
                    print(f"✓ Using {ClientClass.__name__}\n")
                    break
                except Exception as e:
                    print(f"  Warning: {ClientClass.__name__} initialization failed: {e}\n")

    if not llm_client:
        print("✗ No LLM client available. Please:")
        print("  - Start Ollama with: ollama serve")
        print("  - Or set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY")
        return

    # Step 2: Load tasks
    print("Step 2: Loading tasks from dataset...")
    dataset_path = "data/generated/no-knowledge.json"
    if not Path(dataset_path).exists():
        print(f"✗ Dataset not found at {dataset_path}")
        return

    tasks = load_tasks_from_json(dataset_path, limit=3)
    print(f"✓ Loaded {len(tasks)} unique tasks\n")

    # Step 3: Load base system prompt
    print("Step 3: Loading base system prompt...")
    knowledge_path = "src/main/resources/knowledge/no-knowledge.md"
    system_prompt = load_knowledge_prompt(knowledge_path)
    print(f"✓ Loaded {len(system_prompt)} chars of system prompt\n")

    # Step 4: Run optimization loop
    print("Step 4: Running optimization loop...\n")
    optimizer = PromptOptimizer(llm_client, verbose=True)
    results = optimizer.optimize_batch(tasks, system_prompt, max_iterations=2)

    # Step 5: Print summary
    optimizer.print_summary()

    # Step 6: Show sample result
    if results:
        successful_result = next((r for r in results if r.compilation_success), None)
        if successful_result:
            print(f"\nExample successful code generation:")
            print(f"Task: {successful_result.task.description}")
            print(f"Generated code:\n{successful_result.generated_code}\n")
        else:
            failed_result = results[0]
            print(f"\nExample failed code generation:")
            print(f"Task: {failed_result.task.description}")
            print(f"Generated code:\n{failed_result.generated_code}")
            print(f"Error:\n{failed_result.compilation_error}\n")


if __name__ == "__main__":
    main()
