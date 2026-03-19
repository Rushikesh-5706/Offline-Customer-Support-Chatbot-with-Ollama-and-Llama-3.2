# Evaluation Report — Offline Customer Support Chatbot

## 1. Introduction

This project explored whether a locally deployed large language model could handle common e-commerce customer support queries at a quality level that would be useful in production. The test harness used Ollama to run Llama 3.2 at the 3B parameter scale entirely on local hardware, with no API calls to any cloud provider. The core question was whether the model's general language understanding is sufficient for a constrained support domain, and whether structured prompting meaningfully changes the output quality.

Data privacy is a genuine concern in e-commerce. Customer queries frequently contain order numbers, email addresses, partial payment details, and delivery addresses. Routing that data through an external API introduces regulatory risk, particularly under GDPR and similar frameworks. A self-hosted inference setup eliminates that exposure entirely, at the cost of latency and some reduction in raw capability relative to frontier models. This project is a proof of concept for that trade-off.

The two prompting strategies compared here are zero-shot and one-shot. Zero-shot sends the model a system persona and the customer's query, nothing else. One-shot adds a single worked example of a query and an ideal response before the actual query. The comparison is useful because one-shot prompting costs almost nothing in terms of implementation complexity, yet the literature suggests it can meaningfully improve output format and specificity. This evaluation checks whether that effect holds for practical e-commerce support queries.

## 2. Methodology

### 2.1 Dataset Adaptation

The Ubuntu Dialogue Corpus is a large dataset of multi-turn conversations from Ubuntu IRC channels. The conversations are overwhelmingly technical in nature — users debugging kernel modules, troubleshooting Wi-Fi drivers, asking about package manager conflicts. That content is not useful for customer support as-is, but the conversational structure and the range of problem types are easy to adapt.

The adaptation process mapped the class of technical problem to an analogous e-commerce frustration. Connectivity problems became order tracking questions. Permission errors became account login failures. Package installation failures became checkout discount code failures. Three concrete examples:

- Ubuntu original: "I cannot connect to the internet after upgrading to the new kernel, my driver is not loading." becomes "How do I track the shipping status of my recent order?"
- Ubuntu original: "I ran apt-get install and it failed with a dependency conflict, how do I resolve it?" becomes "My discount code is not working at checkout."
- Ubuntu original: "My hard drive is showing the wrong amount of free space after I formatted a partition." becomes "I was charged twice for the same order."

The adaptation is not a direct mechanical translation but rather a structural one. The emotional register (frustration at a system that should work), the need for a clear next step, and the background assumption that the agent knows something the user does not — those qualities transfer between domains. The 20 queries used in this evaluation represent a realistic cross-section of what a mid-size e-commerce support inbox looks like on any given day.

### 2.2 Prompt Design

The zero-shot template establishes a persona for the model: a helpful, concise support agent for a store called Chic Boutique. It names the relevant topics the agent can address (orders, returns, payments, account management) and includes two critical guardrails: an instruction to admit uncertainty rather than fabricate policy details, and a word count cap of 80 words. The word count constraint is important because unconstrained language models tend to hedge, repeat themselves, and pad responses in ways that frustrate customers.

The one-shot template uses the same system persona and adds a single worked example before the customer's actual query. The example chosen is a return policy question with an ideal structured response. It was selected because it is unambiguous, familiar, and has a clear correct format — specific time window, specific process, specific outcome. This gives the model a concrete behavioral reference point rather than relying purely on the description in the system prompt.

The hypothesis going in was that the structural example would push the model toward more specific, actionable responses, particularly for queries where the zero-shot output tends to stay vague (damaged items, wrong items, payment disputes).

### 2.3 Evaluation Rubric

Three criteria were scored on a 1 to 5 integer scale: Relevance, Coherence, and Helpfulness. Relevance measures whether the response addresses the question asked — a response that pivots to general policies when asked about a specific problem scores poorly here. Coherence measures grammar and readability. Helpfulness is the most practically meaningful criterion: it asks whether the customer comes away with something actionable.

A 1 to 5 integer scale was chosen over automated metrics like BLEU or ROUGE because those metrics require reference responses and are known to correlate poorly with human judgment for open-ended generation. Manual scoring is slower but produces a more honest signal for a 20-query evaluation set. The trade-off is acceptable at this scale.

### 2.4 Execution Environment

All inference ran on local hardware using Ollama with the `llama3.2:3b` model. No queries, prompts, or responses were transmitted to any external server at any point. The Ollama server exposes a local HTTP API at port 11434 and the chatbot.py script communicates with it over localhost. The model weights are stored locally after the initial one-time download.

## 3. Results and Analysis

### 3.1 Quantitative Summary

| Metric | Zero-Shot Average | One-Shot Average |
|--------|------------------|-----------------|
| Relevance | 4.00 | 4.95 |
| Coherence | 4.45 | 5.00 |
| Helpfulness | 3.55 | 4.75 |
| Overall Average | 4.00 | 4.90 |

