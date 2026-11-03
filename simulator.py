"""Topic F: a small, turn-based pursuit-evasion grid simulator."""
import argparse
import heapq
import random

MAP = (
    "###############",
    "#.............#",
    "#...#.....#...#",
    "#...#.....#...#",
    "#...###...#...#",
    "#.............#",
    "#......#......#",
    "#......#......#",
    "#..##..#..##..#",
    "#.............#",
    "#...#.....#...#",
    "#.............#",
    "###############",
)
START_EVADER = (7, 5)
START_PURSUERS = [(1, 1), (13, 1), (7, 11)]
# Fixed ordering makes ties predictable: up, right, down, left.
DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
STRATEGIES = ("random", "greedy", "astar")


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def is_open(position):
    x, y = position
    return 0 <= y < len(MAP) and 0 <= x < len(MAP[0]) and MAP[y][x] != "#"


def neighbours(position):
    x, y = position
    return [(x + dx, y + dy) for dx, dy in DIRECTIONS if is_open((x + dx, y + dy))]


def astar_path(start, goal, blocked=()):
    """Return a shortest path including start and goal; [] means unreachable."""
    blocked = set(blocked)
    if start in blocked or goal in blocked:
        return []
    frontier = [(manhattan(start, goal), 0, start)]
    previous = {start: None}
    cost = {start: 0}
    while frontier:
        _, distance, current = heapq.heappop(frontier)
        if distance != cost[current]:
            continue
        if current == goal:
            path = []
            while current is not None:
                path.append(current)
                current = previous[current]
            return path[::-1]
        for next_cell in neighbours(current):
            if next_cell in blocked:
                continue
            new_cost = distance + 1
            if new_cost < cost.get(next_cell, float("inf")):
                cost[next_cell] = new_cost
                previous[next_cell] = current
                priority = new_cost + manhattan(next_cell, goal)
                heapq.heappush(frontier, (priority, new_cost, next_cell))
    return []


class Simulation:
    def __init__(self, evader_strategy="greedy", pursuer_strategy="astar", seed=0, max_steps=200):
        self.evader_strategy = evader_strategy
        self.pursuer_strategy = pursuer_strategy
        self.rng = random.Random(seed)
        self.max_steps = max_steps
        self.evader = START_EVADER
        self.pursuers = list(START_PURSUERS)
        self.steps = 0
        self.status = "running"

    def choose_evader_move(self):
        # Staying is legal. Moving onto a pursuer is not legal for the evader.
        moves = [p for p in neighbours(self.evader) + [self.evader] if p not in self.pursuers]
        if self.evader_strategy == "random":
            return self.rng.choice(moves)
        if self.evader_strategy == "greedy":
            # Hand-crafted rule: maximise distance from the nearest pursuer.
            return max(moves, key=lambda p: min(manhattan(p, enemy) for enemy in self.pursuers))
        # A*-distance evasion: account for walls when measuring danger.
        # This is a hand-crafted escape rule using A*, not an optimal game solver.
        def safety(cell):
            distances = []
            for enemy in self.pursuers:
                path = astar_path(enemy, cell)
                distances.append(len(path) - 1 if path else float("inf"))
            return min(distances)
        return max(moves, key=safety)

    def choose_pursuer_move(self, index):
        current = self.pursuers[index]
        occupied = set(self.pursuers[:index] + self.pursuers[index + 1:])
        moves = [p for p in neighbours(current) + [current] if p not in occupied]
        if self.pursuer_strategy == "random":
            return self.rng.choice(moves)
        if self.pursuer_strategy == "greedy":
            return min(moves, key=lambda p: manhattan(p, self.evader))
        path = astar_path(current, self.evader, occupied)
        return path[1] if len(path) > 1 else current

    def step(self):
        if self.status != "running":
            return
        self.steps += 1
        self.evader = self.choose_evader_move()
        for index in range(len(self.pursuers)):
            self.pursuers[index] = self.choose_pursuer_move(index)
            if self.pursuers[index] == self.evader:
                self.status = "captured"
                return
        if self.steps >= self.max_steps:
            self.status = "escaped"


