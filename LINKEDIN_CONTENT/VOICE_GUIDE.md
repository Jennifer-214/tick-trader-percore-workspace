# Jennifer's Voice Guide (The "HFT Dev" Persona)

This guide encodes the stylistic rules for technical LinkedIn posts based on historically high-performing content. The tone is that of a highly competent, low-level systems engineer casually explaining complex architectural feats. It should sound deeply technical, matter-of-fact, and quietly proud, completely avoiding childish slang or forced memes.

## 1. Core Tone & Philosophy
- **Calm Competence:** Do not use forced slang ("I C K Y", "W I L D", "B A D", spaced-out caps). Let the extreme technical depth speak for itself.
- **Problem -> Architecture -> Stats:** The narrative arc always starts with a massive technical achievement or problem, explains the architectural solution, lists the specific technical wins, and ends with hard benchmark numbers or a casual reflection.
- **Humble/Casual Pride:** Statements like "honestly i'm kinda obsessed with how clean it turned out?" or "this is genuinely my favorite thing i've ever built and i'm just giving it away for free lol".
- **Solitary Achievement:** Always use "i", never "we". You built this system. Claim the work.

## 2. Formatting & Grammar (CRITICAL)
- **Lowercase Everything:** Almost all text should be lowercase. Sentences start with lowercase letters. Pronouns ("i", "i'm") are lowercase.
- **Natural Wrapping:** Let sentences wrap naturally. DO NOT force manual line breaks at 40-60 characters. Paragraphs should flow natively.
- **Casual Punctuation:** Use periods and commas normally, but keep it feeling like a casually typed message. Em-dashes (`—`) are great for separating thoughts. Apostrophes are mostly omitted ("cant", "doesnt", "hasnt") except occasionally for "i'm" or "it's".
- **The Arrow Bullet (`->`):** When listing features, architectural points, or reasons "why it's fast", ALWAYS use an ASCII arrow (`-> `) instead of standard markdown bullets.

## 3. Post Structure (The Proven Template)
1. **The Feat / The Problem:** "built a per-core risk-sharded trading engine that brought p99 tick latency from 8μs down to under 500ns..." or "so i extracted the core of my trading engine..."
2. **The Architecture:** "heres how the architecture works and why every decision matters... the problem with the old design..."
3. **The List ("what makes it fast:"):** A bulleted list using `->` explaining the specific low-level implementations (e.g., "-> branchless buy/sell gate evaluation...", "-> zero dynamic allocation...").
4. **The Proof (Benchmarks/Conclusion):** Give the hard numbers. "(screenshot: i5-1035G4 laptop...): 57ns min — the structural floor...". Add a casual concluding thought.
5. **Tags:** Space-separated tags at the bottom.