"""
data_prep.py

Demonstrates loading the Ubuntu Dialogue Corpus and adapting technical
queries to an e-commerce customer support context.

This script was used to source and adapt the 20 queries used in chatbot.py.
Run once to explore the dataset. Not required for the chatbot evaluation itself.
"""

from datasets import load_dataset


ADAPTATION_EXAMPLES = [
    {
        "original": "I cannot connect to the internet after upgrading to the new kernel, my driver is not loading.",
        "adapted": "How do I track the shipping status of my recent order?",
        "logic": "Both involve a user trying to locate something that the system should surface automatically.",
    },
    {
        "original": "I ran apt-get install and it failed with a dependency conflict.",
        "adapted": "My discount code is not working at checkout.",
        "logic": "Both are cases where an expected operation fails without a clear reason given to the user.",
    },
    {
        "original": "My hard drive is showing the wrong amount of free space after I formatted a partition.",
        "adapted": "I was charged twice for the same order.",
        "logic": "Both involve a numeric discrepancy the user cannot explain.",
    },
    {
        "original": "How do I check the logs for the apache server?",
        "adapted": "I cannot find the invoice or receipt for my recent purchase.",
        "logic": "Both involve locating a stored record of a past system event.",
    },
    {
        "original": "My wifi driver is not working after the latest update.",
        "adapted": "My account password is not working and I cannot log in.",
        "logic": "Both involve a credential or connection failure that blocks the user from accessing a service.",
    },
]


def load_ubuntu_corpus() -> None:
    """
    Load the Ubuntu Dialogue Corpus v2.0 and print a sample of conversations.

    Requires an internet connection for the first run. Subsequent runs use
    the cached version stored by the datasets library.
    """
    print("Loading Ubuntu Dialogue Corpus v2.0...")
    print("This may take a few minutes on the first run.\n")

    dataset = load_dataset("rguo12/ubuntu_dialogue_corpus", "v2.0")
    train_data = dataset["train"]

    print(f"Total training conversations: {len(train_data)}")
    print(f"Available columns: {train_data.column_names}")
    print()

    print("=== Sample conversations (first 3) ===")
    for i, row in enumerate(train_data.select(range(3))):
        print(f"\n--- Conversation {i + 1} ---")
        for key, value in row.items():
            print(f"{key}: {str(value)[:200]}")

    print("\n=== Adaptation Examples ===")
    for i, example in enumerate(ADAPTATION_EXAMPLES, start=1):
        print(f"\nAdaptation {i}:")
        print(f"  Original (Ubuntu): {example['original']}")
        print(f"  Adapted (E-commerce): {example['adapted']}")
        print(f"  Reasoning: {example['logic']}")


if __name__ == "__main__":
    load_ubuntu_corpus()
