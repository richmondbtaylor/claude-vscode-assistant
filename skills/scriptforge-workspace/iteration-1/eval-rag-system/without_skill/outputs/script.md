# How Does a RAG System Actually Work — And Why Do Most Businesses Build Them Wrong?

**Channel:** Richmond Taylor — AI Tools & Automation for Business Decision-Makers
**Format:** YouTube Long-Form Script
**Estimated Runtime:** 12–15 minutes

---

## [HOOK — 0:00–0:45]

**[ON CAMERA — Direct address, confident, leaning slightly forward]**

You've probably heard the pitch: "Just connect your documents to an AI and it'll answer any question about your business."

And every time I hear that, I cringe a little — not because it's wrong, but because it's dangerously incomplete.

I've watched companies spend $50,000 building internal AI assistants that confidently answer questions with completely wrong information. Not because the AI is bad. Because the system was built wrong from day one.

Today I'm going to show you exactly how a RAG system works — and more importantly, I'm going to show you the five mistakes that I see businesses make over and over again that turn a promising tool into a liability.

If you're a decision-maker thinking about building one of these — or you already have one that isn't performing — this video is going to save you a lot of money and frustration.

Let's get into it.

---

## [SECTION 1: What Is RAG, and Why Does It Exist? — 0:45–2:30]

**[ON CAMERA]**

First, let's establish why RAG even exists.

Large language models — the technology behind ChatGPT, Claude, Gemini — are trained on massive amounts of text from the internet. That's their knowledge base.

But here's the problem: that training has a cutoff date. The model doesn't know what happened last week. It doesn't know your internal pricing policy. It has no idea what's in your employee handbook or your Q3 financial report.

**[SCREEN RECORDING or GRAPHIC: Simple timeline showing "AI training cutoff" vs. "Your business today"]**

So what do you do if you want AI to answer questions about your specific business, using your specific documents?

That's the problem RAG was designed to solve.

RAG stands for Retrieval-Augmented Generation. It's a technique — not a product, not a platform, a technique — for giving an AI model access to information it wasn't trained on, at the moment it needs it.

The basic idea is simple: instead of the AI relying only on its training, you give it a way to look things up before it responds. You augment the generation with retrieval.

**[ON CAMERA]**

Think of it like the difference between asking a question to someone who read a lot of books years ago... versus asking someone who has a live connection to your company's entire document library and can pull up the right page before they answer.

Same intelligence. Completely different usefulness.

---

## [SECTION 2: How RAG Actually Works — Step by Step — 2:30–5:30]

**[SCREEN RECORDING or ANIMATED DIAGRAM: Show the RAG pipeline in steps]**

Let me walk you through what actually happens inside a RAG system. I'm going to use plain language because the technical explanations tend to lose the people who actually need to understand this most.

**Step 1: Ingestion**

You have documents — PDFs, Word files, spreadsheets, web pages, whatever. The first step is loading all of that content into the system.

But you can't just dump the files in and call it done. The system has to process them: extract the text, clean it up, and split it into chunks — manageable pieces of text that can be searched individually.

**[GRAPHIC: Document → Chunks]**

How you chunk matters enormously, and we'll come back to that.

**Step 2: Embedding**

Once you have chunks, the system converts each one into something called an embedding — a list of numbers that represents the meaning of that text.

This sounds abstract, but the concept is straightforward: text that means similar things gets converted into numbers that are close together. Text that means different things gets numbers that are far apart.

**[GRAPHIC: Text chunk → Vector (list of numbers)]**

These embeddings get stored in what's called a vector database. Think of it as a library where every book is indexed not by title, but by meaning.

**Step 3: Retrieval**

Now a user asks a question. The system takes that question, converts it into an embedding using the same process, and then searches the vector database for the chunks whose embeddings are closest to the question's embedding.

**[GRAPHIC: Question → Embedding → Search → Top 3–5 Chunks]**

It's finding the most semantically similar content — not just keyword matching, but meaning matching.

The top results — usually three to five chunks — get pulled out.

**Step 4: Generation**

Those retrieved chunks get handed to the language model along with the original question, in what's called a prompt. The model reads both the question and the retrieved context, and generates an answer based on what it found.

**[GRAPHIC: Question + Retrieved Chunks → LLM → Answer]**

