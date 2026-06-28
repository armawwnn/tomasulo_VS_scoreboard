"""
main.py
=======
supports three modes: (-m OR --mode)
  scoreboard  — run the Scoreboard simulator
  tomasulo    — run Tomasulo algorithm simulator
  compare     — run both and print a side-by-side comparison
-----------------
conf file: (-c)
----------------
asm file : (-a)
----------------
for help :
python main.py -h



usage
-----
    python main.py --config config.json --asm program.asm --mode scoreboard
    python main.py -c config.json -a program.asm -m tomasulo
    python main.py -c config.json -a program.asm -m compare
"""

import argparse

from scoreboard import run_scoreboard
from tomasulo import run_tomasulo
from asm_parser import load_config, load_assembly, assign_hardware_config
from compare_func import compare_results
from helper import  print_timing_summary

# handel comad line interface

def build_arg_parser():
    """
    build and return the argument parser for the simulator CLI.
    """
    ap = argparse.ArgumentParser(
        prog="simulator",
        description="Out-of-Order Simulator — Scoreboard & Tomasulo",
    )
    ap.add_argument(
        "--config", "-c",
        type=str,
        required=True,
        metavar="FILE",
        help="Path to the JSON hardware configuration file.",
    )
    ap.add_argument(
        "--asm", "-a",
        type=str,
        required=True,
        metavar="FILE",
        help="Path to the assembly instruction file.",
    )
    ap.add_argument(
        "--mode", "-m",
        type=str,
        choices=["scoreboard", "tomasulo", "compare"],
        required=True,
        help="Simulation mode: scoreboard | tomasulo | compare.",
    )
    return ap


#  MAIN

def main():
    args = build_arg_parser().parse_args()

    # Load inputs
    config      = load_config(args.config)
    raw_asm     = load_assembly(args.asm)
    instructions, func_unit = assign_hardware_config(raw_asm, config)

    #Run selected mode
    if args.mode == "scoreboard":
        timings = run_scoreboard(instructions, func_unit)
        print_timing_summary(timings, "SCOREBOARD")

    elif args.mode == "tomasulo":
        timings = run_tomasulo(instructions, func_unit)
        print_timing_summary(timings, "TOMASULO")

    elif args.mode == "compare":
        print("\n" + "═" * 60)
        print("  Running SCOREBOARD ...")
        print("═" * 60)
        timings_score = run_scoreboard(instructions, func_unit)

        print("\n" + "═" * 60)
        print("  Running TOMASULO ...")
        print("═" * 60)
        timings_tom = run_tomasulo(instructions, func_unit)

        compare_results(instructions, timings_score, timings_tom)


if __name__ == "__main__":
    main()
