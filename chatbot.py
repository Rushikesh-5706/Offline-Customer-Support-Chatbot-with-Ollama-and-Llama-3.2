"""
chatbot.py

Offline customer support chatbot client for Chic Boutique.
Queries a local Ollama server running Llama 3.2 (3B) using both
zero-shot and one-shot prompt templates and logs results to eval/results.md.
"""

import json
import logging
import sys
import time
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OLLAMA_ENDPOINT: str = "http://localhost:11434/api/generate"
MODEL_NAME: str = "llama3.2:3b"
PROMPTS_DIR: Path = Path("prompts")
EVAL_DIR: Path = Path("eval")
RESULTS_FILE: Path = EVAL_DIR / "results.md"
ZERO_SHOT_TEMPLATE_PATH: Path = PROMPTS_DIR / "zero_shot_template.txt"
ONE_SHOT_TEMPLATE_PATH: Path = PROMPTS_DIR / "one_shot_template.txt"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Customer queries
# ---------------------------------------------------------------------------

CUSTOMER_QUERIES: list[str] = [
    "How do I track the shipping status of my recent order?",
    "My discount code is not working at checkout.",
    "I want to return an item I purchased last week.",
    "My account password is not working and I cannot log in.",
    "I received the wrong item in my order. What are my options?",
    "How do I change the delivery address after placing an order?",
    "My payment was declined but the amount was deducted from my bank account.",
    "How do I cancel an order that I just placed?",
    "The item I received is damaged. What should I do?",
    "I placed an order two weeks ago and it still has not arrived.",
    "How do I update my email address on my account?",
    "Can I exchange an item for a different size instead of returning it?",
    "I was charged twice for the same order.",
    "How do I apply a gift card balance to my purchase?",
    "My order status shows as delivered but I never received the package.",
    "How do I unsubscribe from your promotional emails?",
    "I cannot find the invoice or receipt for my recent purchase.",
    "How do I permanently delete my account from your platform?",
    "Is it possible to change the quantity of an item in my existing order?",
    "I forgot to apply my loyalty points during checkout. Can the discount still be applied?",
]

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


