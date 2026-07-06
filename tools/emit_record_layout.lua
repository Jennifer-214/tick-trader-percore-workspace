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
local wanted, any = {}, true
for i = 2, #arg do wanted[arg[i]] = true; any = false end

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
local dump = (res.stdout or "") .. (res.stderr or "")
local records = recordlayout.parse(dump)                     -- plugin parser (tested)
if #records == 0 then
  io.stderr:write("no record layouts in dump (clang failed? " .. tostring(res.code) .. ")\n")
  os.exit(2)
end

-- plugin straddle detector (tested) → fields that cross a 64B line (false-sharing candidates).
local strad = recordlayout.straddlers(records)
local strad_by = {}
for _, r in ipairs(strad.report or {}) do strad_by[r.name] = r.fields end

local out = {}
for _, r in ipairs(records) do
  local base = (r.name:gsub("<.*", ""))                      -- tt::ExecutionCore<64> -> tt::ExecutionCore
  local nons = (base:gsub("^.*::", ""))                      -- -> ExecutionCore (namespace-stripped)
  if any or wanted[r.name] or wanted[base] or wanted[nons] then
    out[r.name] = { size = r.size, align = r.align, straddlers = strad_by[r.name] or {} }
  end
end
io.write(vim.json.encode(out))
io.write("\n")
