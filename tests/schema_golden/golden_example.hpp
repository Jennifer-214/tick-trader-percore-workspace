// Golden fixture — a hand-authored reference block of each first-class type. The CI scan
// validates it (it carries [SCHEMA]_[v1.0] → in-scope); it is the committed format-by-example
// + a regression guard (a schema change that breaks it goes RED in check_session_docs).
//======================================================================
// [FILE]_[tests/schema_golden/golden_example.hpp]
//----------------------------------------------------------------------
// [TAG]_[[DATA_ORIENTED_DESIGN]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[the committed golden fixture — one valid block of each first-class type; the format SSoT-by-example]
// [DIAGRAM]
//   input --> [golden_add] --> sum
//   GoldenState { count }  <- HOT writer / SLOW reader
// [CONTAINS]
//   - [FUNCTION]_[golden_add]
//   - [STRUCT]_[GoldenState]
//======================================================================

//======================================================================
// [FUNCTION]_[golden_add]
//----------------------------------------------------------------------
// [TAG]_[[HOT_PATH] [DATA_ORIENTED_DESIGN]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[branchless add — the golden function exemplar]
// [DIAGRAM]
//   a --+--> sum
//   b --+
//======================================================================
// [CODE]
//======================================================================
inline int golden_add(int a, int b) { return a + b; }
//======================================================================
// [END_CODE]
//======================================================================
// [COMMENT]
//——————————————————————————————————————————————
// [[v1]]
// the reference for the hybrid layout — compact orient above, the body framed,
// the bulky history + derived facts below, then the closer.
// [SUPPORTING_DOCS]
//   - [DESIGN_SPEC]_[in-code-documentation-schema]
//======================================================================
// [DERIVED]   (tool-fills later — never hand-written)
//----------------------------------------------------------------------
// [SIZE]_[pending-generator]
// [SIMD]_[none]
// [BRANCHES]_[data-dependent: 0]
//======================================================================
// [END_FUNCTION]_[golden_add]
//======================================================================

//======================================================================
// [STRUCT]_[GoldenState]
//----------------------------------------------------------------------
// [TAG]_[[HOT_PATH] [DATA_ORIENTED_DESIGN]]
// [THREAD]_[[HOT_WRITER] [SLOW_READER]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[layout-by-access-pattern exemplar — one cache line]
// [DIAGRAM]
//   line0: [count:8][pad:56] = 64B
//======================================================================
// [CODE]
//======================================================================
struct alignas(64) GoldenState { long count; };
//======================================================================
// [END_CODE]
//======================================================================
// [DERIVED]   (tool-fills later)
//----------------------------------------------------------------------
// [SIZE]_[64B]
// [ALIGN]_[64]
// [CACHE_LINES]_[1]
// [STRADDLE]_[none]
//======================================================================
// [END_STRUCT]_[GoldenState]
//======================================================================