def load_template(path: Path) -> str:
    """
    Load a prompt template from the given file path.

    Raises FileNotFoundError with a clear message if the file is missing.
    Returns the template string with leading/trailing whitespace stripped.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Template file not found: {path}. "
            "Ensure the 'prompts/' directory exists and contains the required files."
        )
    return path.read_text(encoding="utf-8").strip()


def format_prompt(template: str, query: str) -> str:
    """
    Replace the {query} placeholder in the template with the actual customer query.

    Returns the formatted prompt string.
    """
    return template.replace("{query}", query)


def query_ollama(prompt: str, retries: int = 2, timeout: int = 120) -> str:
    """
    Send a prompt to the local Ollama API and return the generated response text.

    Parameters
    ----------
    prompt : str
        The full formatted prompt string.
    retries : int
        Number of retry attempts on failure (default: 2).
    timeout : int
        Request timeout in seconds (default: 120).

    Returns
    -------
    str
        The model's response as a stripped string, or an explicit error message
        string if all attempts fail.

    Handles
    -------
    - requests.exceptions.ConnectionError  : Ollama server not running.
    - requests.exceptions.Timeout          : Request took too long.
    - requests.exceptions.HTTPError        : Non-200 status codes.
    - json.JSONDecodeError                 : Malformed response body.
    - KeyError                             : Missing 'response' key in parsed JSON.
    """
    payload: dict = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
    }

    for attempt in range(1, retries + 2):
        try:
            response = requests.post(
                OLLAMA_ENDPOINT,
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            data: dict = response.json()
            return data["response"].strip()

        except requests.exceptions.ConnectionError:
            print(
                "Ollama server is not reachable at http://localhost:11434. "
                "Ensure Ollama is installed and running before executing this script."
            )
            return "[ERROR] Ollama server is not reachable."

        except requests.exceptions.Timeout:
            logger.warning(
                "Request timed out (attempt %d of %d).", attempt, retries + 1
            )
            if attempt == retries + 1:
                return "[ERROR] Request timed out after all retry attempts."

        except requests.exceptions.HTTPError as exc:
            logger.warning(
                "HTTP error on attempt %d: %s", attempt, exc
            )
            if attempt == retries + 1:
                return f"[ERROR] HTTP error: {exc}"

        except json.JSONDecodeError:
            logger.warning(
                "Failed to parse JSON response on attempt %d.", attempt
            )
            if attempt == retries + 1:
                return "[ERROR] Could not parse response from Ollama server."

        except KeyError:
            logger.warning(
                "'response' key missing in API response on attempt %d.", attempt
            )
            if attempt == retries + 1:
                return "[ERROR] Unexpected response structure from Ollama server."

        # Brief pause before retrying
        if attempt <= retries:
            time.sleep(2)

    return "[ERROR] All retry attempts failed."


def check_ollama_health() -> bool:
    """
    Perform a lightweight health check against http://localhost:11434 before
    processing queries.

    Returns True if the server responds with any HTTP reply, False otherwise.
    Prints a clear status message either way.
    """
    try:
        response = requests.get("http://localhost:11434", timeout=5)
        # Any HTTP response (even 404) means the server is alive.
        logger.info("Ollama server is reachable (HTTP %d).", response.status_code)
        return True
    except requests.exceptions.ConnectionError:
        logger.error(
            "Ollama server is not reachable at http://localhost:11434. "
            "Start Ollama before running this script."
        )
        return False
    except requests.exceptions.Timeout:
        logger.error(
            "Health check timed out. Ollama may be starting up; try again in a moment."
        )
        return False


def escape_markdown_pipe(text: str) -> str:
    """
    Escape pipe characters in a string so it renders correctly inside a
    Markdown table cell.

    Replaces '|' with '\\|' and newlines with a single space.
    """
    text = text.replace("|", "\\|")
    text = text.replace("\n", " ")
    return text


def write_results_header(file_handle) -> None:
    """
    Write the scoring rubric and the Markdown table header to the results file.

    The rubric defines three criteria on a 1–5 scale:
    - Relevance
    - Coherence
    - Helpfulness

    The table columns are:
    Query # | Customer Query | Prompting Method | Response |
    Relevance (1-5) | Coherence (1-5) | Helpfulness (1-5)
    """
    rubric = (
        "# Evaluation Results — Chic Boutique Customer Support Chatbot\n\n"
        "## Scoring Rubric\n\n"
        "**Relevance (1-5):** Measures how directly the response addresses the specific "
        "question asked. A score of 1 means the response is unrelated or off-topic. "
        "A score of 5 means the response targets exactly what the customer asked "
        "with no unnecessary detours.\n\n"
        "**Coherence (1-5):** Measures grammatical correctness, sentence structure, "
        "and overall readability. A score of 1 indicates the response is fragmented "
        "or confusing. A score of 5 indicates the response reads naturally and is "
        "immediately understandable.\n\n"
        "**Helpfulness (1-5):** Measures whether the response gives the customer "
        "something actionable or informative. A score of 1 means the response leaves "
        "the customer no better off. A score of 5 means the response provides concrete "
        "next steps or complete information.\n\n"
        "---\n\n"
        "## Results Table\n\n"
    )

    header = (
        "| Query # | Customer Query | Prompting Method | Response "
        "| Relevance (1-5) | Coherence (1-5) | Helpfulness (1-5) |\n"
        "|---------|---------------|-----------------|----------"
        "|----------------|----------------|----------------|\n"
    )

    file_handle.write(rubric)
    file_handle.write(header)


def write_result_row(
    file_handle,
    query_num: int,
    query: str,
    method: str,
    response: str,
    relevance: str = "",
    coherence: str = "",
    helpfulness: str = "",
) -> None:
    """
    Write a single row to the Markdown results table.

    All text fields are passed through escape_markdown_pipe before writing
    to prevent pipe characters from breaking the table structure.
    """
    safe_query = escape_markdown_pipe(query)
    safe_response = escape_markdown_pipe(response)
    safe_method = escape_markdown_pipe(method)

    line = (
        f"| {query_num} | {safe_query} | {safe_method} | {safe_response} "
        f"| {relevance} | {coherence} | {helpfulness} |\n"
    )
    file_handle.write(line)


def main() -> None:
    """
    Main execution function.

    Flow
    ----
    1. Check Ollama health. Exit with code 1 and a clear message if unreachable.
    2. Load zero-shot and one-shot templates from the prompts/ directory.
    3. Ensure eval/ directory exists. Create it if not.
    4. Open eval/results.md in write mode.
    5. Write the rubric and table header.
    6. For each of the 20 queries:
       a. Format zero-shot prompt and call query_ollama(). Log progress.
       b. Format one-shot prompt and call query_ollama(). Log progress.
       c. Write both result rows to the file.
       d. Sleep 1 second between queries to avoid hammering the local server.
    7. Log completion message with the file path.
    8. Print a reminder to manually fill in the scoring columns.
    """
    # Step 1: Health check
    if not check_ollama_health():
        logger.error(
            "Cannot proceed without a running Ollama server. "
            "Start Ollama and try again."
        )
        sys.exit(1)

    # Step 2: Load templates
    zero_shot_template: str = load_template(ZERO_SHOT_TEMPLATE_PATH)
    one_shot_template: str = load_template(ONE_SHOT_TEMPLATE_PATH)
    logger.info("Prompt templates loaded successfully.")

    # Step 3: Ensure eval/ directory exists
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    total_queries: int = len(CUSTOMER_QUERIES)

    # Steps 4–7: Open file, write header, process queries
    with RESULTS_FILE.open("w", encoding="utf-8") as results_file:
        write_results_header(results_file)

        for idx, query in enumerate(CUSTOMER_QUERIES, start=1):
            logger.info(
                "Processing query %d/%d: %s", idx, total_queries, query[:60]
            )

            # Zero-shot
            zero_prompt: str = format_prompt(zero_shot_template, query)
            logger.info("  -> Sending zero-shot prompt to Ollama...")
            zero_response: str = query_ollama(zero_prompt)
            logger.info("  -> Zero-shot response received.")

            # One-shot
            one_prompt: str = format_prompt(one_shot_template, query)
            logger.info("  -> Sending one-shot prompt to Ollama...")
            one_response: str = query_ollama(one_prompt)
            logger.info("  -> One-shot response received.")

            # Write rows (scoring columns left blank for manual completion)
            write_result_row(
                results_file, idx, query, "Zero-Shot", zero_response
            )
            write_result_row(
                results_file, idx, query, "One-Shot", one_response
            )

            # Flush to disk after each query pair so partial results are saved
            results_file.flush()

            if idx < total_queries:
                time.sleep(1)

    # Step 7: Completion log
    logger.info("Evaluation complete. Results written to: %s", RESULTS_FILE)

    # Step 8: Manual scoring reminder
    print(
        "\nResults saved to eval/results.md.\n"
        "Please open that file and fill in the Relevance, Coherence, and Helpfulness "
        "scores for each row using the rubric at the top of the file."
    )


if __name__ == "__main__":
    main()
