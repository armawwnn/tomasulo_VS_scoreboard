import json
import re

#read conf file
# conf/conf.json -> 

#"functional_units": {...}, "latencies": {...}, 
#"fu_map": {...}}

def load_config(path):
    with open(path, "r") as f:
        return json.load(f)



#tokenizer
# add R1,R2,R3 --> ["ADD", "R1","R2","R3"]

def load_assembly(path):
    instructions = []
    with open(path, "r") as f:
        for raw_line in f:
            line = raw_line.split("#")[0].strip()   # strip comments
            if not line:
                continue
            # split on whitespace and commas
            tokens = [t.strip() for t in re.split(r"[\s,]+", line) if t.strip()]
            if tokens:
                instructions.append(tokens)
    return instructions

# out of 2 above func tokens + conf->
# {"op":"ADD","dest":"R1","src1":"R2","src2":"R3",
#"latency":2,"fu_type":"Integer"}

def assign_hardware_config(raw_instructions, config):
    latencies = {k.upper(): v for k, v in config["latencies"].items()}
    fu_map    = {k.upper(): v for k, v in config["fu_map"].items()}
    func_unit = config["functional_units"]

    instructions = []
    for tokens in raw_instructions:
        op = tokens[0].upper()

        if op not in latencies:
            raise ValueError(
                f"Unknown opcode '{op}'. Add it to config['latencies']."
            )
        if op not in fu_map:
            raise ValueError(
                f"Unknown opcode '{op}'. Add it to config['fu_map']."
            )

        if op == "STORE":
            dest = None
            src1 = tokens[1] if len(tokens) > 1 else None
            src2 = tokens[2] if len(tokens) > 2 else None
        else:
            dest = tokens[1] if len(tokens) > 1 else None
            src1 = tokens[2] if len(tokens) > 2 else None
            src2 = tokens[3] if len(tokens) > 3 else None

        instructions.append({
            "op":      op,
            "dest":    dest,
            "src1":    src1,
            "src2":    src2,
            "latency": latencies[op],
            "fu_type": fu_map[op],
        })

    return instructions, func_unit