def run_gui(args):
    """Canvas-drawn characters keep the demo portable: no image files needed."""
    import tkinter as tk
    from tkinter import ttk
    root = tk.Tk()
    root.title("Ghost Run | Topic F")
    root.configure(bg="#100f1b")
    root.resizable(False, False)
    bg, panel, muted = "#100f1b", "#1c192c", "#aba3bf"
    orange, mint = "#ff9b45", "#a9f5df"
    evader_choice = tk.StringVar(value=args.evader)
    pursuer_choice = tk.StringVar(value=args.pursuers)
    status_text = tk.StringVar()
    detail_text = tk.StringVar()
    turns_text = tk.StringVar()
    playing = False
    sim = None
    trails = []

    header = tk.Frame(root, bg=bg, padx=22, pady=16)
    header.pack(fill="x")
    tk.Label(header, text="GHOST RUN", font=("Helvetica", 26, "bold"), fg=mint, bg=bg).pack(anchor="w")
    tk.Label(header, text="A haunted pursuit-evasion arena  /  TOPIC F", font=("Helvetica", 11), fg=muted, bg=bg).pack(anchor="w", pady=(4, 0))
    body = tk.Frame(root, bg=bg, padx=22)
    body.pack()
    cell = 38
    width, height = len(MAP[0]) * cell, len(MAP) * cell
    canvas = tk.Canvas(body, width=width, height=height, bg=panel, highlightthickness=1, highlightbackground="#4e3a67")
    canvas.pack(side="left")
    side = tk.Frame(body, bg=panel, width=232, height=height, padx=18, pady=18)
    side.pack(side="left", padx=(14, 0), fill="y")
    side.pack_propagate(False)

    def label(text, color=muted, size=10, bold=False):
        widget = tk.Label(side, text=text, fg=color, bg=panel, font=("Helvetica", size, "bold" if bold else "normal"), justify="left", anchor="w", wraplength=196)
        widget.pack(anchor="w", fill="x", pady=(0, 6))
        return widget

    label("LIVE MATCH", orange, 10, True)
    state_label = label("", mint, 18, True)
    state_label.configure(textvariable=status_text)
    turns_label = label("", "#f3eefb", 12)
    turns_label.configure(textvariable=turns_text)
    progress = tk.Canvas(side, width=190, height=5, bg="#373047", highlightthickness=0)
    progress.pack(anchor="w", pady=(0, 18))
    label("THE CAST", orange, 10, True)
    label("GHOST / Evader", mint, 12, True)
    label("Find space. Survive the hunt.")
    label("GHOSTS / Pursuers 1-3", orange, 12, True)
    label("Chase the ghost through the maze.")
    label("STRATEGIES", orange, 10, True)
    label("Ghost", mint)
    ttk.Combobox(side, textvariable=evader_choice, values=STRATEGIES, state="readonly", width=19).pack(anchor="w", pady=(0, 10))
    label("Orange ghost hunters", orange)
    ttk.Combobox(side, textvariable=pursuer_choice, values=STRATEGIES, state="readonly", width=19).pack(anchor="w", pady=(0, 10))
    label("Press Reset / Apply after changing strategies.", muted, 9)

    def draw_ghost(cx, cy, color, number=None):
        # The same playful ghost silhouette for both teams, in two colours.
        glow = "#22423f" if number is None else "#4b2c2b"
        canvas.create_oval(cx-18, cy-17, cx+18, cy+18, fill=glow, outline="")
        canvas.create_oval(cx-12, cy-15, cx+12, cy+9, fill=color, outline="")
        canvas.create_polygon(cx-12, cy-4, cx+12, cy-4,
                              cx+12, cy+14, cx+6, cy+9, cx, cy+14,
                              cx-6, cy+9, cx-12, cy+14,
                              fill=color, outline="")
        # Raised arms, big eyes and a tongue echo the ghost emoji.
        canvas.create_polygon(cx-10, cy-2, cx-18, cy-8, cx-16, cy+3,
                              cx-10, cy+7, fill=color, outline="")
        canvas.create_polygon(cx+10, cy-2, cx+18, cy-8, cx+16, cy+3,
                              cx+10, cy+7, fill=color, outline="")
        for dx in (-5, 5):
            canvas.create_oval(cx+dx-4, cy-9, cx+dx+4, cy,
                               fill="#fffaf2", outline="")
            canvas.create_oval(cx+dx-2, cy-6, cx+dx+2, cy-1,
                               fill="#211c30", outline="")
        canvas.create_oval(cx-5, cy+1, cx+5, cy+9, fill="#211c30", outline="")
        canvas.create_oval(cx, cy+5, cx+5, cy+11, fill="#ee729d", outline="")
        if number is not None:
            canvas.create_oval(cx+8, cy-19, cx+20, cy-7,
                               fill="#39263e", outline=color)
            canvas.create_text(cx+14, cy-13, text=str(number),
                               fill="#fff0db", font=("Helvetica", 8, "bold"))

    def draw():
        canvas.delete("all")
        for y, row in enumerate(MAP):
            for x, value in enumerate(row):
                left, top = x * cell, y * cell
                if value == "#":
                    canvas.create_rectangle(left, top, left+cell, top+cell, fill="#30283f", outline="#171421")
                    canvas.create_line(left+3, top+3, left+cell-3, top+3, fill="#59436c")
                    canvas.create_line(left, top+19, left+cell, top+19, fill="#211c30")
                    canvas.create_line(left+19, top, left+19, top+19, fill="#211c30")
                    canvas.create_line(left+9, top+19, left+9, top+cell, fill="#211c30")
                else:
                    color = "#1a1928" if (x+y) % 2 else "#1e1c2d"
                    canvas.create_rectangle(left, top, left+cell, top+cell, fill=color, outline="#242134")
                    if (x * 7 + y * 11) % 19 == 0:
                        canvas.create_line(left+12, top+27, left+17, top+22, left+22, top+25, fill="#383047")
        # Fading route markers show where the ghost has travelled.
        for index, (x, y) in enumerate(trails[-16:]):
            radius = 2 if index < 8 else 3
            cx, cy = (x+.5)*cell, (y+.5)*cell
            canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, fill="#4b857c", outline="")
        gx, gy = sim.evader
        draw_ghost((gx+.5)*cell, (gy+.5)*cell, mint)
        for index, (x, y) in enumerate(sim.pursuers):
            draw_ghost((x+.5)*cell, (y+.5)*cell, orange, index+1)
        turns_text.set(f"TURN  {sim.steps:03d} / {sim.max_steps}")
        progress.delete("all")
        progress.create_rectangle(0, 0, 190*sim.steps/sim.max_steps, 5, fill=mint, outline="")
        status_text.set("THE HUNT IS ON" if playing else "READY TO HAUNT" if sim.steps == 0 else "PAUSED")
        detail_text.set(f"Ghost: {sim.evader_strategy}    /    Hunters: {sim.pursuer_strategy}    /    Seed: {args.seed}")
        if sim.status != "running":
            captured = sim.status == "captured"
            title = "CAUGHT!" if captured else "GHOST ESCAPED!"
            status_text.set("CAPTURED" if captured else "SURVIVED")
            detail_text.set("Reset to start a new match. Change strategies to compare their behaviour.")
            canvas.create_rectangle(82, height/2-60, width-82, height/2+60, fill="#151321", outline=orange if captured else mint, width=2)
            canvas.create_text(width/2, height/2-15, text=title, fill=orange if captured else mint, font=("Helvetica", 24, "bold"))
            canvas.create_text(width/2, height/2+23, text=f"{sim.steps} turns  /  Reset to play again", fill="#ddd4eb", font=("Helvetica", 11))
        play_button.configure(text="Pause hunt" if playing else "Start hunt")

    def reset():
        nonlocal sim, playing
        playing = False
        trails.clear()
        sim = Simulation(evader_choice.get(), pursuer_choice.get(), args.seed, args.max_steps)
        draw()

    def advance():
        nonlocal playing
        if sim.status == "running":
            trails.append(sim.evader)
            sim.step()
        if sim.status != "running":
            playing = False
        draw()

    def single_step():
        nonlocal playing
        playing = False
        advance()

    def toggle():
        nonlocal playing
        if sim.status == "running":
            playing = not playing
            draw()

    footer = tk.Frame(root, bg=bg, padx=22, pady=14)
    footer.pack(fill="x")

    def button(text, command, primary=False):
        # A styled label avoids macOS native buttons ignoring background colours.
        normal = orange if primary else "#30283f"
        hover = "#ffb66e" if primary else "#49395c"
        widget = tk.Label(footer, text=text, font=("Helvetica", 11, "bold"),
                          bg=normal, fg="#201629" if primary else "#f1e9fc",
                          relief="flat", padx=16, pady=10, cursor="hand2",
                          takefocus=True, highlightthickness=1,
                          highlightbackground="#5c466e", highlightcolor=mint)
        widget.pack(side="left", padx=(0, 8))

        def activate(event=None):
            command()
            return "break"

        def click(event):
            if 0 <= event.x < widget.winfo_width() and 0 <= event.y < widget.winfo_height():
                widget.focus_set()
                activate()
            return "break"

        widget.bind("<ButtonRelease-1>", click)
        widget.bind("<Return>", activate)
        widget.bind("<space>", activate)
        widget.bind("<Enter>", lambda event: widget.configure(bg=hover))
        widget.bind("<Leave>", lambda event: widget.configure(bg=normal))
        return widget

    play_button = button("Start hunt", toggle, True)
    button("One turn", single_step)
    button("Reset / Apply", reset)
    tk.Label(footer, text="PACE", fg=muted, bg=bg, font=("Helvetica", 9, "bold")).pack(side="left", padx=(12, 4))
    speed = tk.Scale(footer, from_=1, to=8, orient="horizontal", length=100, bg=bg, fg=mint, troughcolor=panel, highlightthickness=0, showvalue=False)
    speed.set(3)
    speed.pack(side="left")
    tk.Label(root, textvariable=detail_text, fg=muted, bg=bg, font=("Helvetica", 10), pady=3).pack()
    tk.Label(root, text="SPACE  start / pause     |     RIGHT ARROW  one turn     |     R  reset", fg="#756c8d", bg=bg, font=("Helvetica", 9), pady=8).pack()

    def tick():
        if playing:
            advance()
        root.after(int(1000 / speed.get()), tick)

    # Shortcuts are disabled while selecting a strategy.
    def shortcut(action):
        focused = root.focus_get()
        if not isinstance(focused, ttk.Combobox):
            action()

    root.bind("<space>", lambda event: shortcut(toggle))
    root.bind("<Right>", lambda event: shortcut(single_step))
    root.bind("r", lambda event: shortcut(reset))
    reset()
    tick()
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evader", choices=STRATEGIES, default="greedy")
    parser.add_argument("--pursuers", choices=STRATEGIES, default="astar")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--headless", action="store_true", help="Run without a window")
    parser.add_argument("--episodes", type=int, default=100, help="Matches in headless mode")
    args = parser.parse_args()
    if args.max_steps < 1 or args.episodes < 1:
        parser.error("max-steps and episodes must be positive")
    if not args.headless:
        run_gui(args)
        return
    captures = 0
    total_steps = 0
    for episode in range(args.episodes):
        sim = Simulation(args.evader, args.pursuers, args.seed + episode, args.max_steps)
        while sim.status == "running":
            sim.step()
        captures += sim.status == "captured"
        total_steps += sim.steps
    print(f"Evader: {args.evader}; pursuers: {args.pursuers}")
    print(f"Matches: {args.episodes}; captures: {captures}; escapes: {args.episodes - captures}")
    print(f"Capture rate: {captures / args.episodes:.1%}; mean turns: {total_steps / args.episodes:.1f}")


if __name__ == "__main__":
    main()
