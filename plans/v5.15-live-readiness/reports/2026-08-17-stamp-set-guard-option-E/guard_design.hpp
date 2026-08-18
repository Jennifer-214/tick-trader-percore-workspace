// Full-fidelity replica of the D-426 guard design (expression form, trait-gated).
#pragma once
#include <cstdint>
#include <type_traits>
#include <utility>

#define BITMAP_SET(w, m) ((w) |= (m))

namespace tt {
    template <class F, class... Args>
    constexpr auto is_valid_impl(int) -> decltype(std::declval<F>()(std::declval<Args>()...), bool{}) { return true; }
    template <class F, class... Args>
    constexpr bool is_valid_impl(...) { return false; }
    template <class... Args, class F>
    constexpr bool is_valid(F&&) { return is_valid_impl<F, Args...>(0); }

    template <typename T> inline constexpr bool is_stamp_emit_inputs_v = false;
}

// expression form — mirrors STAMP_SET's (s) argument exactly
#define TT_HAS_MEMBER(s, name) \
    (tt::is_valid<decltype((s))>([](auto&& _x) -> decltype(void(_x.name)) {}))

#define STAMP_SET(s, name)                                                        \
    do {                                                                          \
        static_assert(!tt::is_stamp_emit_inputs_v<std::decay_t<decltype(s)>>      \
                          || !TT_HAS_MEMBER(s, name),                             \
                      "STAMP_SET on an emit-side FIELD sets a presence bit "      \
                      "without its value - use STAMP_PUT(s, name, value)");       \
        BITMAP_SET((s).has_flags, MASK_##name);                                   \
    } while (0)

struct EmitInputs {                 // opts in -> guarded
    uint64_t has_flags;
    double   inference_cfg_bandit_blend_ratio;
    char     run_name[64];
};
struct ParseResult {                // does NOT opt in -> unrestricted
    uint64_t has_flags;
    double   inference_cfg_bandit_blend_ratio;
};
namespace tt { template <> inline constexpr bool is_stamp_emit_inputs_v<EmitInputs> = true; }

#define MASK_inference_cfg_bandit_blend_ratio 1u
#define MASK_run_name                         2u
#define MASK_xgb_hyperparams                  4u