**[ON CAMERA]**

That's the full loop. User asks a question, system finds the relevant content, AI generates a response using that content.

When it works well, it feels like magic. The AI responds with specific, accurate, grounded answers — citing your actual documentation.

When it's built wrong, it confidently makes things up, retrieves the wrong content, or gives you answers that are technically based on your documents but completely miss the point of the question.

Which brings me to the part that actually matters.

---

## [SECTION 3: Why Most Businesses Build RAG Systems Wrong — 5:30–10:00]

**[ON CAMERA — authoritative, slightly slower pacing]**

I've consulted on a lot of AI builds. And the same mistakes come up every time. Let me walk you through the five biggest ones.

---

### Mistake #1: Treating It Like a File Upload, Not a Data Architecture Project

**[ON CAMERA]**

The number one mistake is thinking that you just connect your Google Drive or SharePoint to an AI tool and you're done.

You're not done. You've barely started.

The quality of a RAG system is almost entirely determined by the quality of your data preparation. If your documents are unstructured, inconsistent, full of formatting noise, or out of date — your AI will reflect all of that.

**[GRAPHIC: "Garbage in, garbage out" but for AI]**

I've seen companies feed a RAG system 10 years of email threads and wonder why the AI gives incoherent answers. You wouldn't hire an employee and tell them to read a decade of unorganized emails as their onboarding. Don't do it to your AI.

Curate your source documents. Clean them. Make sure they're current. That upfront work is what separates a useful system from an expensive chatbot that you'll quietly retire in six months.

---

### Mistake #2: Bad Chunking Strategy

**[SCREEN RECORDING or GRAPHIC: Two chunk examples — one too big, one too small]**

Remember how the system splits your documents into chunks? Most teams either use the default settings without thinking about it, or they pick a chunk size arbitrarily.

If your chunks are too large, you're feeding the AI walls of text — and the relevant answer gets buried in irrelevant content.

If your chunks are too small, you lose the surrounding context that gives the answer meaning. Imagine someone asks "What's the refund policy for enterprise clients?" and the chunk that gets retrieved is just the sentence "Refunds are available." — with no context about which client tier, what the timeline is, or what the conditions are.

**[ON CAMERA]**

Good chunking respects the natural structure of your content. A policy document should be chunked differently than a product catalog. A legal contract should be chunked differently than a FAQ page.

There's no universal right answer, but there is a universally wrong one: not thinking about it at all.

---

### Mistake #3: No Evaluation Pipeline

**[ON CAMERA]**

Here's a question most companies can't answer: How do you know if your RAG system is giving correct answers?

Most teams build it, demo it to stakeholders, see a few impressive results, and ship it. Then they find out six months later — usually from a frustrated user or a costly mistake — that it's been confidently wrong about entire categories of questions.

**[GRAPHIC: Chart — "Tested Questions: 12 | Total Possible Questions: Thousands"]**

You need an evaluation framework. A set of test questions with known correct answers, run regularly against the system, so you can measure accuracy over time.

This doesn't have to be sophisticated. A spreadsheet of 50 questions and answers, run weekly, will catch regressions and help you improve the system. But most teams never build it.

---

### Mistake #4: Ignoring the Retrieval Step

**[ON CAMERA]**

Everyone obsesses over the AI model — which LLM to use, how to write the prompt. And those things matter. But the retrieval step is where most systems actually fail.

If the wrong chunks are retrieved, it doesn't matter how good your AI is. It's going to generate a wrong answer based on wrong information. Confidently.

**[SCREEN RECORDING or GRAPHIC: Relevant chunk vs. irrelevant chunk being retrieved for the same question]**

Common retrieval problems include:

- Keyword-heavy questions that fool the embedding search into pulling irrelevant results
- Questions that require combining information from multiple sections, none of which score highly on their own
- Questions about topics that happen to use similar language to a completely different topic in your documents

The fix is something called hybrid search — combining the semantic vector search with traditional keyword search — and adding a re-ranking step that evaluates the retrieved chunks more carefully before passing them to the model.

Most off-the-shelf RAG tools don't do this by default. You have to deliberately design for it.

---

### Mistake #5: Building It As a One-Time Project

**[ON CAMERA]**

The final mistake is treating RAG as a build-and-forget project.

