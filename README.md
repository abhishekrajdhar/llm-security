# 🛡️ LLM Safety Evaluator

A robust, full-stack platform built with Streamlit to automatically evaluate the safety, alignment, and adversarial resilience of Large Language Models (LLMs). This project sends categorized adversarial prompts to a specified LLM API and visualizes its safety score based on how well the model resists generating harmful or illicit content.

## Features

- **Multi-Model Support**: Assess any model accessible via OpenAI-compatible endpoints or Google's native Gemini (`v1beta`) endpoints.
- **Categorized Adversarial Dataset**: Includes 140+ pre-configured adversarial prompts designed to test the model across 7 distinct risk vectors.
- **Automated Response Evaluation**: Utilizes a heuristic response evaluation system to classify outputs as `SAFE`, `PARTIALLY SAFE`, or `UNSAFE`.
- **Dynamic Scoring Engine**: Automatically generates a numeric score (0-100) and letter grade (A-F) based on model resilience.
- **Actionable Security Recommendations**: Analyzes category weaknesses and provides insights on how to improve the safety training of your LLM.
- **Interactive Visual Dashboard**: High-quality Plotly graphics including category breakdown bars and distribution charts.
- **Deep Inspection Interface**: Inspect specific prompts, the generated output, and latency metrics directly in the UI.

## Tested Risk Categories

1. **Bias and Discrimination**
2. **Violence and Abuse**
3. **Sexual Misconduct**
4. **Jailbreak Attempts**
5. **Illegal Activity**
6. **Misinformation**
7. **Sensitive Data Requests**

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.12 or newer.
- An API Key for the model you want to test (e.g., OpenAI, Google Gemini, or a custom local proxy).

### Installation

1. **Clone the repository and enter the directory**:
   ```bash
   cd llm_safety_evaluator
   ```

2. **Create a virtual environment (Recommended)**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Dashboard

Start the Streamlit server to access the GUI:
```bash
streamlit run app.py
```
*The dashboard will become available locally at `http://localhost:8501` (or the next available port).*

---

## 🛠️ Usage

1. Open the **Configuration Sidebar** on the left.
2. Select your **API Format** (`openai` or `gemini`).
3. Enter the target model's **API Key**. 
   - *Note: Your key is not stored anywhere; it is directly injected into the async requests.*
4. Adjust the **Prompts per category** slider if you wish to run a shorter or more exhaustive test.
5. Click **Run Safety Evaluation**.
6. Navigate through the **Dashboard Overview**, **Vulnerability Report**, and **Deep Inspection** tabs to explore the results.

---

## 📂 Architecture & Project Structure

```text
llm_safety_evaluator/
├── app.py                            # Main Streamlit application and layout logic
├── requirements.txt                  # Python dependencies
├── datasets/
│   └── safety_prompts.json           # 140+ structured adversarial test prompts
├── engine/
│   └── model_client.py               # Asynchronous HTTP handler for AI requests
├── evaluation/
│   ├── response_evaluator.py         # Rule-based heuristics for Safe/Unsafe 
│   └── scoring_engine.py             # Translates classifications into grades/scores
├── analysis/
│   └── report_generator.py           # Logic for identifying actionable advice
└── visualization/
    └── dashboard.py                  # Plotly visualizations and Streamlit components
└── utils/
    ├── config.py                     # App settings, timeouts, and grading scales
    └── logger.py                     # Centralized logging utilities
```

---

## Future Extensibility
This platform natively supports swapping out the rule-based heuristic evaluator (`response_evaluator.py`) with an LLM-as-a-Judge system by leveraging the asynchronous API client methods.

## Contributing
We welcome updates to the `datasets/safety_prompts.json` file to keep the model challenge vectors continuously updated against the latest jailbreak strategies.
