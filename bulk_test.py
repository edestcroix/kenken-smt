#! /usr/bin/env python3

import os
import subprocess
import argparse
from kenken_src import parse_kenken, build_smt
from multiprocessing import Pool

from typing import List, Dict
from mdtable import TableMaker


PUZZLES = "puzzles/"
OUTDIR = "results/"
TEST_CMD = "mathsat -stats"
NUM_PROCESSES = 6
MULTIPROCESS_THRESHOLD = 50


TRACKED_STATISTICS = {
    "time-seconds": "Time (seconds)", # Don't remove this one
    # All others can be changed.
    "sat-restarts": "Sat Restarts",
    "sat-propagations": "Sat Propagations",
    "sat-theory-conflicts": "Sat Theory Conflicts",
    "euf-total-calls": "EUF Calls",
    "euf-conflicts": "EUF Conflicts",
    "la-total-calls": "LA Calls",
    "la-conflicts": "LA Conflicts",
    "la-implications": "LA Implications",
}


def validate_solution(solution_file, solution):
    parse_line = (
        lambda line: line.replace(")", "").replace("(", "").strip().split(" ")[1]
    )
    with open(solution_file, "r") as f:
        return (
            "".join(parse_line(line) for line in solution) == f.readlines()[1].strip()
        )


def parse_statisticts(lines: List[str]) -> Dict:
    # the statistics are a list of lines of the form:
    # :stat-name value
    # map this into a dict
    return dict(tuple(line[2:].split(" ")) for line in lines)


# Runs on the actual directory containing the puzzle_files.
# This function actually handles the files themselves.
# (The lowest level of the testing tree)
def test_puzzle_set(puzzles, directory):
    stats = []
    for puzzle_file, solution_file in puzzles:
        solution_file = directory + solution_file
        with open(directory + puzzle_file, "r") as f:
            stats.append([puzzle_file])
            puzzle = f.readlines()
        try:
            kenken = parse_kenken(puzzle[1:])
        except Exception:
            print(f"{directory}{puzzle_file}: Parsing failed")
            continue
        output = (
            subprocess.run(
                TEST_CMD,
                input=build_smt(kenken).encode("utf-8"),
                shell=True,
                capture_output=True,
            )
            .stdout.decode("utf-8")
            .splitlines()
        )
        # the output is two parts, the solved puzzle above the ";; statistics" line,
        # and the statistics below that line.
        if output[0] != "sat":
            print(f"{directory}{puzzle_file}: No solution found")
            continue
        stat_index = output.index(";; statistics")
        correctness = (
            "Correct"
            if validate_solution(solution_file, output[1:stat_index])
            else "Incorrect"
        )
        try:
            statistics = parse_statisticts(output[stat_index + 2 : -1])
            stats[-1].extend([statistics[stat] for stat in TRACKED_STATISTICS])
        except Exception:
            print(f"{directory}{puzzle_file}: Statistics parsing failed")
            statistics = {}

        print(
            f"{directory}{puzzle_file}: {correctness} solution found in {statistics['time-seconds']} seconds"
        )


    return stats


def main_puzzle_test(directory: str, limit) -> List:
    files = os.listdir(directory)
    # every other file is a solution
    puzzles = [
        f for f in files if f.endswith(".txt") and not f.endswith("solution.txt")
    ]
    solutions = [f for f in files if f.endswith("solution.txt")]
    puzzles = zip(puzzles, solutions)
    puzzles = sorted(puzzles, key=lambda x: int(x[0].split("-")[0]))

    # if limit is more than the threashold, divide the number of puzzles
    # into NUM_PROCESSES chunks, and run each chunk in a separate process.
    # This allows for even MORE number crunching. (Seriously, processing
    # and solving this many kenken puzzles is REALLY crunchy)
    if limit <= MULTIPROCESS_THRESHOLD:
        puzzles = puzzles[:limit]
        return test_puzzle_set(puzzles, directory)

    chunk_size = limit // NUM_PROCESSES
    chunks = [puzzles[i : i + chunk_size] for i in range(0, limit, chunk_size)]
    with Pool(NUM_PROCESSES) as p:
        stat_lists = p.starmap(
            test_puzzle_set,
            zip(chunks, [directory] * NUM_PROCESSES),
        )
        return [item for sublist in stat_lists for item in sublist]


