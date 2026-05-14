# LinkedIn Post: Mirror Drift

**Hook:** Why does your backtest say "Profit" but your live engine says "Flat"? Welcome to the world of **Mirror Drift**.

In complex systems, we often need the same logic in two places. In HFT, we calculate features in the Backtester (to train models) and in the Live Engine (to execute trades). 

**The Trap:** You copy-paste the formula. 
`double spread = (ask - bid) / mid;`

**The Reality:** 
One month later, someone "optimizes" the live version to use fixed-point math for speed. They use a slightly different rounding mode. Now, the live engine sees a spread of `0.000100` while the backtest saw `0.000101`. That 1-ULP (Unit in the Last Place) difference is enough to flip a model's prediction from "Buy" to "Hold."

You've just introduced a silent, systematic bias that no unit test will catch.

**The Fix: Single-Source-of-Truth Registries**

We extinguished this entire bug class by banning manual mirroring. 

1. **X-Macro Registries:** We define the feature's metadata, formula, and dependencies in a single macro row. 
2. **Auto-Generation:** That one row generates the C++ struct fields for the Live Engine, the JSON parser for the Backtester, and the validation logic for the GUI.
3. **Bit-Identical Testing:** We run "Cross-Architecture Parity" tests that feed the same raw bytes into both engines and assert that the output is bitwise identical.

**The Lesson:** If you have to write the same thing twice, you've already failed. Use code generation to turn "manual discipline" into "structural certainty."

#HFT #Cpp #SoftwareArchitecture #MachineLearning #MLOps #Programming
