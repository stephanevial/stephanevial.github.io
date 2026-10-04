---
url: /lexique-ia/en/book/token/
title: "Token: definition and example | Stéphane Vial"
description: "In artificial intelligence, a token is the smallest unit of text that language models handle. It can be a whole word, a fragment of a word, a punctuation mark…"
h1: "Token"
chapeau: "Chapter 5"
gabarit: notion
ordre: 5
page: 83
---

**Definition**  
In artificial intelligence, a token is the smallest unit of text that language models handle. It can be a whole word, a fragment of a word, a punctuation mark or a space, depending on how each model does its splitting. Rather than reading continuous sentences, the model receives an ordered sequence of tokens, each converted into a numerical representation before being processed. Generative models also produce their answers token by token, in an extremely fast probabilistic chain.

**Example**  
The sentence *Hello, how are you?* could be split into six tokens: *Hello* + *,* + *how* + *are* + *you* + *?*. Some words can be divided further: *tokenization* would become *token* + *ization*. In applications such as ChatGPT, Claude or Gemini, which run on large language models, every question sent and every answer generated is counted in tokens. That count determines the length limits of a conversation, the processing speed and often the cost of use.

**Why it matters**  
The token is the basic unit of operation for language models. The context window, too, is expressed in tokens, not in words. This logic has concrete effects: the same text does not yield the same number of tokens from one language to another. The cost of using models is in fact generally calculated based on the number of tokens processed, input as well as output. Understanding what a token is therefore helps you grasp how an AI system “reads” and generates text, but also why some requests cost more in computation and in energy.

## How to cite this text

Vial, S. (2026). Token. In *A Living Lexicon of Artificial Intelligence* (p. 83). Stéphane Vial, publisher, Montréal.
