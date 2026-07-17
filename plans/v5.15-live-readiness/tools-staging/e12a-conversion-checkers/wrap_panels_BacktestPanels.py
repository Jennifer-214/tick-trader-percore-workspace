#!/usr/bin/env python3
# Part-scripted [SCHEMA]_[v1.0] wrapper for Backtest/BacktestPanels.hpp (E.1.2.A P6.120).
# Comments-only: strips the 12 section banners, inserts a [FILE] block, wraps 45 units.
# Reliability rests on the verified invariant: every top-level unit closes with a
# column-0 `}` and there are NO other column-0 braces (no namespace/extern). Lossless
# gate is the backstop — this script must not change a single code byte.
import re, sys

PATH = "Backtest/BacktestPanels.hpp"
BAR  = "//" + "="*70
THIN = "//" + "-"*70
GAP  = "// [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D-327)"

FILE_HEADER_OLD = """//======================================================================================================
// [BACKTEST PANELS]
//======================================================================================================
// Phase 1 panels: Data Browser, Run Control, Results
// follows existing panel pattern from DashboardPanels.hpp:
//   - each panel is a standalone ImGui window (dockable, rearrangeable)
//   - state structs are separate from render functions
//   - GUI never calls engine functions directly (reads display structs only)
//======================================================================================================"""

FILE_BLOCK = f"""{BAR}
// [FILE]_[Backtest/BacktestPanels.hpp]
{THIN}
// [TAG]_[[GUI] [BACKTEST]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[the foxml_suite backtest GUI — Data Browser, Run Control, Results, Comparison, Past Runs, Optimizer, and the big Training panel (WF / held-out / multi-horizon train+stamp); each panel = a state struct + worker threads + an ImGui render fn, and the GUI only ever reads display structs, never calls engine fns directly]
{BAR}
// follows the panel pattern from DashboardPanels.hpp:
//   - each panel is a standalone ImGui window (dockable, rearrangeable)
//   - state structs are separate from render functions
//   - GUI never calls engine functions directly (reads display structs only)
//   - long-running work (backtest / WF / training) runs on a pthread worker;
//     the render fn reads a thread-safe snapshot when the worker finishes
{BAR}"""

# the 11 non-file section banner headings to strip (heading + surrounding == bars)
BANNERS = [
    "// [DATA PANEL STATE]",
    "// [SAMPLES SNAPSHOT — thread-safe display struct]",
    "// [RUN CONTROL STATE]",
    "// [PANEL: DATA BROWSER]",
    "// [PANEL: RUN CONTROL]",
    "// [PANEL: RESULTS]",
    "// [COMPARISON STATE]",
    "// [PANEL: COMPARISON]",
    "// [OPTIMIZER PANEL STATE]",
    "// [PANEL: OPTIMIZER]",
    "// [TRAINING PANEL STATE]",
    "// [PANEL: TRAINING]",
]

G  = "[GUI] [BACKTEST]"
GM = "[GUI] [ML] [BACKTEST]"

