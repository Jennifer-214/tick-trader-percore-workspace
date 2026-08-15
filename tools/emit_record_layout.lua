-- emit_record_layout.lua — headless struct-layout fact emitter for the CI cache-layout gate (D-320).
--
-- REUSES the plugin's tested record-layout PARSER (recordlayout.parse) + straddle detector
-- (recordlayout.straddlers) + clang flag-extraction (sizeprobe._flags_for), so the CI gate and the
-- fox-symdeps HUD compute struct layout from the SAME source — no Class-18 / two-fact-cores mirror
-- (D-310 unified the fact cores; D-320 locks the reuse). LAYOUT facts ONLY, via clang
-- `-Xclang -fdump-record-layouts` (Itanium-ABI-identical to the shipped g++ — D-321; CODEGEN facts
-- like instr-count/branches stay on g++, never here).
--
--   Run: nvim --headless --clean -u NONE -l tools/emit_record_layout.lua <tu.cpp> [Struct ...]
--   Out: JSON { "<record>": { size, align, straddlers:[{name,off,size}] }, ... } on stdout.
--        (no [Struct] args → emit every non-noise record in the TU)

local script = vim.fn.resolve(arg[0] or "")
local ENGINE = vim.fn.fnamemodify(script, ":h:h")            -- tools/emit_record_layout.lua -> engine root
package.path = ENGINE .. "/tools/plugins/fox-symdeps.nvim/lua/?.lua;" .. package.path
local sizeprobe    = require("fox-symdeps.sizeprobe")
local recordlayout = require("fox-symdeps.recordlayout")

local tu = arg[1]
if not tu or tu == "" then io.stderr:write("usage: emit_record_layout.lua <tu.cpp> [Struct ...]\n"); os.exit(2) end
-- `--require-all`: a requested record that matched nothing becomes FATAL (see the check at the
-- tail). OPT-IN, deliberately. check_cache_layout.py batches ~193 record requests of which ~77
-- are legitimately absent from the TU (un-instantiated / unlinked) and it reports those as
-- "unpoliced, NOT verified" — that TU-scope honesty is the correct behaviour for a straddle gate
-- and making absence fatal by default silently converted it into "gate could not run", which is
-- strictly worse than either passing or failing. A COMPLEMENT consumer has the opposite need:
-- it subtracts a registry from a member list, so a missing record yields an empty member list
-- and a vacuously-clean verdict. Both are right for their caller; the caller chooses.
local wanted, any, require_all = {}, true, false
for i = 2, #arg do
  if arg[i] == "--require-all" then require_all = true
  else wanted[arg[i]] = true; any = false end
end

-- Reuse the plugin's compile-flag extraction (the SAME flags the HUD's size-probe uses).
local flags, dir = sizeprobe._flags_for(tu)
if not flags then io.stderr:write("no compile_commands flags for " .. tu .. "\n"); os.exit(2) end