The headline number is a 0.9-point improvement in overall average from zero-shot to one-shot, a roughly 22 percent gain relative to the zero-shot baseline. The improvement, however, is not uniformly distributed. Helpfulness improved by 1.20 points — the largest single-criterion gain — while Coherence improved by only 0.55 points, the smallest. This pattern makes intuitive sense. The model writes grammatically correct sentences regardless of prompting method; Coherence was already high at 4.45 in the zero-shot condition. The bottleneck was specificity, not fluency. One-shot prompting addressed specificity by providing a behavioral example, while having essentially no effect on sentence-level quality because that was not the limiting factor.

Relevance also improved substantially, from 4.00 to 4.95. The zero-shot model occasionally interpreted a query slightly too broadly and produced a response that addressed a category of problem rather than the specific problem. The one-shot example appears to calibrate the model's scope more tightly, though it is difficult to attribute this entirely to the example versus natural run-to-run variation in model output.

### 3.2 Qualitative Observations

The starkest performance gap between methods appears in query 5, 9, and 10. Query 5 asks what to do after receiving the wrong item. The zero-shot response tells the customer to contact support and that a replacement or refund can be arranged — this is technically correct but barely useful. The one-shot response specifies the 30-day window, explains the free return shipment, and offers both resolution paths explicitly. The customer reading the one-shot response has a clear path forward; the customer reading the zero-shot response has to contact support again to learn what their actual options are.

Query 9, the damaged item case, is the clearest example of a zero-shot failure in this dataset. The response — "You should contact our customer support team about this. We handle damaged item cases and can help you." — scores 2 on Helpfulness because it tells the customer to do something they already know they need to do without adding any real information. The one-shot version provides the 7-day reporting window, requests the specific evidence needed (photos), and offers both resolution paths. The structural example from the return policy question generalized well to this adjacent scenario.

Queries 1, 4, 8, and 16 show negligible difference between methods. These are procedural queries with obvious correct answers: track your order in Order History, reset your password with the forgot-password link, cancel via Order History before dispatch, unsubscribe via the footer link. The model handles these confidently regardless of prompting method, which is a reasonable result — simple procedural questions do not require behavioral calibration.

One genuine concern is that neither method grounds responses in actual policy data. The model invents plausible-sounding details: the 30-day return window, the 5 to 7 business day refund timeline, the 7-day damage reporting window. These numbers are common in e-commerce and sound correct, but they are not sourced from any real Chic Boutique policy document because no such document was provided. A customer acting on the 7-day damage claim window and finding it does not match actual policy would have a worse experience than if the model had simply said it did not know the exact window.

### 3.3 Notable Response Examples

| Scenario | Query | Zero-Shot Response (excerpt) | One-Shot Response (excerpt) |
|----------|-------|-----------------------------|-----------------------------|
| Zero-shot underperformed | Q9: Item received is damaged | "You should contact our customer support team about this." | "Please contact us within 7 days with your order number and photos of the damage. We will arrange a free return and send a replacement or issue a full refund." |
| One-shot ideal response | Q5: Wrong item received | "Contact customer support. We can arrange a replacement or a refund for you." | "We apologize for sending the wrong item. Contact us within 30 days with your order number and a photo of what you received. We will arrange free return shipping and send the correct item or issue a full refund." |
| Surprising result | Q7: Payment declined but charged | "This sometimes happens when a payment authorization is placed..." | Similar quality to zero-shot; zero-shot scored 4,5,4 vs one-shot 5,5,5 |

Query 7 was the mild surprise. The zero-shot response to the payment hold question was clearer and more informative than expected. The model correctly identified the authorization hold mechanism without being prompted to do so, suggesting it has internalized enough knowledge about payment processing to handle this query reasonably well unprompted. The one-shot version was slightly more structured and scored a perfect 5 on Relevance, but the gap was narrower than anticipated.

## 4. Conclusion and Limitations

Llama 3.2 3B is a viable starting point for general-purpose e-commerce support queries when paired with one-shot prompting. For high-volume, domain-restricted use cases — standard questions about returns, shipping, password resets, and cancellations — the one-shot model produces responses that are coherent and largely on-target. The 4.90 overall average with one-shot prompting is high enough to warrant further investment. That said, "viable starting point" means exactly that and not more.

The most significant limitation is the absence of grounding. The model does not know Chic Boutique's actual return window, the actual refund timeline, or the actual damage claim process. It generates plausible defaults drawn from common retail norms, and those defaults may be wrong. In a real deployment this is a patient safety equivalent — telling a customer the wrong return window is not dangerous, but it erodes trust and creates downstream support load. Retrieval-augmented generation, where the model is provided policy documents at inference time, is the appropriate solution. The model's language ability is sufficient; the problem is that it is making things up to fill in the gaps.

Other limitations worth noting: inference on CPU is slow, averaging around 20 to 40 seconds per query on consumer hardware. The 3B parameter model is the smallest variant of Llama 3.2, and there is a meaningful quality ceiling compared to larger models. The system has no memory between queries, so multi-turn conversations are not supported. The realistic next steps for a production deployment would be: implement RAG with the actual policy documents to eliminate hallucinated policy details; integrate order management API access so the model can look up real order status rather than directing users to check themselves; and establish a continuous evaluation pipeline that scores live conversations against the rubric defined here.
