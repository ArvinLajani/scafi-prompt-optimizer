
#Automated Compiler-in-the-Loop Prompt Optimization for ScaFi Aggregate Programming

**Author:** Arvin Lajani  
**Institution:** University of Bologna  
**Email:** arvin.lajani@studio.unibo.it  
 Prof. Mirko Viroli, Prof. Gianluca Aguzzi  

---

## 📌 Executive Summary

Large Language Models (LLMs) demonstrate strong capabilities in mainstream programming languages like Python and Java, but often struggle with niche Domain-Specific Languages (DSLs) such as **ScaFi**, a Scala-based framework for aggregate computing. Due to limited representation in public training datasets, lightweight local models frequently generate code containing subtle syntax errors, type mismatches, or non-idiomatic construct invocations.

To address these limitations, this project presents an automated, **compiler-in-the-loop prompt optimization framework**. The system connects a local LLM (**Llama 3.2 via Ollama**) with real-time Scala compilation feedback provided by `sbt`. By capturing raw compiler output, isolating structural error logs, and passing feedback to a domain-constrained Critic LLM, the system dynamically refines system prompts across iterative generations. 

**Key Achievement:** The framework achieved a **100% compilation success rate (3/3 tasks)** across canonical aggregate programming primitives, operating completely offline without external cloud API dependencies.

---

## 🏗️ Architecture & Methodology

The pipeline implements an iterative, closed-loop compiler optimization cycle:

+------------------+       +-------------------+       +--------------------+
|  Task Generator  | ----> | Code Sanitizer &  | ----> |   Scala Compiler   |
|   (Llama 3.2)    |       | Extractor         |       |   (sbt subprocess) |
+------------------+       +-------------------+       +--------------------+
^                                                        |
|                  +------------------+                  | (Compilation
+----------------- |    Critic LLM    | <----------------+  Error Logs)
(Refined System   |   (Ollama Feedback)
Prompt Rules)    +------------------+

### Pipeline Components

1. **Task Generator (`optimize_prompts.py`):** Accepts natural language task descriptions and constructs prompt contexts using base system prompts and domain knowledge files.
2. **Compiler Validator (`compile_scafi.py`):** Executes an `sbt` subprocess to compile generated code snippets inside a dedicated Scala evaluation harness.
3. **Critic Refinement Engine:** Parses compilation failures to extract exact `[error]` lines, suppressing build-system noise. The Critic LLM generates concise prompt refinements appended to the prompt for subsequent iterations.

---

## ⚙️ Key Technical Refinements

### 1. Subprocess Isolation & Error Log Filtering
Standard Scala Build Tool (`sbt`) output contains extensive build resolution logs, dependency checks, and environment setup messages. Passing unmapped stdout directly to the LLM leads to context saturation and critic hallucinations. The execution interface was engineered to isolate lines starting strictly with `[error]`, ensuring the Critic LLM analyzes exact compiler diagnostics (e.g., type mismatches, missing imports, syntax errors).

### 2. Domain-Constrained Critic System Prompting
When presented with compilation errors, unconstrained LLMs tend to invent non-existent helper functions or attempt to redefine built-in ScaFi primitives (e.g., implementing custom `def rep[...]` or `def mux[...]` blocks). The Critic system prompt was strictly bound to acknowledge built-in ScaFi constructs:
* State Primitives: `rep`
* Branching: `mux`
* Neighborhood Aggregation: `foldhood`, `minHoodPlus`, `nbr`, `nbrRange`
* Sensing & Environment: `sense`, `mid`

This constraint forces the Critic to direct its suggestions toward proper Scala syntax and argument typing rather than altering core DSL abstractions.

### 3. Strict Compiler Warning Compliance (`-Werror` / `-Xfatal-warnings`)
The target Scala build environment enforces strict compilation hygiene, treating warnings as fatal errors (`-Werror`). In early testing, single-line variable definitions (e.g., `val hopCount = ...`) failed compilation due to Scala's "unused local definition" warning. To satisfy strict compiler rules, the generator prompt was updated with a mandatory output rule: every script must explicitly evaluate and return the target variable on its final line.

---

## 📊 Benchmark & Experimental Results

The framework was evaluated against three core aggregate computing benchmark tasks:

| Task Description | Core DSL Primitives Evaluated | Initial Attempt | Final Result | Iterations Required |
| :--- | :--- | :---: | :---: | :---: |
| **1. Standard Channel Creation** | `rep`, `mux`, `sense`, `minHoodPlus`, `nbrRange` | Pass | **SUCCESS (100%)** | 1 |
| **2. Obstacle-Aware Channel** | `sense("obstacle")`, `Double.PositiveInfinity`, nested `mux` | Pass | **SUCCESS (100%)** | 1 |
| **3. Hop Count Distance Field** | `rep`, `mux`, `sense`, `minHoodPlus`, `nbr` | Pass | **SUCCESS (100%)** | 1 |

**Overall Optimization Success Rate:** **3/3 (100%)**

---

## 📄 Validated ScaFi Code Generations

Below are the exact, compiled code snippets generated by the pipeline for each evaluation task:

### Task 1: Standard Channel Creation
*Task: Create a channel from the source node to the destination node.*
scala
val distanceSource = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("source")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val distanceTarget = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("destination")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val totalDistance = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("destination")) { 0.0 } { minHoodPlus(nbr(d) + nbrRange()) })
val isChannel = (distanceSource + distanceTarget) <= (totalDistance + 2.0)
isChannel

Task 2: Obstacle-Aware Channel Creation
Task: Create a channel (with obstacles) from the source node to the destination node.

Scala
val isObstacle = sense[Boolean]("obstacle")
val distanceSource = rep(Double.PositiveInfinity)(d => mux(isObstacle) { Double.PositiveInfinity } { minHoodPlus(nbr(d) + nbrRange()) })
val distanceTarget = rep(Double.PositiveInfinity)(d => mux(!isObstacle) { minHoodPlus(nbr(d) + nbrRange()) } { Double.PositiveInfinity })
val totalDistance = rep(Double.PositiveInfinity)(d => mux(isObstacle) { Double.PositiveInfinity } { mux(!isObstacle) { distanceSource } { distanceTarget } })
val isChannel = (distanceSource + distanceTarget) <= (totalDistance + 2.0) && !isObstacle
isChannel
Task 3: Hop Count Distance Field
Task: Calculate hop count distance from a source node.

Scala
val hopCount = rep(Double.PositiveInfinity)(d => mux(sense[Boolean]("source")) { 0.0 } { minHoodPlus(nbr(d) + 1.0) })
hopCount
💡 Discussion & Key Insights
Compiler Feedback vs. Static Zero-Shot: Lightweight local models (3B parameters) understand functional programming paradigms, but struggle with precise DSL syntax. Real-time compiler feedback bridges this gap effectively without requiring full parameter fine-tuning.

Automated Error Recovery: Isolating compiler stderr output allows the LLM to act as its own debugger, transforming complex compiler diagnostics into actionable prompt instructions.

Reproducibility & Cost: Running local LLM inference via Ollama combined with standard local Scala build tools creates a reproducible testing environment with zero API costs or third-party latency.


