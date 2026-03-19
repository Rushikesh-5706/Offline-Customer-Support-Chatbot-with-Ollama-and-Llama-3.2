# Offline Customer Support Chatbot with Ollama and Llama 3.2

This project demonstrates how to run an e-commerce customer support chatbot entirely on local hardware using Ollama and the Llama 3.2 3B model. It compares zero-shot and one-shot prompting strategies across 20 realistic customer queries and records the results in a structured evaluation file.

## Project Overview

E-commerce companies collect a significant amount of personal data through their customer support channels. A customer asking about an order status pastes their order number. A customer disputing a charge includes transaction details. Over a support queue of any meaningful size, routing all of that through a third-party API creates both regulatory exposure and a dependency on external availability. GDPR and similar privacy regulations introduce real liability, and the cost of cloud inference at scale is not trivial.

Running a language model locally with Ollama sidesteps both problems. The model weights live on your server, inference happens within your network perimeter, and no customer data ever leaves the machine. The trade-off is raw capability: a 3B parameter model is not competitive with GPT-4 or Claude on complex reasoning tasks. For a constrained customer support domain, however, the question is whether it is good enough — not whether it is the best possible option.

This project tests that question concretely. It runs 20 queries drawn from adapted Ubuntu Dialogue Corpus scenarios through two prompt configurations and scores the outputs on Relevance, Coherence, and Helpfulness. The results and analysis are in `eval/results.md` and `report.md`.

## Architecture

```
+-----------------------+
|                       |
|   chatbot.py          |
| (Your Python Script)  |
|                       |
+-----------+-----------+
            | 1. Format prompt with query
            | 2. Construct JSON payload
            v
+-----------------------+
|   HTTP POST Request   |
| to http://localhost...|
+-----------+-----------+
            |
            v
+-----------------------+
|                       |
|   Ollama Server       |
| (Running Locally)     |
|                       |
+-----------+-----------+
            | 3. Pass prompt to model
            v
+-----------------------+
|                       |
|   Llama 3.2 Model     |
|   (Inference)         |
|                       |
+-----------+-----------+
            | 4. Generate response text
            v
+-----------------------+
|                       |
|   Ollama Server       |
|                       |
|                       |
+-----------+-----------+
            | 5. Package response in JSON
            v
+-----------------------+
|   HTTP 200 OK Response|
| with generated text   |
+-----------+-----------+
            | 6. Parse JSON
            | 7. Log response
            v
+-----------------------+
|                       |
|   eval/results.md     |
| (Output Log File)     |
|                       |
+-----------------------+
```

## Repository Structure

```
.
├── chatbot.py                   # Main script: runs all 20 queries, writes results
├── data_prep.py                 # Demonstrates Ubuntu Corpus loading and adaptation
├── README.md                    # This file
├── setup.md                     # Step-by-step installation and execution guide
├── report.md                    # Quantitative and qualitative analysis report
├── requirements.txt             # Python dependencies (requests, datasets)
├── .gitignore                   # Standard Python gitignore
├── prompts/
│   ├── zero_shot_template.txt   # System persona + query placeholder, no example
│   └── one_shot_template.txt    # System persona + worked example + query placeholder
└── eval/
    └── results.md               # Pre-populated 40-row evaluation table with scores
```

## Key Concepts

### What Ollama is and why it was chosen

Ollama is a tool for running open-weight language models locally via a simple HTTP API. It handles model quantization, hardware detection, and serving behind a lightweight server that mimics the interface pattern of cloud LLM APIs. It was chosen because it removes all setup friction for local inference — there is no CUDA configuration required, no manual weight loading, and the API contract is clean enough to use with a minimal requests-based client.

### What Llama 3.2 3B is and its constraints

Llama 3.2 is Meta's family of small language models released in late 2024, designed for edge and on-device deployment. The 3B variant uses approximately 2 GB of disk space when quantized and can run on CPU-only hardware, making it accessible without specialized compute. The constraint is quality: at 3 billion parameters it lacks the domain depth and instruction-following precision of larger models, which is one reason this evaluation exists — to quantify exactly where it falls short.

