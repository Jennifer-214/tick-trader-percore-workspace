// MUST COMPILE: the three legitimate shapes.
#include "guard_design.hpp"
#include <cstdio>
int main() {
    EmitInputs   inf{}; ParseResult r{};
    STAMP_SET(inf, xgb_hyperparams);                      // group bit, no member -> ALLOW
    STAMP_SET(r,   inference_cfg_bandit_blend_ratio);     // parse side, not opted in -> ALLOW
    ParseResult* h = &r;
    STAMP_SET(*h,  inference_cfg_bandit_blend_ratio);     // handle-copy side -> ALLOW
    printf("ALLOW-LEG: all three legitimate shapes compiled\n");
    return 0;
}
