// MUST FAIL TO COMPILE: the live defect shape (StampHelper.hpp:250).
#include "guard_design.hpp"
int main() {
    EmitInputs inf{};
    STAMP_SET(inf, inference_cfg_bandit_blend_ratio);     // bit without value -> MUST REFUSE
    return 0;
}
