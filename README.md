# Automated Compiler-in-the-Loop Prompt Optimization for ScaFi

[![Scala](https://img.shields.io/badge/Scala-2.13-red.svg)](https://www.scala-lang.org/)
[![SBT](https://img.shields.io/badge/sbt-1.x-blue.svg)](https://www.scala-sbt.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![LLM](https://img.shields.io/badge/LLM-Llama_3.2_(Ollama)-orange.svg)](https://ollama.com/)

An automated, compiler-guided prompt optimization pipeline for **ScaFi** (a Scala-based Aggregate Computing DSL). This project uses a local LLM (**Llama 3.2 via Ollama**) paired with real-time Scala compilation feedback (`sbt`) to generate syntactically valid and idiomatic aggregate programming code without cloud API dependencies.

> **Project Report:** For complete methodology, pipeline architecture, and academic evaluation, please refer to [`FINAL_REPORT.md`](FINAL_REPORT.md).

---

## 📌 Executive Summary

Large Language Models (LLMs) often struggle with domain-specific languages (DSLs) like ScaFi due to limited representation in public training corpora. This pipeline addresses the issue by creating a closed feedback loop:
1. An LLM generates candidate ScaFi code.
2. An `sbt` subprocess compiles the generated code.
3. If compilation fails, isolated compiler errors (`[error]`) are passed to a Critic LLM.
4. The Critic refines the system prompt to prevent syntax, type, and idiom violations in subsequent iterations.

---

## 🏗️ Architecture Overview
ollama pull llama3.2
ollama serve
python optimize_prompts.py

📂 Repository Structure
Plaintext
scafi-prompt-optimizer/
├── optimize_prompts.py       # Main optimization loop driver
├── compile_scafi.py          # sbt subprocess interface & log parser
├── dataset/                  # Task definitions and targets
├── src/                      # ScaFi Scala source files & knowledge bases
├── FINAL_REPORT.md           # Comprehensive academic report
└── README.md                 # Project documentation

👥 Academic Context
Author: Arvin Lajani (University of Bologna)

 Prof. Mirko Viroli, Prof. Gianluca Aguzzi
