#! /usr/bin/env python3


from kenken_src import Kenken

# Both of these can be changed to adjust the output
SVG_SW = 6
SVG_CELL_SIZE = 120

# Changing these might break things
SVG_WIDTH = SVG_CELL_SIZE * 7
SVG_HEIGHT = SVG_CELL_SIZE * 7


def __neighbors_in_region(cell, region_cells):
    # return a tuple (left, right, up, down)
    # where each value is true if that
    # cell is in the same region as the
    # argument cell.

    # the right cell is 1 more than the argument cell
    # the left cell is 1 less than the argument cell
    # the up cell is 7 less than the argument cell
    # the down cell is 7 more than the argument cell
    left, right, up, down = False, False, False, False

    for region_cell in region_cells:
        if region_cell == cell + 1:
            right = True
        if region_cell == cell - 1:
            left = True
        if region_cell == cell - 7:
            up = True
        if region_cell == cell + 7:
            down = True

    return (left, right, up, down)
        

# define a function that takes the neighbor information
# from the previous function and x,y, width, height information,
# and creates an svg box where the borders are half the thickness
# on the sides with neighbors
def build_svg_box(x, y, w, h, neighbors, big_lines, small_lines):
    widths = [1 if neighbors[i] else SVG_SW for i in range(4)]
    fills = ["#B0B0B0" if neighbors[i] else "#000000" for i in range(4)]
    f_left, f_right, f_up, f_down = fills
    w_left, w_right, w_up, w_down = widths
    up = f'<line x1="{x}" y1="{y}" x2="{x+w}" y2="{y}" style="stroke:{f_up};stroke-width:{w_up}"/>\n'
    down = f'<line x1="{x}" y1="{y+h}" x2="{x+w}" y2="{y+h}" style="stroke:{f_down};stroke-width:{w_down}"/>\n'
    # make vertical lines just a bit longer so they line up with the edge of 
    # the thicker lines. Also, make sure the minimum y is ofst, so lines don't go off the top of the svg.
    ofst = SVG_SW/2
    left = f'<line x1="{x}" y1="{max(y-ofst, ofst)}" x2="{x}" y2="{y+h+ofst}" style="stroke:{f_left};stroke-width:{w_left}"/>\n'
    right = f'<line x1="{x+w}" y1="{max(y-ofst, ofst)}" x2="{x+w}" y2="{y+h+ofst}" style="stroke:{f_right};stroke-width:{w_right}"/>\n'
    for i, line in enumerate([left, right, up, down]):
        if neighbors[i]:
            small_lines.append(line)
        else:
            big_lines.append(line)


def build_svg(kenken: Kenken, solutions, puzzle_id, header):
    svg, sol = "", ""
    svg += f"""<svg width="{SVG_WIDTH}" height="{SVG_HEIGHT+40}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\n"""
    # draw a white background
    svg += f'<rect x="0" y="0" width="{SVG_WIDTH}" height="{SVG_HEIGHT+40}" style="fill:#ffffff;stroke-width:{SVG_SW};stroke:#000000"/>\n'
    big_lines, small_lines = [], []

    # pick a color for the region
    for _, ((op, num), cells) in kenken.items():
        for i, cell in enumerate(cells):
            left, right, up, down = __neighbors_in_region(cell, cells)

            # draw the border lines thinner for borders between cells
            # of the same region
            build_svg_box((cell-1)%7*SVG_CELL_SIZE, (cell-1)//7*SVG_CELL_SIZE, SVG_CELL_SIZE, SVG_CELL_SIZE, [left, right, up, down], big_lines, small_lines)

            #svg += f'<rect x="{(cell-1)%7*SVG_CELL_SIZE}" y="{(cell-1)//7*SVG_CELL_SIZE}" width="{SVG_CELL_SIZE}" height="{SVG_CELL_SIZE}" style="fill:{color};stroke-width:{SVG_SW};stroke:#000000"/>\n'
            if i == 0:
                # write the constraint in the first cell
                op = op.replace("/", "÷").replace("*", "×") if op else ""
                # set the text color to white if the background is dark
                svg += f'<text x="{(cell-1)%7*SVG_CELL_SIZE+10}" y="{(cell-1)//7*SVG_CELL_SIZE+20}" font-size="18" fill="#000000">{num}{op}</text>\n'

            solution = solutions[cell - 1]
            sol += f'<text x="{(cell-1)%7*SVG_CELL_SIZE+SVG_CELL_SIZE/2-16}" y="{(cell-1)//7*SVG_CELL_SIZE+SVG_CELL_SIZE/2+12}" font-size="48" fill="#000000">{solution}</text>\n'

    # all the smaller lines are added before the bigger ones,
    # so that the bigger lines are all drawn on top of the smaller
    # ones, because it looks better this way.
    svg += "".join(small_lines)
    svg += "".join(big_lines)

    svg += f'<text x="10" y="{SVG_HEIGHT+25}" font-size="18" fill="#000000">{header}</text>\n'
    with open(f"kenken-{puzzle_id}_sol.svg", "w") as f:
        f.write(svg)
        f.write(sol)
        f.write("</svg>")
    # write the header at the bottom
    svg += "</svg>"
    with open(f"kenken-{puzzle_id}.svg", "w") as f:
        f.write(svg)

