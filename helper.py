def print_timing_summary(timings, mode_label):
    """
    Print the final instruction timing table returned by a simulator.
    """
    sep = "─" * 60
    print(f"\n{sep}")
    print(f"  {mode_label} — Final Instruction Timing")
    print(sep)
    total = max(
        (t.get("Write Result", 0) for t in timings if t.get("Write Result")),
        default=0,
    )
    for i, t in enumerate(timings):
        issue   = t.get("Issue",        "—")
        execute = t.get("Execute",      "—")
        write   = t.get("Write Result", "—")
        print(f"  I{i+1:>2}: Issue={issue:<4}  Execute={str(execute):<8}  Write={write}")
    print(sep)
    print(f"  Total cycles: {total}")
    print(sep)





#formatting 

def exec_range_str(start, end):
    """Return '5' for a single-cycle op, '5-8' for a multi-cycle op."""
    return str(start) if start == end else f"{start}-{end}"


def format_instruction(inst):
    """Return a display string like 'ADD R1, R2, R3' for an instruction dict."""
    parts = [str(inst[k]) for k in ("dest", "src1", "src2") if inst.get(k)]
    return f"{inst['op']} {', '.join(parts)}" if parts else inst["op"]


