from pipeline_common import (
    build_fu_instances, reset_fu, find_free_fu,
    make_sim_state, all_done,
    check_raw, stage_execute, stage_read_operands,
    build_instruction_rows, build_reg_rows, print_table, print_simulation_state,
    _active_fu,
)



def check_waw(dest, reg_result):
    return dest is not None and dest in reg_result


def check_war(fu, fu_instances, state):
    dest = fu["dest"]
    if dest is None:
        return False

    for other in fu_instances:
        if not _active_fu(other) or other["inst_idx"] == fu["inst_idx"]:
            continue
        j = other["inst_idx"]
        if state["issued"][j] and not state["read_done"][j]:
            reads_old_value = (
                (other["src1"] == dest and other["qj"] != fu["name"])
                or
                (other["src2"] == dest and other["qk"] != fu["name"])
            )
            if reads_old_value:
                return True

    return False



def assign_fu_scoreboard(fu, inst, inst_idx, reg_result):
    src1 = inst.get("src1")
    src2 = inst.get("src2")

    fu["busy"]             = True
    fu["op"]               = inst["op"]
    fu["dest"]             = inst.get("dest")
    fu["src1"]             = src1
    fu["src2"]             = src2
    fu["qj"]               = reg_result.get(src1) if src1 else None
    fu["qk"]               = reg_result.get(src2) if src2 else None
    fu["cycles_remaining"] = inst["latency"]
    fu["exec_started"]     = False
    fu["exec_start_cycle"] = None
    fu["inst_idx"]         = inst_idx


def broadcast_writeback(done_fu, fu_instances):
    for other in fu_instances:
        if other["qj"] == done_fu["name"]:
            other["qj"] = None
        if other["qk"] == done_fu["name"]:
            other["qk"] = None


def build_fu_rows_scoreboard(fu_instances):
    return [
        {
            "Name": fu["name"],
            "Busy": "Yes",
            "Op":   fu["op"]  or "",
            "Qj":   fu["qj"] or "",
            "Qk":   fu["qk"] or "",
        }
        for fu in fu_instances if fu["busy"]
    ]



def stage_write_back_scoreboard(fu_instances, state, reg_result, cycle):
    for fu in fu_instances:
        if not _active_fu(fu):
            continue
        i = fu["inst_idx"]
        if state["exec_done"][i] and not state["written_back"][i]:
            if not check_war(fu, fu_instances, state):
                state["written_back"][i]            = True
                state["timings"][i]["Write Result"] = cycle

                dest = fu["dest"]
                if dest is not None and reg_result.get(dest) == fu["name"]:
                    del reg_result[dest]

                broadcast_writeback(fu, fu_instances)
                reset_fu(fu)


def stage_issue_scoreboard(instructions, next_issue_idx, fu_instances,
                           state, reg_result, cycle):
    if next_issue_idx >= len(instructions):
        return next_issue_idx

    inst    = instructions[next_issue_idx]
    dest    = inst.get("dest")
    free_fu = find_free_fu(fu_instances, inst["fu_type"])

    if free_fu is None or check_waw(dest, reg_result):
        return next_issue_idx   # stall

    i = next_issue_idx
    state["issued"][i]           = True
    state["timings"][i]["Issue"] = cycle

    assign_fu_scoreboard(free_fu, inst, i, reg_result)

    if dest is not None:
        reg_result[dest] = free_fu["name"]

    return next_issue_idx + 1



def run_scoreboard(instructions, func_unit):
    state          = make_sim_state(len(instructions))
    fu_instances   = build_fu_instances(func_unit)
    reg_result     = {}   # {register: FU_name}
    next_issue_idx = 0
    cycle          = 0

    while not all_done(state) and cycle < 500:
        cycle += 1

        stage_write_back_scoreboard(fu_instances, state, reg_result, cycle)
        stage_execute(fu_instances, state, cycle)
        stage_read_operands(fu_instances, state)
        next_issue_idx = stage_issue_scoreboard(
            instructions, next_issue_idx, fu_instances, state, reg_result, cycle
        )

        print_simulation_state(
            cycle, instructions, state, fu_instances,
            reg_result, build_fu_rows_scoreboard(fu_instances)
        )

    print(f"\n Simulation finished in {cycle} cycle(s).\n")
    return state["timings"]

