#!/usr/bin/env python3
# Generalized [SCHEMA]_[v1.0] wrapper for GUI/*.hpp (E.1.2.A P6.121+).
# Comments-only. Per-file config: FILE-block placement (replace-banner | after-anchor),
# banners to strip, and the unit table. Boundary rule: unit closes at the first column-0
# `}`/`};` after its signature (namespaces + trivial structs are left inline = not listed).
# Lossless gate is the hard backstop.
import re, sys
BAR  = "//" + "="*70
THIN = "//" + "-"*70
GAP  = "// [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D-327)"

def fileblock(path, tags, overview, contains):
    out = [BAR, f"// [FILE]_[{path}]", THIN, f"// [TAG]_[{tags}]", "// [SCHEMA]_[v1.0]",
           f"// [OVERVIEW]_[{overview}]"]
    if contains:
        out.append("// [CONTAINS]")
        for c in contains: out.append(f"//   - {c}")
    out.append(BAR)
    return out

def wrap_file(cfg):
    path = cfg["path"]
    src = open(path).read()
    # 1) [FILE] block
    fb = fileblock(path, cfg["file_tags"], cfg["file_overview"], cfg.get("contains"))
    act, anchor = cfg["fileblock"]
    if act == "replace":
        assert anchor in src, f"{path}: file banner not found"
        src = src.replace(anchor, "\n".join(fb), 1)
    else:  # after
        lines0 = src.split("\n")
        ai = [i for i,l in enumerate(lines0) if l.rstrip()==anchor]
        assert len(ai)==1, f"{path}: anchor {anchor!r} found {len(ai)}x"
        lines0[ai[0]+1:ai[0]+1] = [""] + fb
        src = "\n".join(lines0)
    lines = src.split("\n")
    # 2) strip section banners: heading + opening bar(s) + the bar below +
    #    the closing bar after any contiguous prose (keep the prose)
    isbar = lambda s: re.match(r'^//={20,}\s*$', s) is not None
    for heading in cfg.get("banners", []):
        idx=[i for i,l in enumerate(lines) if l.rstrip()==heading]
        assert len(idx)==1, f"{path}: banner {heading!r} x{len(idx)}"
        i=idx[0]; rm={i}
        j=i-1
        while j>=0 and isbar(lines[j]): rm.add(j); j-=1          # opening bar(s)
        j=i+1
        if j<len(lines) and isbar(lines[j]): rm.add(j); j+=1     # bar below heading
        while j<len(lines) and lines[j].lstrip().startswith("//") and not isbar(lines[j]): j+=1  # prose
        if j<len(lines) and isbar(lines[j]): rm.add(j)           # closing bar after prose
        for k in sorted(rm, reverse=True): del lines[k]
    # 3) locate units
    defkw = re.compile(r'^(struct|static inline|static void|void|bool|int|inline|static ImVec4|static ImU32|static const char)\b')
    located=[]
    for name,kind,tags,ov in cfg["units"]:
        sig=None
        for i,l in enumerate(lines):
            if not defkw.match(l): continue
            if kind=="struct":
                if re.match(rf'^struct\s+{re.escape(name)}\b', l): sig=i;break
            else:
                # skip a forward-declaration (single-line sig ending in ';')
                if re.search(rf'\b{re.escape(name)}\s*\(', l) and not l.rstrip().endswith(";"):
                    sig=i;break
        assert sig is not None, f"{path}: sig not found {name}"
        # pull a preceding `template <...>` line into the unit (it belongs in [CODE])
        while sig-1>=0 and re.match(r'^template\s*<', lines[sig-1]):
            sig-=1
        close=None
        for j in range(sig+1,len(lines)):
            if re.match(r'^\}', lines[j]): close=j;break
        assert close is not None, f"{path}: close not found {name}"
        assert re.match(r'^\};?\s*(//.*)?$', lines[close]), \
            f"{path}: {name} close line not a clean }} : {lines[close]!r}"
        # pre = top of contiguous comment/blank block above sig, trim leading blanks
        j=sig-1
        while j>=0 and (lines[j].strip()=='' or lines[j].lstrip().startswith('//')): j-=1
        pre=j+1
        while pre<sig and lines[pre].strip()=='': pre+=1
        located.append((sig,close,pre,name,kind,tags,ov))
    located.sort()
    for a,b in zip(located,located[1:]):
        assert a[1]<b[0], f"{path}: overlap {a[3]}/{b[3]}"
    for sig,close,pre,name,kind,tags,ov in sorted(located,reverse=True):
        TYPE="STRUCT" if kind=="struct" else "FUNCTION"
        header=[BAR,f"// [{TYPE}]_[{name}]",THIN,f"// [TAG]_[{tags}]","// [SCHEMA]_[v1.0]",f"// [OVERVIEW]_[{ov}]",BAR]
        code_open=[BAR,"// [CODE]",BAR]
        close_blk=[BAR,"// [END_CODE]",BAR]
        if kind=="struct": close_blk+=[GAP,BAR,f"// [END_STRUCT]_[{name}]",BAR]
        else: close_blk+=[f"// [END_FUNCTION]_[{name}]",BAR]
        lines[close+1:close+1]=close_blk
        lines[sig:sig]=code_open
        lines[pre:pre]=header
    open(path,"w").write("\n".join(lines))
    print(f"{path}: wrapped {len(located)} units")

