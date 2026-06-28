from pipeline_common import (
    make_fu, reset_fu,
    make_sim_state, all_done,
    build_instruction_rows, print_table,
    exec_range_str, _active_fu,
)


#config normalisation 

def _normalise(func_unit):
    result = {}
    for fu_type, spec in func_unit.items():
        if isinstance(spec, int):
            result[fu_type] = {"rs": spec, "fu": spec}
        else:
            result[fu_type] = {"rs": spec["rs"], "fu": spec["fu"]}
    return result


# slot builders 

def _build_rs_slots(hw):
    slots = []
    for fu_type, counts in hw.items():
        for idx in range(counts["rs"]):
            rs = make_fu(fu_type, idx)
            rs["name"]      = f"RS_{fu_type}{idx + 1}"
            rs["executing"] = False
            rs["fu_name"]   = None
            slots.append(rs)
    return slots


def _build_fu_slots(hw):
    slots = []
    for fu_type, counts in hw.items():
        for idx in range(counts["fu"]):
            slots.append({
                "name":     f"FU_{fu_type}{idx + 1}",
                "fu_type":  fu_type,
                "busy":     False,
                "inst_idx": None,
                "rs_name":  None,
            })
    return slots


#finders 

def _free_rs(rs_slots, fu_type):
    return next(
        (rs for rs in rs_slots if rs["fu_type"] == fu_type and not rs["busy"]),
        None,
    )


def _free_fu(fu_slots, fu_type):
    return next(
        (fu for fu in fu_slots if fu["fu_type"] == fu_type and not fu["busy"]),
        None,
    )


# register file 

def _make_reg_file(instructions):
    regs = set()
    for inst in instructions:
        for key in ("dest", "src1", "src2"):
            val = inst.get(key)
            if val and "(" not in val:   # skip address expressions like '0(R2)'
                regs.add(val)
    return {r: r for r in regs}


# ── RS assignment at Issue time ───────────────────────────────────────────────

def _assign_rs(rs, inst, inst_idx, rat, reg_file):
    src1 = inst.get("src1")
    src2 = inst.get("src2")

    rs["busy"]             = True
    rs["op"]               = inst["op"]
    rs["dest"]             = inst.get("dest")
    rs["src1"]             = src1
    rs["src2"]             = src2
    rs["cycles_remaining"] = inst["latency"]
    rs["exec_started"]     = False
    rs["exec_start_cycle"] = None
    rs["inst_idx"]         = inst_idx
    rs["executing"]        = False
    rs["fu_name"]          = None

    # src1
    if src1 is None or "(" in src1:
        rs["vj"], rs["qj"] = src1, None
    elif src1 in rat:
        rs["vj"], rs["qj"] = None, rat[src1]
    else:
        rs["vj"], rs["qj"] = reg_file.get(src1, src1), None

    # src2
    if src2 is None or "(" in src2:
        rs["vk"], rs["qk"] = src2, None
    elif src2 in rat:
        rs["vk"], rs["qk"] = None, rat[src2]
    else:
        rs["vk"], rs["qk"] = reg_file.get(src2, src2), None


def _reset_rs(rs):
    reset_fu(rs)
    rs["vj"] = None
    rs["vk"] = None
    rs["executing"] = False
    rs["fu_name"]   = None



def _broadcast_cdb(done_rs, rs_slots, rat, state):
    result = done_rs["name"]   # symbolic value — just the RS name token

    for rs in rs_slots:
        if not rs["busy"] or rs["inst_idx"] is None:
            continue
        j = rs["inst_idx"]

        if rs["qj"] == done_rs["name"]:
            rs["vj"], rs["qj"] = result, None
        if rs["qk"] == done_rs["name"]:
            rs["vk"], rs["qk"] = result, None

        # Both operands ready → eligible to execute NEXT cycle
        if rs["busy"] and rs["qj"] is None and rs["qk"] is None:
            if not state["read_done"][j]:
                state["read_done"][j] = True

    dest = done_rs["dest"]
    if dest is not None and rat.get(dest) == done_rs["name"]:
        del rat[dest]



def _rs_rows(rs_slots):
    return [
        {
            "RS":        rs["name"],
            "Busy":      "Yes",
            "Op":        rs["op"]       or "",
            "Dest":      rs["dest"]     or "",
            "Vj":        rs.get("vj")  or "",
            "Vk":        rs.get("vk")  or "",
            "Qj":        rs["qj"]       or "",
            "Qk":        rs["qk"]       or "",
            "Executing": "Yes" if rs["executing"] else "No",
        }
        for rs in rs_slots if rs["busy"]
    ]


def _fu_rows(fu_slots):
    return [
        {"FU": fu["name"], "Busy": "Yes", "RS": fu["rs_name"] or ""}
        for fu in fu_slots if fu["busy"]
    ]


def _print_state(cycle, instructions, state, rs_slots, fu_slots, rat):
    print(f"\n{'='*30} CYCLE {cycle} {'='*30}")

    print("\n[Instruction Status Table]")
    print_table(build_instruction_rows(instructions, state), "grid")

    print("\n[Reservation Station Table]")
    print_table(_rs_rows(rs_slots), "grid")

    fu_table = _fu_rows(fu_slots)
    if fu_table:
        print("\n[Functional Unit Slots]")
        print_table(fu_table, "simple")

    print("\n[Register Alias Table (RAT)]")
    rat_rows = [{"Register": r, "Producer RS": v} for r, v in sorted(rat.items())]
    print_table(rat_rows, "simple")

    print("=" * 71)



