# Evaluation Report — Offline Customer Support Chatbot

## 1. Introduction

This project tested whether a locally deployed language model could handle common e-commerce customer support queries at a quality level that would be useful in a real production setting. The setup used Ollama to run Llama 3.2 at the 3B parameter scale entirely on local hardware, with no API calls to any cloud provider. The central question was whether the model's general language understanding is sufficient for a constrained support domain, and whether structured prompting changes output quality in a predictable direction.

Data privacy is a real concern in e-commerce. Customer support conversations frequently contain order numbers, email addresses, partial payment details, and delivery addresses. Routing that data through a third-party API introduces regulatory risk, particularly under GDPR and similar privacy frameworks. A self-hosted inference setup eliminates that exposure entirely, at the cost of some latency and a reduction in raw capability compared to frontier models. This project is a concrete proof-of-concept for that trade-off.

The two prompting strategies compared are zero-shot and one-shot. Zero-shot sends the model a system persona and the customer's query with nothing else. One-shot adds a single worked example of an ideal response before the actual query. The hypothesis going in was that one-shot prompting would improve specificity and structure — a widely held assumption supported by the academic literature. What the actual results showed was more complicated.

## 2. Methodology

### 2.1 Dataset Adaptation

The Ubuntu Dialogue Corpus is a large dataset of multi-turn conversations from Ubuntu IRC channels. The conversations are overwhelmingly technical: users debugging kernel modules, troubleshooting network drivers, asking about package manager conflicts. That content is not directly usable for customer support, but the structural qualities transfer well — a frustrated user, a knowledgeable agent, a concrete problem, and the need for a clear next step.

The adaptation mapped the class of technical problem to an analogous e-commerce frustration. Three concrete examples:

- Ubuntu original: "I cannot connect to the internet after upgrading to the new kernel, my driver is not loading." becomes "How do I track the shipping status of my recent order?" Both involve a user trying to locate something that should be visible to the system.
- Ubuntu original: "I ran apt-get install and it failed with a dependency conflict." becomes "My discount code is not working at checkout." Both are cases where an expected operation fails without a clear reason given to the user.
- Ubuntu original: "My hard drive is showing the wrong amount of free space after I formatted a partition." becomes "I was charged twice for the same order." Both involve a numeric discrepancy the user cannot explain.

The 20 queries used in this evaluation represent a realistic cross-section of what a mid-size e-commerce support inbox looks like on any given day.

### 2.2 Prompt Design

The zero-shot template establishes a persona for the model: a helpful, concise support agent for a store called Chic Boutique. It names the relevant topics (orders, returns, payments, account management) and includes two guardrails: an instruction to admit uncertainty rather than fabricate details, and an 80-word response cap. The word count constraint is important because unconstrained language models tend to hedge and pad responses in ways that frustrate customers reading quickly.

The one-shot template uses the same system persona and adds a single worked example before the actual query. The example chosen is a return policy question paired with an ideal structured response. It was selected because it is unambiguous, common, and has a clear correct format — specific time window, specific process, specific outcome. The intent was to give the model a behavioral reference that would push responses toward specificity and away from vague deflection.

### 2.3 Evaluation Rubric

Three criteria were scored on a 1 to 5 integer scale: Relevance, Coherence, and Helpfulness. Relevance measures whether the response addresses the question actually asked. Coherence measures grammar and readability. Helpfulness is the most practically meaningful criterion: it asks whether the customer comes away with something actionable.

A 1 to 5 manual scoring scale was chosen over automated metrics like BLEU or ROUGE because those metrics require reference responses and correlate poorly with human judgment for open-ended generation. Manual scoring is slower but produces a more honest signal at this evaluation scale, and it forces the reviewer to actually read every response rather than letting a script aggregate numbers.

### 2.4 Execution Environment

All inference ran on local hardware using Ollama with the `llama3.2:3b` model. No queries, prompts, or responses were transmitted to any external server at any point during the experiment. The Ollama server exposes a local HTTP API at port 11434, and `chatbot.py` communicates with it exclusively over localhost. The model weights are stored locally after the initial one-time download.

## 3. Results and Analysis

### 3.1 Quantitative Summary

| Metric | Zero-Shot Average | One-Shot Average |
|--------|------------------|-----------------|
| Relevance | 4.35 | 3.50 |
| Coherence | 4.40 | 3.95 |
| Helpfulness | 3.80 | 3.00 |
| Overall Average | 4.18 | 3.48 |

The headline result contradicts the initial hypothesis: zero-shot prompting outperformed one-shot prompting across all three criteria. The overall gap of 0.70 points in favor of zero-shot is not a measurement artifact — it reflects genuine failures in the one-shot condition that do not appear in zero-shot. The most likely explanation is that the single worked example, which describes how to handle a return, anchored the model too strongly to that specific scenario. When the actual query was structurally different, the model occasionally overfit to the example pattern rather than reasoning freshly from the system prompt.