# (name, kind, tags, overview)  — 45 units; 9 trivial worker-arg structs left inline
UNITS = [
 ("DataPanelState","struct",G,"state for the Data Browser panel — the recursive CSV scan results + per-file selection"),
 ("DataPanel_Init","fn",G,"init the Data Browser state with the default data dir"),
 ("DataPanel_Scan","fn",G,"recursively scan data_dir for .csv files, filename-sorted (chronological for YYYY-MM-DD)"),
 ("SamplesSnapshot","struct",G,"thread-safe label-distribution display struct — the worker writes it once post-run, the GUI reads it when running==0 (kills the labels[] realloc-race)"),
 ("RunControlState","struct",G,"state for the Run Control panel — the worker thread, run config + results, snapshot, and candle feed"),
 ("RunControl_Init","fn",G,"init Run Control state + allocate the BacktestResults buffers"),
 ("SamplesSnapshot_Compute","fn",G,"compute the kind-aware label distribution into a SamplesSnapshot — worker-thread only, after labels are populated and before running=0"),
 ("backtest_worker_fn","fn",G,"background thread: run a backtest, then compute the samples snapshot"),
 ("collect_multi_horizon_worker_fn","fn",GM,"background thread: collect features once for a multi-horizon training run"),
 ("RunControl_Start","fn",G,"spawn the backtest worker thread for the selected files + config"),
 ("GUI_Panel_DataBrowser","fn",G,"render the Data Browser panel — the discovered-file list + selection"),
 ("GUI_Panel_RunControl","fn",G,"render the Run Control panel — start/cancel, progress, and the post-run snapshot stats"),
 ("ResultsPnlColor","fn",G,"pick a P&L cell color from the value sign"),
 ("GUI_Panel_Results","fn",G,"render the Results panel — the backtest stats table + equity curve"),
 ("ComparisonState","struct",G,"state for the Comparison panel — saved run slots for side-by-side compare"),
 ("PastRun","struct",G,"one loaded past-run record — kind-aware metrics + fingerprint + horizon metadata"),
 ("PastRunsState","struct",G,"state for the Past Runs panel — the scanned run-directory list + selection"),
 ("PastRuns_Init","fn",G,"init the Past Runs state"),
 ("parse_kv_line","fn",G,"parse one key=value line from a run's metadata file"),
 ("PastRuns_LoadOne","fn",G,"load one past-run record from its run directory"),
 ("past_runs_unlink_cb","fn",G,"nftw unlink callback for recursive run-directory deletion"),
 ("PastRuns_DeleteDir","fn",G,"recursively delete a run directory via nftw"),
 ("PastRun_ParseHorizon","fn",G,"parse a horizon prefix + label out of a run-directory name"),
 ("PastRuns_ScanOneDir","fn",G,"scan one directory for past-run records"),
 ("PastRuns_Scan","fn",G,"scan the runs root for every past-run record"),
 ("PastRun_MetricLabel","fn",G,"the metric-label string for a run's label kind (accuracy vs correlation)"),
 ("GUI_Panel_PastRuns","fn",GM,"render the Past Runs panel — the run table + per-run detail + delete/compare actions"),
 ("Comparison_Init","fn",G,"init the Comparison state"),
 ("Comparison_Free","fn",G,"free the Comparison saved-run buffers"),
 ("Comparison_SaveRun","fn",G,"save the current results into a Comparison slot"),
 ("GUI_Panel_Comparison","fn",G,"render the Comparison panel — side-by-side saved runs"),
 ("OptimizerPanelState","struct",G,"state for the Optimizer panel — the two sweep ranges + the results grid + the worker"),
 ("OptimizerPanel_Init","fn",G,"init the Optimizer panel state with default sweep ranges"),
 ("optimizer_worker_fn","fn",GM,"background thread: run a parameter sweep"),
 ("GUI_Panel_Optimizer","fn",GM,"render the Optimizer panel — sweep ranges, the results grid, and the best cell"),
 ("TrainingPanelState","struct",GM,"state for the Training panel — every training / validation / multi-horizon knob and worker handle"),
 ("TrainingPanel_Init","fn",GM,"init the Training panel state — defaults for every training/validation knob"),
 ("walkforward_worker_fn","fn",GM,"background thread: run walk-forward CV"),
 ("hp_sweep_worker_fn","fn",GM,"background thread: run a hyperparam training sweep"),
 ("fullvalidation_worker_fn","fn",GM,"background thread: run full validation (WF + held-out gap)"),
 ("train_model_worker_fn","fn",GM,"background thread: train + stamp one production model"),
 ("mh_run_one_horizon_fv","fn",GM,"run full validation for one horizon of a multi-horizon grid + emit its stamp"),
 ("mh_per_horizon_parallel_worker","fn",GM,"parallel per-horizon worker for the multi-horizon sweep (caps libgomp to 1 thread)"),
 ("train_multi_horizon_worker_fn","fn",GM,"background thread: train a multi-horizon model grid, serial or parallel"),
 ("GUI_Panel_Training","fn",GM,"render the Training panel — collect features, WF, held-out, optimizer, multi-horizon, and model training/stamping"),
]

