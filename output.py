from tabulate import tabulate
from helper import *

# ── Display helpers ───────────────────────────────────────────────────────────

def print_table(data, fmt):
    """Print a tabulate table, or 'No Data' when the list is empty."""
    print(tabulate(data, headers="keys", tablefmt=fmt) if data else "No Data")


def build_instruction_rows(instructions, state):
    """Build the rows for the Instruction Status Table."""
    return [
        {
            "Instruction":  format_instruction(inst),
            "Issue":        state["timings"][i].get("Issue",        ""),
            "Execute":      state["timings"][i].get("Execute",      ""),
            "Write Result": state["timings"][i].get("Write Result", ""),
        }
        for i, inst in enumerate(instructions)
    ]


def build_reg_rows(reg_result):
    """
    Build rows for the Register Result / RAT table.
    """
    return [{"Register": r, "FU": f} for r, f in sorted(reg_result.items())]


def print_simulation_state(cycle, instructions, state, fu_instances,reg_result, fu_rows):
    print(f"\n{'='*30} CYCLE {cycle} {'='*30}")

    print("\n[Instruction Status Table]")
    print_table(build_instruction_rows(instructions, state), "grid")

    print("\n[Functional Unit Status Table]")
    print_table(fu_rows, "grid")

    print("\n[Register Result Status Table]")
    print_table(build_reg_rows(reg_result), "simple")

    print("=" * 71)