def process_stats_list(stats: List):
    # each element of stats is
    # a list of the form:
    # puzzle, stat1, stat2, stat3, ...
    # for each stat, compute the average, max, and min

    
    overal_stats = []
    for i, stat_id in enumerate(TRACKED_STATISTICS):
        # for each puzzle in stats,
        # get the stat at index i+1
        
        # first, check if that index exists for every
        # element of stat
        filtered_stats = [puzzle for puzzle in stats if len(puzzle) > i + 1]
        stat_max = round(max(float(puzzle[i + 1] or 0.0) for puzzle in filtered_stats), 4)
        stat_min = round(min(float(puzzle[i + 1] or 0.0) for puzzle in filtered_stats), 4)
        stat_avg = round(sum(float(puzzle[i + 1] or 0.0) for puzzle in filtered_stats)/len(filtered_stats), 4)

        overal_stats.append((TRACKED_STATISTICS[stat_id], stat_avg, stat_min, stat_max))

    return overal_stats

# tests one of the a, adms, etc directories.
def test_puzzle_dir(directory, limit, subdir=None):
    # in the directory, there are subdirectories,
    # if subdir is None, test all subdirectories,
    # otehr wise test only the specified one
    print(f"Testing {directory}")
    dirname = directory.split("/")[-1]
    if subdir:
        stats = main_puzzle_test(f"{directory}/{subdir}/", limit)
        output_stat_table(stats,f"{dirname}-{subdir}", limit)
        return
    # if the limit is less then MULTIPROCESS_THRESHOLD,
    # multiprocess here instead of later.
    elif limit <= MULTIPROCESS_THRESHOLD:
        subdirs = os.listdir(directory)
        subdirs = [f"{directory}/{subdir}/" for subdir in subdirs]
        with Pool(NUM_PROCESSES) as p:
            stat_lists = p.starmap(
                main_puzzle_test,
                sorted(zip(subdirs, [limit] * NUM_PROCESSES)))
            
        for subdir, stats in zip(subdirs, stat_lists):
                out_name = subdir.split("/")[-2]
                output_stat_table(stats, f"{dirname}-{out_name}", limit)
    else:
        for subdir in os.listdir(directory):
            stats = main_puzzle_test(f"{directory}/{subdir}/", limit)
            output_stat_table(stats, f"{directory.replace('/', '-')}-{subdir}", limit)


def output_stat_table(stats, output_name, limit):
    table_maker = TableMaker(new_line=False)
    columns = ["Statistic", "Average", "Min", "Max"]
    try:
        overal_stats = [columns] + process_stats_list(stats)
    except Exception:
        print(f"Error processing statistics for {output_name}")
        return

    columns = ["Puzzle"] + [TRACKED_STATISTICS[stat] for stat in TRACKED_STATISTICS]

    stats = [columns] + stats
    with open(f"{OUTDIR}{output_name}.md", "w") as f:
        f.write(table_maker.table("Summary", overal_stats))
        f.write(table_maker.table(f"Results ({limit})", stats) + "\n")
    print(f"Testing Complete: Statistics written to {output_name}.md")


def main():
    parser = argparse.ArgumentParser(description="Test SMT solver on kenken puzzles")
    parser.add_argument("-d", "--dir", type=str, default="")
    parser.add_argument("-l", "--limit", type=int, default=10)
    parser.add_argument("-F", "--Fuck", type=bool, default=False)
    parser.add_argument("-D", "--top-dir", type=str, default="")
    args = parser.parse_args()

    # if the limit is less then the multiprocessing threshold,
    # start a new process for each directory instead.
    os.makedirs(OUTDIR, exist_ok=True)

    # don't run on the "dm" directory, because
    # it takes fucking forever.

    if args.top_dir:
        test_puzzle_dir(f"{PUZZLES}{args.top_dir}", args.limit, args.dir)
        return
    limit = args.limit
    if difficulty_dir := args.dir:
        directories = os.listdir(PUZZLES)
        directories = [f"{PUZZLES}{directory}/" for directory in directories if directory != "dm"]
        with Pool(NUM_PROCESSES) as p:
            p.starmap(test_puzzle_dir, zip(directories, [limit] * NUM_PROCESSES, [args.dir]*NUM_PROCESSES))
    else:
        for directory in os.listdir(PUZZLES):
            if directory != "dm":
                print(f"Testing {directory} puzzles")
                test_puzzle_dir(f"{PUZZLES}{directory}", limit, difficulty_dir)

    # only run the "dm" directory if the user really wants to.
    if args.Fuck:
        test_puzzle_dir(f"{PUZZLES}dm", limit, difficulty_dir)
    


if __name__ == "__main__":
    main()
