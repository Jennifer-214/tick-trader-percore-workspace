# LinkedIn Post: X-Macro Registries

**Topic ID:** #8
**Target Date:** 2026-06-02
**Primary Pillar:** Pattern Library

---

## 1. The Hook (First 2 Lines)
*Goal: Stop the scroll. Challenge an assumption or state a surprising result.*

Adding one field to your system shouldn't require touching 5 different files.
If you're still manually updating parsers, emitters, and structs, you're inviting the "N-site" bug class.

---

## 2. The Context/Problem
*Goal: Why does this matter? What's the pain point?*

We've all been there: you add a new configuration parameter. You update the struct. You forget the JSON parser. Or the GUI panel. Or the persistence logic. Suddenly, your backtest and live production are out of sync because one site was missed.

---

## 3. The Technical Solution
*Goal: High-signal insight. Use lists or code-like snippets.*

We use **X-Macro Registries with Y3 Dispatch** to maintain a single source of truth for all metadata. One row in a macro generates EVERYTHING.

- **The Registry:** A single list of fields with types, default values, and metadata.
- **Y3 Dispatch:** Token-pasting to conditionally include fields in specific views (e.g., `PARSER_ONLY` vs `RUNTIME`).
- **AUTOPOPULATE:** A companion macro that handles the boilerplate of copying data between structures.

```cpp
#define FOREACH_OMS_FIELD(X) \
    X(order_id,   SCALAR,  INCLUDE, uint64_t) \
    X(filled_qty, SCALAR,  INCLUDE, double)   \
    X(debug_msg,  STRING,  SKIP,    char[64])

// Expansion 1: Struct fields
#define X(name, storage, presence, type) type name;
struct OrderState { FOREACH_OMS_FIELD(X) };

// Expansion 2: JSON Parser
#define X(name, storage, presence, type) if (key == #name) { parse_val(r.name, val); }
```

---

## 4. The "Aha!" Moment / Lesson
*Goal: What should the reader take away?*

Don't fix bugs; extinguish them. By moving to a registry-driven architecture, we made it physically impossible to "forget" a site. If it's in the macro, it's in the parser, the struct, and the GUI.

---

## 5. Call to Action (CTA)
*Goal: Drive engagement/comments.*

What's your strategy for keeping parallel data structures in sync? Do you trust your memory or your compiler?

---

## 6. Hashtags
*Copy from TAG_LIBRARY.md*

#HFT #Cpp #Metaprogramming #SoftwareArchitecture #CleanCode #Maintainability
