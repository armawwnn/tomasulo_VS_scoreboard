from output import * #Display and Formatting





# ("MUL",0) -> {"name":"Mult1","fu_type":"Mult","busy":False,...
def make_fu(fu_type, index):
    return {
        "name":             f"{fu_type}{index + 1}",
        "fu_type":          fu_type,
        "busy":             False,
        "op":               None,
        "dest":             None,
        "src1":             None,
        "src2":             None,
        "qj":               None,   
        "qk":               None,   
        "cycles_remaining": 0,
        "exec_started":     False,
        "exec_start_cycle": None,
        "inst_idx":         None, # index of current inst
    }

# flat func units and index it
# {"Integer":2} -> [Integer1, Integer2]
def build_fu_instances(func_unit):
    instances = []
    for fu_type, spec in func_unit.items():
        count = spec if isinstance(spec, int) else spec["fu"]
        for idx in range(count):
            instances.append(make_fu(fu_type, idx))
    return instances

# flush fu
def reset_fu(fu):
    fu["busy"]             = False
    fu["op"]               = None
    fu["dest"]             = None
    fu["src1"]             = None
    fu["src2"]             = None
    fu["qj"]               = None
    fu["qk"]               = None
    fu["cycles_remaining"] = 0
    fu["exec_started"]     = False
    fu["exec_start_cycle"] = None
    fu["inst_idx"]         = None

#find whitch fu is not bussy
def find_free_fu(fu_instances, fu_type):
    return next(
        (fu for fu in fu_instances if fu["fu_type"] == fu_type and not fu["busy"]),
        None,
    )


# ── Simulation state ──────────────────────────────────────────────────────────
# n = number of instructions
# 3 - > {"timings":[{},{},{}], "issued":[False,False,False], ...}
#state of all instructions
def make_sim_state(n):
    return {
        "n":              n,
        "timings":        [{} for _ in range(n)],
        "issued":         [False] * n,
        "read_done":      [False] * n,
        "read_done_prev": [False] * n,
        "exec_done":      [False] * n,
        "written_back":   [False] * n,
    }

# if all WB == TRUE -> TRUE means finish
def all_done(state):
    return all(state["written_back"])


# ── Internal guard ────────────────────────────────────────────────────────────

def _active_fu(fu):
    return fu["busy"] and fu["inst_idx"] is not None


# RAW check
# fu["qj"] = MUL1 -> TRUE
def check_raw(fu):
    return (fu["qj"] is not None) or (fu["qk"] is not None)


#update exe 
# cycle ---
# if cycleremaining = 0 -> update timigsi -> True
def stage_execute(fu_instances, state, cycle):
    for fu in fu_instances:
        if not _active_fu(fu):
            continue
        i = fu["inst_idx"]
        if state["read_done"][i] and not state["exec_done"][i]:
            if not fu["exec_started"]:
                fu["exec_started"]             = True
                fu["exec_start_cycle"]         = cycle
                state["timings"][i]["Execute"] = cycle   # placeholder

            fu["cycles_remaining"] -= 1
            if fu["cycles_remaining"] == 0:
                state["exec_done"][i]          = True
                state["timings"][i]["Execute"] = exec_range_str(
                    fu["exec_start_cycle"], cycle
                )

#set read done 
# if qj & qk == None -> read_done i -> True
def stage_read_operands(fu_instances, state):
    for fu in fu_instances:
        if not _active_fu(fu):
            continue
        i = fu["inst_idx"]
        if state["issued"][i] and not state["read_done"][i]:
            if not check_raw(fu):
                state["read_done"][i] = True