def _stage_write_back(rs_slots, state, rat, cycle):
    for rs in rs_slots:
        if not rs["busy"] or rs["inst_idx"] is None:
            continue
        i = rs["inst_idx"]
        if state["exec_done"][i] and not state["written_back"][i]:
            state["written_back"][i]            = True
            state["timings"][i]["Write Result"] = cycle
            _broadcast_cdb(rs, rs_slots, rat, state)
            _reset_rs(rs)


def _stage_execute(rs_slots, fu_slots, state, cycle):

    # step 1:
    for rs in rs_slots:
        if not rs["busy"] or rs["inst_idx"] is None:
            continue
        i = rs["inst_idx"]
        if state["read_done_prev"][i] and not rs["executing"] and not state["exec_done"][i]:
            fu = _free_fu(fu_slots, rs["fu_type"])
            if fu is not None:
                rs["executing"]        = True
                rs["exec_started"]     = True
                rs["exec_start_cycle"] = cycle
                rs["fu_name"]          = fu["name"]
                fu["busy"]             = True
                fu["inst_idx"]         = i
                fu["rs_name"]          = rs["name"]
                state["timings"][i]["Execute"] = cycle   # placeholder

    # step 2
    for rs in rs_slots:
        if not rs["busy"] or not rs["executing"] or rs["inst_idx"] is None:
            continue
        i = rs["inst_idx"]
        if state["exec_done"][i]:
            continue

        rs["cycles_remaining"] -= 1
        if rs["cycles_remaining"] == 0:
            state["exec_done"][i]          = True
            state["timings"][i]["Execute"] = exec_range_str(
                rs["exec_start_cycle"], cycle
            )

            fu = next((f for f in fu_slots if f["rs_name"] == rs["name"]), None)
            if fu is not None:
                fu["busy"] = False
                fu["inst_idx"] = None
                fu["rs_name"]  = None
            rs["fu_name"] = None


def _stage_issue(instructions, next_issue_idx, rs_slots, state, rat, reg_file, cycle):
    if next_issue_idx >= len(instructions):
        return next_issue_idx

    inst = instructions[next_issue_idx]
    rs   = _free_rs(rs_slots, inst["fu_type"])

    if rs is None:
        return next_issue_idx   # structural stall

    i = next_issue_idx
    state["issued"][i]           = True
    state["timings"][i]["Issue"] = cycle

    _assign_rs(rs, inst, i, rat, reg_file)

    dest = inst.get("dest")
    if dest is not None:
        rat[dest] = rs["name"]   # rename

    # If all operands were ready at Issue time ==> mark read_done
    if rs["qj"] is None and rs["qk"] is None:
        state["read_done"][i] = True

    return next_issue_idx + 1



def run_tomasulo(instructions, func_unit):
    hw             = _normalise(func_unit)
    state          = make_sim_state(len(instructions))
    rs_slots       = _build_rs_slots(hw)
    fu_slots       = _build_fu_slots(hw)
    rat            = {}   
    reg_file       = _make_reg_file(instructions)
    next_issue_idx = 0
    cycle          = 0

    while not all_done(state) and cycle < 500:
        cycle += 1

        state["read_done_prev"] = list(state["read_done"])

        _stage_write_back(rs_slots, state, rat, cycle)
        _stage_execute(rs_slots, fu_slots, state, cycle)
        next_issue_idx = _stage_issue(
            instructions, next_issue_idx, rs_slots, state, rat, reg_file, cycle
        )

        _print_state(cycle, instructions, state, rs_slots, fu_slots, rat)

    print(f"\n  Simulation finished in {cycle} cycle(s).\n")
    return state["timings"]


# test


# if __name__ == "__main__":
#     instructions = [
#         {"op": "LOAD",  "dest": "R1",  "src1": "0(R2)", "src2": None,    "latency": 2,  "fu_type": "Memory"},
#         {"op": "MUL",   "dest": "R3",  "src1": "R1",    "src2": "R4",    "latency": 10, "fu_type": "Mult"},
#         {"op": "ADD",   "dest": "R5",  "src1": "R3",    "src2": "R6",    "latency": 2,  "fu_type": "Integer"},
#         {"op": "SUB",   "dest": "R7",  "src1": "R8",    "src2": "R9",    "latency": 2,  "fu_type": "Integer"},
#         {"op": "ADD",   "dest": "R10", "src1": "R7",    "src2": "R1",    "latency": 2,  "fu_type": "Integer"},
#         {"op": "STORE", "dest": None,  "src1": "R10",   "src2": "4(R2)", "latency": 2,  "fu_type": "Memory"},
#     ]
#     func_unit = {
#         "Integer": {"rs": 3, "fu": 2},
#         "Mult":    {"rs": 2, "fu": 2},
#         "Divide":  {"rs": 1, "fu": 1},
#         "Memory":  {"rs": 2, "fu": 1},
#     }
#     run_tomasulo(instructions, func_unit)