### Zero-shot prompting: definition and when it works

Zero-shot prompting sends the model a task description and the input with no examples of what a correct output looks like. It relies entirely on the model's pre-trained knowledge and instruction-following capability. Zero-shot works well for queries that have obvious, procedural answers — resetting a password, cancelling an order — where the model's general knowledge is sufficient to produce a useful response without behavioral calibration.

### One-shot prompting: definition and when it shows value

One-shot prompting adds a single demonstration — one example input paired with an ideal output — before the actual query. The model uses that example to infer the expected format, level of specificity, and tone. One-shot outperforms zero-shot most noticeably on queries where the zero-shot response is structurally correct but too vague to be actionable. Providing one example of a well-structured response appears to shift the model's output distribution toward that structure even when the query is substantively different from the example.

## Dataset

The Ubuntu Dialogue Corpus is a large collection of multi-turn conversations scraped from Ubuntu IRC channels. It was originally designed to train and evaluate dialogue systems, and contains roughly 930,000 conversations covering a wide range of technical topics. The corpus was used here not for its content but for its structure: conversations involving a frustrated user, a knowledgeable agent, and a concrete problem to solve. Those structural properties transfer directly to customer support.

Two adaptation examples: "I cannot connect to the internet after upgrading the kernel, my driver is not loading" becomes "How do I track the shipping status of my recent order?" — both involve a user trying to get a system to tell them where something is. "I ran apt-get install and it failed with a dependency conflict" becomes "My discount code is not working at checkout" — both are cases where an expected operation silently fails with no clear reason given to the user.

## Findings Summary

| Metric | Zero-Shot Average | One-Shot Average |
|--------|------------------|-----------------|
| Relevance | 4.55 | 3.50 |
| Coherence | 4.60 | 3.95 |
| Helpfulness | 3.80 | 3.00 |
| Overall Average | 4.32 | 3.48 |

Zero-shot outperformed one-shot across all three criteria. The widest gap is in Relevance (1.05 points), where the one-shot model consistently deflected or partially addressed queries rather than answering them directly. Coherence shows the narrowest gap (0.65 points), which makes sense: sentence-level fluency is largely unaffected by the addition of a worked example. The results suggest that the single example anchored the model too strongly to the return policy scenario, degrading its handling of queries that require a different kind of response.

## How to Run

Full instructions are in [setup.md](setup.md). For anyone who already has Ollama installed and the model pulled:

```bash
git clone https://github.com/Rushikesh-5706/Offline-Customer-Support-Chatbot-with-Ollama-and-Llama-3.2.git
cd Offline-Customer-Support-Chatbot-with-Ollama-and-Llama-3.2
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
python chatbot.py
```

Results are written to `eval/results.md` on completion. The scoring columns are left blank for manual evaluation.

## Limitations and Future Work

The central limitation of this setup is that the model has no access to ground truth. It invents plausible return windows, refund timelines, and claim procedures based on common e-commerce norms, but none of those figures are sourced from an actual policy document. A customer who acts on an incorrect policy detail has a worse outcome than if the model had simply said it did not know. Retrieval-augmented generation, where the model is fed the actual policy text at inference time, is the appropriate fix for this.

A second limitation is the absence of a real order management interface. The model directs customers to check their Order History for tracking information, which is reasonable advice in the abstract, but a production system would have the agent look up the actual tracking status and report it directly. Without API access to the underlying data, the chatbot can handle the language of customer support but not the function of it.

Slower inference on CPU hardware is a practical concern worth acknowledging. On a machine without GPU acceleration, each query takes 20 to 40 seconds, making the full 20-query evaluation run take up to 25 minutes. An upgrade to a larger model on GPU hardware would improve both speed and output quality. The architecture supports that upgrade without any changes to the chatbot code — swapping the model name in the constants is sufficient.

## License

MIT
