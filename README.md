# SMT Conversion Scripts
For simplicity, all the code functionality is in `kenken_src.py`, and
the executable scripts import the necessary code. The implementation
of kenken2smt starts at `__parse_cell()` and ends at `build_smt()`,
and smt2kenken is just the `parse_smt()` function at the end.
Comments declare where the code blocks start and end. The reason
for this, is that removing the `.py` extensions from the files makes python
unable to import from the files, preventing the code from being imported into
the testing script, and from the puzzle parser being used by the pretty printer.
For consistency with other submissions, rather than leave the file extensions
I decided to do it this way.  
Both `kenken2smt` and `smt2kenken` consequentially require `kenken_src.py` in the
same directory to run.
## kenken2smt
`./kenken2smt` will run kenken2smt. It reads from stdin and writes to stdout.
## smt2kenken
`./smt2kenken` will run smt2kenken. It takes the output from mathsat  
and converts it into a single-line kenken solution. It will fail
if run on output generated by `mathsat -stats`. It is only 
able to read the default model output by `mathsat`.
# The Pretty Printer
The pretty printer `pp` imports from `kenken_src.py` and `kenken_svg.py`.
It takes the same input as `kenken2smt`. It reads and parses the same
input puzzles, and uses the puzzle ID in the file to get the solution
using the `fetch.sh` script provided, rather than solving it with mathsat.
It outputs two SVG images, `kenken-[PUZZLE_ID].svg` and `kenken-[PUZZLE_ID]_sol.svg`,
where PUZZLE_ID is the id from the file used to fetch the solution. It requires
`kenken_svg` and `fetch.sh` in the same directory to work.