Your business changes. New policies get written. Old information becomes outdated. Prices change. Products launch and get discontinued.

A RAG system is only as current as the documents it's indexing. If you don't have a process to keep those documents updated, your AI assistant will keep confidently citing the 2022 pricing sheet and the policy that was replaced eight months ago.

**[GRAPHIC: Timeline — document updates vs. AI knowledge]**

The best RAG systems have continuous ingestion pipelines — automated processes that detect when source documents change and re-index them. Or at minimum, a scheduled review process. But many companies build the initial system and then move on. And the system slowly becomes a liability.

---

## [SECTION 4: What Good Actually Looks Like — 10:00–12:00]

**[ON CAMERA]**

So what does a well-built RAG system actually look like in practice?

Let me give you a concrete example.

Imagine a mid-size professional services firm. They have three years of proposal documents, a detailed service catalog, client case studies, and an internal pricing matrix. Their team spends hours every week answering the same questions: "What did we charge a client in this industry?" "What's our standard scope for this type of engagement?" "Do we have a case study that fits this prospect?"

A well-built RAG system for this firm would:

- Have curated, structured documents — not raw email chains or draft files
- Chunk documents in a way that preserves section context
- Use hybrid search plus re-ranking to make sure the right content surfaces
- Have a test suite of 50–100 common questions that gets reviewed monthly
- Have an automated pipeline that updates the index whenever documents are revised in their document management system

**[ON CAMERA]**

The result? Staff get accurate answers in seconds. New hires ramp up faster. Senior people stop getting interrupted with questions that are already answered in the documentation.

That's not magic. That's good architecture.

---

## [SECTION 5: Should You Build or Buy? — 12:00–13:15]

**[ON CAMERA]**

One more thing worth addressing: should you build your own RAG system, or use one of the many platforms that have this built in?

The honest answer is: it depends on your complexity, your security requirements, and your budget.

For most businesses, starting with a platform — tools like Microsoft Copilot, Notion AI, or purpose-built document AI tools — is the right call. They handle the infrastructure, and the tradeoffs are acceptable for standard use cases.

But if you're dealing with sensitive data, complex document structures, or highly specific retrieval needs, a custom build gives you far more control.

**[ON CAMERA]**

The key in either case is not to treat it as a plug-and-play product. Regardless of whether you're building or buying, you need a data strategy, an evaluation process, and a maintenance plan. That's what separates an AI initiative that delivers lasting value from one that looks impressive at the demo and disappoints in production.

---

## [OUTRO — 13:15–14:00]

**[ON CAMERA — direct, calm close]**

RAG systems are genuinely powerful. When they're built well, they compress hours of knowledge retrieval into seconds and make your team significantly more capable.

But they don't work by accident. They work because someone made deliberate decisions about data quality, chunking, retrieval design, evaluation, and maintenance.

If you're evaluating an AI build for your business — or you already have one and it's underperforming — run it against those five mistakes. I'd bet at least two of them are in play.

If you found this useful, subscribe — I cover practical AI strategy for business leaders every week. No hype, no fluff, just what you actually need to make good decisions about this stuff.

And drop a comment: have you built a RAG system? What surprised you? I read every one.

I'll see you in the next one.

---

## [END SCREEN — 14:00–14:30]

**[B-roll: Text overlays of next recommended video]**

*Subscribe button animation*
*"Watch next:" card — [Related video placeholder]*

---

## Production Notes

**Tone:** Authoritative but accessible. Richmond is the trusted advisor in the room — not the academic, not the hype man.

**Visuals to commission:**
- Animated RAG pipeline diagram (Ingestion → Embedding → Retrieval → Generation)
- "Garbage in, garbage out" graphic adapted for AI/documents
- Side-by-side chunk size comparison
- Retrieval failure vs. success visual
- Document currency timeline graphic

**B-roll suggestions:**
- Screen recordings of a chatbot interaction (correct vs. incorrect answer)
- Abstract vector/database visuals
- Office/business context footage

**Keywords to optimize for:**
- RAG system explained
- Retrieval augmented generation for business
- How RAG works
- AI document search mistakes
- Building RAG systems

---

*Script by: Claude Code for Richmond Taylor / Bishop AI*
*Word count: ~2,100 words*
*Estimated read time: 13–14 minutes at natural pace*
