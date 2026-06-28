# Out-of-Order Instruction Scheduling Simulator

A cycle-accurate simulator for two classic dynamic scheduling mechanisms:
**Scoreboarding** (CDC-6600) and **Tomasulo's Algorithm** (IBM 360/91).

Built as project for *Advanced Computer Architecture*

---

## Features

- **Scoreboard** — detects and stalls on RAW, WAR, and WAW hazards; maintains
  the Functional Unit Status Table and Register Result Table per cycle.
- **Tomasulo** — eliminates WAR and WAW via register renaming (RAT); models
  separate RS and FU counts per unit type; enforces the CDB N+1 timing rule.
- **Compare mode** — runs both algorithms on the same program and prints a
  side-by-side timing table, speedup ratio, and hazard analysis.
- **Assembly file parser** — reads a plain `.asm` file; hardware config is a
  JSON file, so no code changes are needed to try different programs.
- **Cycle-by-cycle output** — every clock cycle prints the Instruction Status
  Table, FU / RS Table, and Register Result / RAT.

---