def is_barline(s):
    return re.match(r'^//={20,}\s*$', s) is not None

def main():
    src = open(PATH).read()
    assert FILE_HEADER_OLD in src, "file-header banner not found verbatim"
    src = src.replace(FILE_HEADER_OLD, FILE_BLOCK, 1)
    lines = src.split('\n')

    # 1) strip the 11 section banners (heading + adjacent == bars), keep prose
    for heading in BANNERS:
        idx = [i for i,l in enumerate(lines) if l.rstrip()==heading]
        assert len(idx)==1, f"banner {heading!r} found {len(idx)}x"
        i = idx[0]
        lo, hi = i, i
        if i-1>=0 and is_barline(lines[i-1]): lo = i-1
        if i+1<len(lines) and is_barline(lines[i+1]): hi = i+1
        del lines[lo:hi+1]

    # 2) wrap units bottom-up (so insertions don't shift earlier signatures)
    defkw = re.compile(r'^(struct|static inline|static void|void|bool|int|inline|static ImVec4)\b')
    located = []
    for name, kind, tags, ov in UNITS:
        sig = None
        for i,l in enumerate(lines):
            if not defkw.match(l):
                continue
            if kind=="struct":
                if re.match(rf'^struct\s+{re.escape(name)}\b', l): sig = i; break
            else:
                if re.search(rf'\b{re.escape(name)}\s*\(', l): sig = i; break
        assert sig is not None, f"signature not found: {name}"
        # close = first column-0 `}` at/after sig+1
        close = None
        for j in range(sig+1, len(lines)):
            if re.match(r'^\}', lines[j]): close = j; break
        assert close is not None, f"close brace not found: {name}"
        # pre = top of the contiguous comment/blank block above sig (stop at code),
        # then trim leading blanks → the description prose lands in the orient region
        j = sig - 1
        while j >= 0 and (lines[j].strip()=='' or lines[j].lstrip().startswith('//')):
            j -= 1
        pre = j + 1
        while pre < sig and lines[pre].strip()=='':
            pre += 1
        located.append((sig, close, pre, name, kind, tags, ov))

    # sanity: no overlaps, all distinct
    located.sort()
    for a,b in zip(located, located[1:]):
        assert a[1] < b[0], f"overlap {a[3]} / {b[3]}"

    for sig, close, pre, name, kind, tags, ov in sorted(located, reverse=True):
        TYPE = "STRUCT" if kind=="struct" else "FUNCTION"
        header = [BAR, f"// [{TYPE}]_[{name}]", THIN,
                  f"// [TAG]_[{tags}]", "// [SCHEMA]_[v1.0]",
                  f"// [OVERVIEW]_[{ov}]", BAR]
        code_open = [BAR, "// [CODE]", BAR]
        close_blk = [BAR, "// [END_CODE]", BAR]
        if kind=="struct":
            close_blk += [GAP, BAR, f"// [END_STRUCT]_[{name}]", BAR]
        else:
            close_blk += [f"// [END_FUNCTION]_[{name}]", BAR]
        lines[close+1:close+1] = close_blk   # after body close
        lines[sig:sig]         = code_open   # [CODE] right before signature
        lines[pre:pre]         = header      # block header above the description prose

    # 3) assertions: no original section banner text remains
    joined = '\n'.join(lines)
    for heading in BANNERS:
        assert heading not in joined, f"banner still present: {heading}"
    open(PATH,'w').write(joined)
    print(f"wrapped {len(UNITS)} units; {len(BANNERS)} banners stripped; [FILE] block inserted")

main()