-- clang for LAYOUT (D-321). Keep only the LAYOUT-relevant flags — `-I`/`-isystem`/`-D`/`-std`
-- (deduped) — and DROP codegen (`-O`/`-march`/`-flto`/`-funroll`/other `-f`): record layout is
-- ABI-determined (independent of optimization), and those g++ flags trip clang under
-- `-fsyntax-only`. This is the clang-portable layout-flag subset (TECH_DEBT-231; candidate to
-- promote into a shared `sizeprobe` clang-mode so HUD + CI share ONE filter).
local keep, have_std, i = {}, false, 1
while i <= #flags do
  local f = flags[i]
  if f == "-isystem" or f == "-include" then keep[#keep + 1] = f; keep[#keep + 1] = flags[i + 1] or ""; i = i + 1
  elseif f:match("^%-I") or f:match("^%-D") then keep[#keep + 1] = f
  elseif f:match("^%-std=") and not have_std then keep[#keep + 1] = f; have_std = true
  end
  i = i + 1
end
if not have_std then keep[#keep + 1] = "-std=gnu++20" end
local argv = { "clang++", "-fsyntax-only", "-ferror-limit=0", "-Xclang", "-fdump-record-layouts" }
vim.list_extend(argv, keep)
argv[#argv + 1] = vim.fn.fnamemodify(tu, ":p")   -- ABSOLUTE — cwd is the compile dir (build_clangd), not the TU's dir

local res = vim.system(argv, { cwd = dir, text = true }):wait()
if res.code ~= 0 then
  -- D-413/F3 RESOLUTION (empirically calibrated): clang rc!=0 is the STANDING condition on the
  -- real TU (benign dialect noise under the stripped clang flag subset — D-321) while the dump
  -- stays usable. A dumped record is COMPLETE-BY-CONSTRUCTION (clang only prints a layout it
  -- finished); the only rc-failure casualty is records MISSING from the dump — and those are
  -- POLICED downstream (check_cache_layout names them unpoliced, never counts them verified).
  -- So: tolerate + NOTE, never refuse (a blanket refusal broke the whole pipeline on rc=1 noise).
  io.stderr:write("note: clang rc=" .. tostring(res.code)
    .. " (dialect noise tolerated; dumped records are complete — missing ones surface as unpoliced)\n")
end
local dump = (res.stdout or "") .. (res.stderr or "")
local records = recordlayout.parse(dump)                     -- plugin parser (tested)
if #records == 0 then
  io.stderr:write("no record layouts in dump (clang failed? " .. tostring(res.code) .. ")\n")
  os.exit(2)
end

-- plugin straddle detector (tested) → straddlers + NAMED unverified fields (tri-state, D-413).
local strad = recordlayout.straddlers(records)
local strad_by, unv_by = {}, {}
for _, r in ipairs(strad.report or {}) do strad_by[r.name] = r.fields; unv_by[r.name] = r.unverified end

local out, matched = {}, {}
for _, r in ipairs(records) do
  local base = (r.name:gsub("<.*", ""))                      -- tt::ExecutionCore<64> -> tt::ExecutionCore
  local nons = (base:gsub("^.*::", ""))                      -- -> ExecutionCore (namespace-stripped)
  local tmpl = (r.name:gsub("^.*::", ""))                    -- -> ExecutionCore<64> (ns-stripped, TEMPLATE KEPT)
  local hit = wanted[r.name] or wanted[base] or wanted[nons] or wanted[tmpl]
  if any or hit then
    local rec = { size = r.size, align = r.align, straddlers = strad_by[r.name] or {} }
    local unv = unv_by[r.name]
    if unv and #unv > 0 then rec.partial = unv end   -- ADDITIVE key (D-413): named UNVERIFIED fields
    -- ADDITIVE key (E.1.2 D-421 step 2): the FULL member list, for COMPLEMENT consumers.
    -- The straddle gate asks "which fields cross a line" — a partition guard asks the opposite
    -- question, "which fields exist AT ALL", so it can subtract a coverage registry from the
    -- struct and demand the remainder be empty-or-declared. recordlayout.parse already carries
    -- r.fields; this only stops projecting it away. Emitted ONLY for explicitly-requested
    -- records: on a whole-TU dump (199 records here) it would be mostly noise for every
    -- existing consumer, and asking for a record by name is the signal that you want its detail.
    if hit then
      local mem = {}
      for _, f in ipairs(r.fields or {}) do
        mem[#mem + 1] = { name = f.name, type = f.type, off = f.off }
      end
      rec.members = mem
    end
    out[r.name] = rec
    for k in pairs(wanted) do
      if k == r.name or k == base or k == nons or k == tmpl then matched[k] = true end
    end
  end
end

-- Under `--require-all`, a REQUESTED record that matched nothing is an ERROR, never a silent
-- empty result (D-421 step 2). Found by walking into it: `NodeContext<64>` matched none of the
-- three then-supported forms (base strips `<64>`, so only the bare or fully-qualified spellings
-- worked) and the emitter answered `[]` with rc=0 — a consumer that trusted that would have
-- computed a complement over zero members and reported the struct fully covered. The `tmpl` form
-- above removes that particular trap; this makes any FUTURE spelling miss fatal for the consumers
-- that cannot survive one, while leaving the tolerant batch consumers alone.
local missing = {}
for k in pairs(wanted) do if not matched[k] then missing[#missing + 1] = k end end
if require_all and #missing > 0 then
  table.sort(missing)
  io.stderr:write("requested record(s) not found in dump: " .. table.concat(missing, ", ")
    .. "\n  (a record absent from the dump is NOT an empty record — refusing to emit a"
    .. " result that would read as 'no members'. Check the spelling against a full dump:"
    .. " run with no record args and look at the JSON keys.)\n")
  os.exit(2)
end

io.write(vim.json.encode(out))
io.write("\n")
