# Setup and Execution Guide

## Prerequisites

- Python 3.9 or higher
- Git
- 4 GB of free disk space (for the Llama 3.2 model)
- An internet connection for the initial model download only

## Step 1: Install Ollama

**macOS**

The easiest route is Homebrew:

```bash
brew install ollama
```

If you prefer not to use Homebrew, download the installer directly from [https://ollama.com/download](https://ollama.com/download) and follow the on-screen instructions.

**Windows**

Download the Windows installer from [https://ollama.com/download](https://ollama.com/download) and run it. Ollama will be added to your system and start automatically.

**Linux**

Run the official install script:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

## Step 2: Pull the Llama 3.2 Model

```bash
ollama pull llama3.2:3b
```

This downloads approximately 2 GB of model weights to your local machine. It only needs to be done once. Subsequent runs use the cached version.

## Step 3: Start the Ollama Server

On macOS and Windows, Ollama starts automatically as a background process after installation. You do not need to run any additional command.

On Linux, start the server manually:

```bash
ollama serve
```

Leave this terminal window open while running the chatbot script. The server listens on `http://localhost:11434` by default.

## Step 4: Clone the Repository

```bash
git clone https://github.com/Rushikesh-5706/Offline-Customer-Support-Chatbot-with-Ollama-and-Llama-3.2.git
cd Offline-Customer-Support-Chatbot-with-Ollama-and-Llama-3.2
```

## Step 5: Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 6: Run the Chatbot

```bash
python chatbot.py
```

The script processes all 20 customer queries twice each (once with the zero-shot template and once with the one-shot template), logging progress to stdout after each response. When finished, it writes all 40 responses to `eval/results.md`. Depending on your hardware, expect roughly 20 to 40 seconds per query on a CPU-only machine, making the total run approximately 15 to 25 minutes.

## Step 7: Review Results

Open `eval/results.md` in any text editor or Markdown viewer. The file contains the scoring rubric at the top followed by the full results table. The Relevance, Coherence, and Helpfulness columns are blank and should be filled in manually based on the rubric. Once all 40 rows are scored, use the Summary Statistics section at the bottom to compile aggregate averages.

## Troubleshooting

**"Connection refused" when running chatbot.py**

Ollama is not running. On Linux, start it with `ollama serve`. On macOS or Windows, open the Ollama application from your Applications folder or Start Menu and wait for the menu bar icon to appear before retrying.

**"Model not found" error**

The Llama 3.2 model has not been downloaded yet. Run `ollama pull llama3.2:3b` and wait for the download to complete before running the chatbot script.

**Responses taking 30 or more seconds each**

This is expected behavior when running inference on a CPU without GPU acceleration. The script logs a progress message after every response so you can see it is still working. If you have a machine with an NVIDIA GPU, installing the CUDA-enabled version of Ollama will reduce inference time considerably.

## Optional: Explore the Dataset

The repository includes `data_prep.py`, which demonstrates how the Ubuntu Dialogue Corpus was loaded and adapted into the 20 e-commerce queries used in this project. Running this script requires an internet connection on the first run, as the dataset is downloaded and cached locally by the `datasets` library.

```bash
python data_prep.py
```

This script is not required for the chatbot evaluation. It is provided for transparency and reproducibility.
