
from tabulate import tabulate



def _total_cycles(timings):
    cycles = [t.get("Write Result", 0) for t in timings if t.get("Write Result")]
    return max(cycles) if cycles else 0


def _avg_cpi(timings):
    n = len(timings)
    if n == 0:
        return 0.0
    return _total_cycles(timings) / n


def _speedup(cycles_score, cycles_tom):
    if cycles_score == 0 or cycles_tom == 0:
        return "N/A"
    return round(cycles_score / cycles_tom, 2)



def build_comparison_table(instructions, timings_score, timings_tom):
    rows = []
    for i, inst in enumerate(instructions):
        op   = inst.get("op", "")
        dest = inst.get("dest", "")
        label = f"{op} {dest}".strip() if dest else op

        ts = timings_score[i] if i < len(timings_score) else {}
        tt = timings_tom[i]   if i < len(timings_tom)   else {}

        sb_write  = ts.get("Write Result", "")
        tom_write = tt.get("Write Result", "")

        if isinstance(sb_write, int) and isinstance(tom_write, int):
            delta = sb_write - tom_write
            delta_str = f"+{delta}" if delta > 0 else str(delta)
        else:
            delta_str = "—"

        rows.append({
            "Instruction":   label,
            "SB Issue":      ts.get("Issue",        ""),
            "SB Execute":    ts.get("Execute",      ""),
            "SB Write":      sb_write,
            "TOM Issue":     tt.get("Issue",        ""),
            "TOM Execute":   tt.get("Execute",      ""),
            "TOM Write":     tom_write,
            "delta Write":       delta_str,
        })
    return rows



def detect_stalls(instructions, timings):
    stalls = []
    for i in range(1, len(timings)):
        prev_issue = timings[i - 1].get("Issue")
        curr_issue = timings[i].get("Issue")
        if isinstance(prev_issue, int) and isinstance(curr_issue, int):
            gap = curr_issue - prev_issue
            if gap > 1:
                op   = instructions[i].get("op", "?")
                dest = instructions[i].get("dest", "")
                label = f"{op} {dest}".strip() if dest else op
                stalls.append(
                    f"  I{i+1} ({label}): Issue delayed by {gap-1} cycle(s) "
                    f"(stall between cycle {prev_issue} and {curr_issue})"
                )
    return stalls



def compare_results(instructions, timings_score, timings_tom):
    cycles_score = _total_cycles(timings_score)
    cycles_tom   = _total_cycles(timings_tom)
    speedup      = _speedup(cycles_score, cycles_tom)

    sep = "═" * 80

    print(f"\n{sep}")
    print("  COMPARISON: Scoreboard (SB) vs Tomasulo (TOM) — Per-Instruction Timing")
    print(sep)
    rows = build_comparison_table(instructions, timings_score, timings_tom)
    print(tabulate(rows, headers="keys", tablefmt="grid"))

    print(f"\n{sep}")
    print("  SUMMARY")
    print(sep)
    summary = [
        {"Metric":           "Total cycles",
         "Scoreboard":       cycles_score,
         "Tomasulo":         cycles_tom,
         "Winner":           "Tomasulo" if cycles_tom < cycles_score
                             else ("Scoreboard" if cycles_score < cycles_tom
                                   else "Tie")},
        {"Metric":           "Average CPI",
         "Scoreboard":       round(_avg_cpi(timings_score), 2),
         "Tomasulo":         round(_avg_cpi(timings_tom), 2),
         "Winner":           ""},
        {"Metric":           "Tomasulo speedup",
         "Scoreboard":       "—",
         "Tomasulo":         f"{speedup}*",
         "Winner":           ""},
    ]
    print(tabulate(summary, headers="keys", tablefmt="simple"))

    print(f"\n{sep}")
    print("  STALL ANALYSIS")
    print(sep)

    sb_stalls  = detect_stalls(instructions, timings_score)
    tom_stalls = detect_stalls(instructions, timings_tom)

    print("\nScoreboard issue stalls (RAW / WAW / structural):")
    if sb_stalls:
        for s in sb_stalls:
            print(s)
    else:
        print("  None detected.")

    print("\nTomasulo issue stalls (structural only — WAW/WAR eliminated by renaming):")
    if tom_stalls:
        for s in tom_stalls:
            print(s)
    else:
        print("  None detected.")

    print(f"\n{sep}")
    print("  KEY ALGORITHMIC DIFFERENCES")
    print(sep)
    print(sep)