G="[GUI]"; GC="[GUI] [CONCURRENCY]"
CONFIGS=[
 dict(path="GUI/EngineHeaderPanel.hpp",
   fileblock=("replace","""//======================================================================================================
// [ENGINE HEADER PANEL — v5.8.6b]
//======================================================================================================
// Single-line ImGui header showing the running engine's version + feature
// registry hash + model format version. Same content rendered in both
// engine_gui (live) and foxml_suite (training/backtest) — call
// EngineHeader_Render() from each binary's render loop.
//
// All values pulled from compile-time constants:
//   ENGINE_VERSION_STRING (Version.hpp)
//   FEATURE_REGISTRY_HASH() (FeatureRegistry.hpp — FNV-1a fold)
//   MODEL_FORMAT_VERSION (ModelInference.hpp)
//
// This panel is the operator-visible counterpart to the boot-log line
// emitted by NodeModelZoo_TryLoadRole at model load. Shows what the
// CURRENT BUILD speaks; per-loaded-model match state is in the boot log.
// (Future ship can extend this panel with per-model match status if
// the boot log proves insufficient — for now it's deliberately minimal.)
//======================================================================================================"""),
   file_tags=G, file_overview="single-line engine header — release/engine/format/registry-hash from compile-time constants + the optional cfg-path and WS-heartbeat freshness from the snapshot; rendered identically in engine_gui + foxml_suite",
   contains=None,
   units=[("EngineHeader_Render","fn",G,"render the one-line Engine header — build-time version/format/registry fields, plus cfg source path + color-coded WS heartbeat freshness when a snapshot is passed")]),
 dict(path="GUI/FoxmlTheme.hpp",
   fileblock=("after","#pragma once"),
   file_tags=G, file_overview="the FoxML Classic ImGui + ImPlot palette (terminal-matched) + the theme applicator — sourced from the Kitty/Waybar theme; FoxmlColors holds the constexpr palette, Foxml_ApplyTheme wires it into the ImGui/ImPlot styles",
   contains=None,
   units=[("Foxml_ApplyTheme","fn",G,"apply the FoxML Classic palette to the ImGui + ImPlot styles — sharp corners, warm-gold chrome, no blue defaults")]),
 dict(path="GUI/TradeReader.hpp",
   fileblock=("after","#pragma once"),
   file_tags=G, file_overview="reads the engine CSV trade log into chart markers + an equity curve — a port of tools/chart.py TradeReader; refreshes on file-size change (no per-frame reopen), locale-immune CSV parse",
   contains=None,
   units=[("TradeData","struct",G,"the loaded trade markers + equity curve + the file-size cache for change detection"),
          ("TradeData_Init","fn",G,"init a TradeData for a CSV path"),
          ("csv_field","fn",G,"extract the Nth comma-separated field from a CSV line"),
          ("TradeData_Refresh","fn",G,"reload the trade CSV if its size changed — pair BUY/SELL fees FIFO into net-P&L equity points, cap markers to the recent window")]),
 dict(path="GUI/LogViewerPanel.hpp",
   fileblock=("after","#pragma once"),
   file_tags=G, file_overview="tails engine.log in a dockable panel — reads the last 32KB on file-size change, color-codes lines by severity/event, auto-scrolls and wraps",
   contains=None,
   units=[("LogViewer","struct",G,"the tail buffer + file-path + size cache + auto-scroll flag"),
          ("LogViewer_Init","fn",G,"init a LogViewer for a log path"),
          ("LogViewer_Refresh","fn",G,"reload the log tail (last 32KB) if the file grew, snapping to the first complete line"),
          ("GUI_Panel_LogViewer","fn",G,"render the Engine Log panel — per-line color coding + wrapped text + auto-scroll")]),
 dict(path="GUI/CandleAccumulator.hpp",
   fileblock=("after","#pragma once"),
   file_tags=GC, file_overview="aggregates raw trade ticks into OHLCV candles fed from the engine WS thread — thread-safe (engine writes under the mutex, GUI reads a copied snapshot); a port of tools/chart.py CandleAccumulator",
   contains=None,
   units=[("Candle","struct",G,"one OHLCV candle — bucket start + open/high/low/close + volume split by side"),
          ("CandleAccumulator","struct",GC,"the ring of completed candles + the in-progress candle + running VWAP, guarded by a mutex for the WS-writer / GUI-reader split"),
          ("CandleAccumulator_Init","fn",GC,"init the accumulator + its mutex at a candle interval"),
          ("CandleAccumulator_Push","fn",GC,"engine-thread: fold one wall-clock tick into the current candle, flushing to the ring on a bucket boundary"),
          ("CandleAccumulator_PushWithTime","fn",GC,"backtest-replay variant of Push — the caller supplies the tick timestamp instead of wall-clock"),
          ("CandleSnapshot","struct",G,"a GUI-thread copy of the candle ring + in-progress candle + VWAP"),
          ("CandleAccumulator_Snapshot","fn",GC,"copy the ring + current candle into a CandleSnapshot in chronological order (under the mutex)"),
          ("CandleAccumulator_SetInterval","fn",GC,"reset the accumulator to a new candle interval, clearing all data"),
          ("CandleAccumulator_Destroy","fn",GC,"destroy the accumulator's mutex")]),
]
if __name__ == "__main__":
    for c in CONFIGS: wrap_file(c)
    print("BATCH 1 (5 small GUI files) wrapped")
