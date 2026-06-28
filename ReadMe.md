# Out-of-Order Instruction Scheduling Simulator

Cycle-accurate simulator for **Scoreboarding** and **Tomasulo's Algorithm**.

---

## Project Structure

```
.
├── main.py              # CLI entry point
├── pipeline_common.py   # Shared helpers (FU lifecycle, sim state, display)
├── scoreboard.py        # Scoreboard algorithm
├── tomasulo.py          # Tomasulo's algorithm
├── asm_parser.py        # Assembly + JSON config loader
├── compare_func.py      # Side-by-side comparison report
├── helper.py            # Utility functions
├── output.py            # Output formatting
├── asm/                 # Assembly program files
└── conf/                # JSON hardware config files
```

---

## Installation

```bash
pip install tabulate
```

---

## Usage

```bash
python main.py --config conf/config.json --asm asm/program.asm --mode scoreboard
python main.py --config conf/config.json --asm asm/program.asm --mode tomasulo
python main.py --config conf/config.json --asm asm/program.asm --mode compare
```

---

## Input Format

**Assembly file** (`asm/program.asm`):
```asm
# Comments start with #
LOAD  R1, 0(R2)
MUL   R3, R1, R4
ADD   R5, R3, R6
SUB   R7, R8, R9
ADD   R10, R7, R1
STORE R10, 4(R2)
```

**Config file** (`conf/config.json`):
```json
{
    "functional_units": {
        "Integer": {"rs": 3, "fu": 2},
        "Mult":    {"rs": 2, "fu": 2},
        "Divide":  {"rs": 1, "fu": 1},
        "Memory":  {"rs": 2, "fu": 1}
    },
    "latencies": {
        "ADD": 2, "SUB": 2, "MUL": 10, "DIV": 40, "LOAD": 2, "STORE": 2
    },
    "fu_map": {
        "ADD": "Integer", "SUB": "Integer",
        "MUL": "Mult",    "DIV": "Divide",
        "LOAD": "Memory", "STORE": "Memory"
    }
}
```

> `functional_units` also accepts a simple format: `"Integer": 2`
> (sets both RS and FU count to 2).

---

## Algorithms

| | Scoreboard | Tomasulo |
|---|---|---|
| WAW | Issue stall | Eliminated (register rename) |
| WAR | Write-Back stall | Eliminated (Vj/Vk captured at Issue) |
| RAW | Read Operands stall | Wait for CDB broadcast |
| Structural | No free FU → stall | No free RS → stall |
| Stages | Write → Execute → Read → Issue | Write → Execute → Issue |
