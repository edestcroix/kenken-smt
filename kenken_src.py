#! /usr/bin/env python3

from typing import List, Dict, Tuple, Union

Constraint = Tuple[Union[str, None], int]
Region = Tuple[Constraint, List[int]]
Kenken = Dict[str, Region]


# kenken2smt starts here 
def __parse_cell(kenken: Kenken, cell_num, cell):
    # each cell is r1.12*, for example..
    # the first value is the region,
    # and if there are values after the period,
    # this is the region constraint.
    if "." not in cell and cell.strip() not in kenken:
        raise ValueError(f"Error: region {cell.strip()} has no constraint")
    elif "." not in cell:
        region = cell.strip()
        kenken[cell.strip()][1].append(cell_num)
        return

    region, constraint = cell.strip().split(".")
    constraint = (
        (str(constraint[-1]), int(constraint[:-1]))
        if len(constraint) > 1
        else (None, int(constraint))
    )

    if region not in kenken and not constraint:
        raise ValueError(f"Error: region {region} has no constraint")
    elif region not in kenken:
        kenken[region] = (constraint, [cell_num])
    else:
        kenken[region][1].append(cell_num)


# For every cell, declare a variable and constrain it
# between 1 and 7.
def __cell_variables():
    return "".join(
        f"(declare-const V{i} Int)\n(assert (and (> V{i} 0) (< V{i} 8)))\n"
        for i in range(1, 50)
    )


# constrain each row and column to have unique values.
# (I.e no two cells in a row or column can have the same value)
def __row_col_uniqness():
    return "".join(
        f"(assert (distinct V{i} V{i + 1} V{i + 2} V{i + 3} V{i + 4} V{i + 5} V{i + 6}))\n"
        for i in range(1, 50, 7)
    ) + "".join(
        f"(assert (distinct V{i} V{i + 7} V{i + 14} V{i + 21} V{i + 28} V{i + 35} V{i + 42}))\n"
        for i in range(1, 8)
    )

# Create the constraints for each regions. There are three types.
# Division and subtraction are special cases, as they are not communative,
# and both directions must be checked.
# The default case simply asserts that the aritmatic operation is equal to the
# number.
# The last case is for single-cell regions, where there is no operation,
# and the constraint is simply that the cell must be a specific number.
def __gen_statement(op, num, cells):
    if op in ["-", "/"]:
        return f"(assert (or (= {num} ({op} V{cells[0]} V{cells[1]})) (= {num} ({op} V{cells[1]} V{cells[0]}))))\n"
    elif op:
        return f'(assert (= {num} ({op} {" ".join([f"V{cell}" for cell in cells])})))\n'
    else:
        return f"(assert (= {num} V{cells[0]}))\n"

 # to build the puzzle, track the regions and cells,
 # for each region, store the constraint and the cells
 # of the region.
def parse_kenken(puzzle: List[str]) -> Kenken:
    kenken = {}
    kenken_cells = [cell for row in puzzle for cell in row.split(",")]
    for cell_num, cell in enumerate(kenken_cells):
        __parse_cell(kenken, cell_num + 1, cell)

    return kenken

# assemble the full smt file.
def build_smt(kenken: Kenken):
    return (
        "(set-logic UFNIA)\n(set-option :produce-models true)\n(set-option :produce-assignments true)\n"
        + __cell_variables()
        + __row_col_uniqness()
        + "".join(__gen_statement(op, num, cells) for (op, num), cells in kenken.values())
        + "(check-sat)\n"
        + f"(get-value ({' '.join([f'V{i}' for i in range(1, 50)])}))\n"
        + "exit\n"
    )
#################################
# end of kenken2smt



# smt2kenken starts here
##################################
def parse_smt(smt):
    # remove all '(' and ')' characters. this leaves the line
    # as two numbers separated by a space. strip any spaces
    # off the ends. since the cells can only be between 1 and 7,
    # they are always single digits, so the last character left
    # at this point is the cell value.
    parse_line = (
        lambda line: line.replace(")", "").replace("(", "").strip()[-1]
    )
    # if there is more than one line, then there is a solution,
    if "sat" in smt[0]:
        # convert the input from mathsat into single string,
        # don't include the first line; it just says "sat".
        print("".join(parse_line(line) for line in smt[1:]))
    else:
        print("no solution found.")
