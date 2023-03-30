#! /usr/bin/env python3
from sys import stdin
import json
import subprocess
from kenken_src import parse_kenken
from kenken_svg import build_svg

def main():
    # read puzzle from stdin
    kenken_in = stdin.read().splitlines()
    header = kenken_in[0]
    puzzle_id = header.split(" ")[3]
    kenken = parse_kenken(kenken_in[1:])

    # run ./fetch.sh to get the puzzle
    print("Fetching puzzle...")
    puzzle = subprocess.run(["./fetch.sh", puzzle_id], capture_output=True)
    print("Done")
    data = json.loads(puzzle.stdout.decode("utf-8"))
    puzzle_grids = data["data"].splitlines()
    # the solutions are in the first grid, after the seconds line
    # convert the solution grid into a list of cells
    solution = [cell for row in puzzle_grids[1:8] for cell in row.strip().split(" ")]
    build_svg(kenken, solution, puzzle_id, header.replace("#kenken", ""))
    print(f"Kenken {puzzle_id} written to kenken-{puzzle_id}.svg")
    print(f"Kenken {puzzle_id} solution written to kenken-{puzzle_id}_sol.svg")


if __name__ == "__main__":
    main()