Helpfulness shows the widest gap: 3.80 for zero-shot versus 3.00 for one-shot, a difference of 0.80 points. Coherence is closest: 4.40 versus 3.95, a difference of 0.45. This pattern is worth paying attention to. The one-shot model writes grammatically coherent sentences — it has not lost the ability to construct readable prose — but its responses are less useful because they sometimes give wrong information or deflect in ways the zero-shot model does not. Coherence measures fluency; Helpfulness measures function. The one-shot condition degraded function more than fluency.

### 3.2 Qualitative Observations

The most striking failure is query 8: "How do I cancel an order that I just placed?" The one-shot response states flatly that the store does not offer order cancellations. This is incorrect — the zero-shot model correctly explains that cancellation is possible before dispatch. The one-shot model appears to have pattern-matched the concept of "we cannot accommodate" from the return example and applied it in a context where it does not belong. The result is a response that would actively mislead a customer and erode trust in the store.

Query 16 shows a similar failure mode. The zero-shot model correctly identifies the unsubscribe link at the bottom of every promotional email — this is standard industry practice and the model recalls it accurately. The one-shot response begins by restating the customer's question verbatim (a formatting artifact from the example template) and then says it does not have up-to-date information on the unsubscription process. The zero-shot model got this completely right; the one-shot model produced something worse than useless.

Queries where both methods performed comparably include query 4 (password reset), query 11 (update email address), and query 20 (loyalty points at checkout). These are procedural queries with clear, conventional answers. For straightforward questions where the model's general knowledge is sufficient, the prompting method matters much less. The one-shot model's structural example does not add anything for queries the model already handles confidently, and in some cases introduces noise.

Two legitimate one-shot wins were query 3 (item return) and query 4 (password reset). For the return query, the one-shot model correctly cited the 30-day window while the zero-shot model gave a more generic response. For the password reset, the one-shot model produced a slightly more structured response and scored 5/5/5 compared to 5/4/4 for zero-shot. These results suggest the one-shot approach has genuine value in narrow circumstances — specifically when the example is directly analogous to the query — but it is not a reliable general improvement at this model scale.

### 3.3 Notable Response Examples

| Scenario | Query | Zero-Shot (excerpt) | One-Shot (excerpt) |
|----------|-------|--------------------|--------------------|
| One-shot catastrophic failure | Q8: Cancel an order | "We'll be happy to assist you with cancellation... if your order is still in the processing stage, we may be able to cancel it for you before shipping." | "I'm sorry, but we don't offer order cancellations." |
| One-shot hallucination | Q17: Invoice or receipt | "You can check your email inbox for a confirmation email... the email should include the order details and payment information." | "Our digital receipts are no longer retained due to security and environmental concerns." |
| One-shot win | Q3: Return an item | Generic return portal instructions, no timeline given. | Requests order number, cites 30-day return policy. |

Query 7 also deserves a note. Neither method handled the payment authorization hold scenario well. The zero-shot model said it "couldn't find any record of a chargeback" — an odd framing that implies access to internal systems it does not have. The one-shot model admitted ignorance and directed the customer to contact support. Both responses scored 3 on Relevance. This is a case where both templates failed to surface the conceptually correct answer (temporary authorization hold, bank will release within 3-5 days), and where RAG or a tool-use setup would make a meaningful difference.

## 4. Conclusion and Limitations

Llama 3.2 3B is usable for procedural e-commerce support queries — password resets, tracking instructions, email updates — where the model's general knowledge produces a correct answer without grounding in specific policy documents. For those queries, zero-shot prompting with a clear system persona is sufficient and performs consistently. The 4.18 overall zero-shot average is a reasonable starting point for a narrow, well-scoped support function.

The one-shot approach failed to improve on zero-shot in this experiment, and in several cases actively degraded response quality. The core problem is that a single example at 3B scale appears to anchor the model too strongly to the example's specific framing. When the actual query requires a different kind of response, the model may overapply the pattern rather than adapt to the new context. Larger models with stronger instruction-following capabilities may handle this more gracefully, but that hypothesis would need its own evaluation to confirm.

The most significant limitations shared by both methods are the absence of grounding in real policy documents and the absence of access to actual order data. The model invents plausible policy details — return windows, refund timelines, claim procedures — drawn from common retail norms, and some of those invented details will be wrong relative to actual store policy. A retrieval-augmented generation setup, where the model is provided the real policy text at inference time, is the appropriate fix for the hallucination problem. Integration with an order management API would allow the model to provide specific tracking information rather than directing customers to find it themselves. Both of those architectural additions would substantially improve the usefulness of this baseline setup without requiring a change in the underlying model.
