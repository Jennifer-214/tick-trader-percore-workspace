# LinkedIn Post: The Bug Where You Wire the Entry but Forget the Exit

**Hook:** The most dangerous code in your repository isn't the code that fails; it's the code that's "orphaned."

We've all been there: You're porting a feature from a legacy architecture to a new one. You wire up the initialization. You wire up the main logic loop. You test it, and it looks green.

But you forgot the **Exit Logic**. 

**The War Story:** 
In a recent refactor, we discovered that while our strategies were entering trades perfectly, they had stopped "Adapting" to market regime changes. The `Strategy_Adapt` calls had been silently orphaned during a sharded-engine port. The code compiled, the tests (which only checked entries) passed, but the engine was effectively flying blind to regime shifts.

**How We Fixed It Structurally:**
We didn't just patch the call site. We moved to a **Strategy Interface Contract** enforced by X-Macros.

1. **The Registry:** Every strategy is now defined in a single macro row: `X(StrategyName, Init, Adapt, Build, Exit)`.
2. **Auto-Dispatch:** The engine uses this registry to auto-generate the dispatch table. If a strategy is added, all five lifecycle stages are *automatically* wired.
3. **Orphan Audits:** We now use a custom tool to diff the call graph. If a lifecycle stage exists but isn't called by the engine, the build fails.

**The Lesson:** When a bug class keeps recurring, stop patching the instances. Change the architecture so the bug becomes physically impossible to write. 

#HFT #Cpp #SoftwareArchitecture #TechnicalDebt #SystemsEngineering #Programming
