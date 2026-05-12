---
name: Don't use AskUserQuestion tool — present options as plain text
description: Caramel prefers seeing the entire conversation including option presentations as text she can scroll back through, not modal question boxes
type: feedback
originSessionId: 3f84971f-8154-47ea-a8b9-86f7fad2325d
---
When asking Caramel to choose between options or for clarification, write the options out in plain text and let her reply directly. **Do not use the AskUserQuestion tool.**

**Why:** She wants to see the full conversation history visible — option text, options, recommendations, all inline. Question-box modals collapse the question shape into a UI widget that doesn't preserve the same way as plain conversation text. She loses scroll-back ability.

**How to apply:** When you'd otherwise reach for AskUserQuestion (multi-option choices, multi-select preferences, clarification prompts), instead write a clearly-structured plain-text section:

```
## Option A — [name]
Description + tradeoffs

## Option B — [name]
Description + tradeoffs

**Recommendation:** Option A because [rationale].
```

Then end the turn and wait for her reply. Same content; different surface. Apply across all decision points: A.2 approach selection, audit follow-ups, scope decisions.
