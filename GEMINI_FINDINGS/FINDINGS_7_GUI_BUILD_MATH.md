# Phase 7: GUI, Build, and Deep Arithmetic Edge Cases

## NEW Obscure Issues (59-68)

1. **FixedPoint AddSat Carry Neglect** (`FixedPoint/FixedPointN.hpp`)
   - **Details:** The `FPN_AddSat` implementation attempts to saturate on overflow but neglects to properly check the carry flag out of the most significant word for very large precision types. This can cause the addition to wrap around to a small positive value instead of saturating at `MAX`.
2. **FixedPoint ToDouble Exponent Overflow** (`FixedPoint/FixedPointN.hpp`)
   - **Details:** `FPN_ToDouble` lacks bounds checking on its bitwise exponent calculation. Extremely large `FPN` values (e.g., $F > 96$) can silently overflow the IEEE-754 double exponent space, resulting in `Inf` or `-Inf` spreading through the system without triggering NaN guards.
3. **FixedPoint FromString Integer Wrap-Around** (`FixedPoint/FixedPointN.hpp`)
   - **Details:** `FPN_FromString` parses integer digits iteratively by multiplying by 10 and adding. It lacks bounds checking during this accumulation. Parsing a maliciously large string (e.g., massive JSON payload) will silently integer-wrap, creating a completely incorrect internal value.
4. **FixedPoint Exp Magnitude Loss** (`FixedPoint/FixedPointN.hpp`)
   - **Details:** The Taylor series expansion for `FPN_Exp` converges too slowly and loses magnitude for negative values far from zero, risking zero-truncation. In ML contexts, this can flatten probability distributions in the Bandit blending logic.
5. **GUI Blocking I/O Freezes** (`GUI/SettingsPanel.hpp`)
   - **Details:** Functions like `cfg_write_field` and `Settings_RescanModels` perform blocking file operations (`fopen`, `fwrite`) and directory scans directly on the ImGui render thread. This will cause the entire UI to freeze and jitter whenever settings are changed or models are loaded.
6. **Concurrent `localtime()` Race Condition** (`GUI/ChartPanel.hpp` vs `DataStream/MetricsLog.hpp`)
   - **Details:** Both `GUI_PriceChart` and engine-side logging (`_metrics_timestamp`) use the C standard `localtime()` function. `localtime` returns a pointer to a shared static buffer. If the GUI and engine threads call it simultaneously, the time struct will be corrupted, logging invalid timestamps. Needs `localtime_r()`.
7. **HealthLog Unsafe Rotation via `system()`** (`MemHeaders/HealthLog.hpp`)
   - **Details:** `Health_LogPruneRotated` uses `system()` to execute shell commands (`rm`, `mv`) for log rotation. Calling `system()` forks the process, which is catastrophic in an HFT environment, causing massive kernel-level latency spikes and risking zombie processes.
8. **Missing Signal Handlers (SIGINT/SIGTERM)** (`main.cpp`)
   - **Details:** The application lacks a graceful termination handler for standard OS signals. If stopped via `systemctl stop` or `Ctrl+C`, the engine terminates immediately. This orphans open orders on the exchange and prevents writing the final `portfolio.snapshot`, risking capital on restart.
9. **Build System AVX-512 & Aliasing Gaps** (`CMakeLists.txt`)
   - **Details:** The CMake configuration does not explicitly set `-mavx512f` or `-mavx512vl`, meaning the compiler relies entirely on the default architecture of the build machine. It also lacks `-fno-strict-aliasing` despite extensive type punning in the codebase, inviting aggressive compiler optimizations that break memory logic.
10. **Naive SMT Sibling Topology Detection** (`CoreFrameworks/EngineSharded.hpp`)
    - **Details:** `EngineSharded_GetSiblingCPU` uses a naive file-reading logic on `/sys/devices/system/cpu/cpuX/topology/thread_siblings_list`. It assumes a basic 2-way SMT format. On complex topologies (e.g., multi-numa AMD EPYC, Intel P/E cores, or >2-way SMT), the parser will fail or pin threads incorrectly, destroying L1/L2 cache locality.