# Topic F — Steps 1 and 2

A small Python pursuit-evasion simulator. One evader tries to survive while three pursuers try to capture it. This milestone implements the grid and baseline strategies; there is no training yet.

## Run

Install Python 3 with Tkinter support (the Python.org desktop installer normally includes it). No pip packages are required. Open a terminal in this folder:

```sh
python3 simulator.py
```

Select strategies for both sides and click **Reset / Apply**, then **Start hunt** or **One turn**. Reset repeats the same initial state and random seed. The default is a greedy evader against A* pursuers.

Without a window:

```sh
python3 simulator.py --headless --evader random --pursuers astar --episodes 100 --seed 0
python3 -m unittest -v
```

On Windows, use `py` instead of `python3` if needed. If Tkinter is unavailable, headless mode still works. If Python requests Xcode developer tools on macOS, install a working Python distribution first.

## Exact rules (our design choices)

- The fixed map is 15 columns by 13 rows; `#` marks blocked cells.
- Positions are `(x, y)`, with `(0, 0)` at the top-left.
- One turn: the evader moves first, then P1, P2, P3 in order.
- An action moves one cell up, right, down or left, or stays still. No diagonal moves.
- Walls and positions outside the map are illegal.
- Pursuers cannot share cells. Each sees the updated positions from earlier moves.
- The evader cannot enter a cell currently occupied by a pursuer.
- Pursuers may enter the evader's cell: this immediately ends the match as a capture.
- Because moves are sequential, agents cannot swap occupied cells in one simultaneous action.
- Surviving 200 turns counts as an escape. Change this with `--max-steps`.
- All agents know the whole map and current positions. No field-of-view restriction yet.
- Pursuers share a strategy type but decide individually; no explicit team coordination yet.
- The map and starting positions are fixed. A seed controls random decisions.

The fixed turn order gives the evader the first move and later pursuers updated information. This is a documented simplification, not a claim of perfectly balanced gameplay.

## Baselines and defence notes

| Strategy | Pursuer | Evader |
|---|---|---|
| Random | Uniform choice among legal moves, including stay | Same, excluding pursuer cells |
| Greedy | Minimise Manhattan distance to the evader | Maximise Manhattan distance from the nearest pursuer |
| A* | Follow the first step of a shortest legal path to the evader | Pick the legal next cell with the greatest minimum A* path distance from pursuers |

Greedy is our hand-crafted rule-based baseline. A* is our pathfinding heuristic baseline. These labels overlap; they are not three separate requirements needing entirely different frameworks.

Manhattan distance is `abs(x1-x2) + abs(y1-y2)`. It ignores obstacles, so greedy can get stuck. A* combines travelled cost `g` and estimated remaining distance `h`: `f = g + h`. Every move costs one, and Manhattan distance is a valid heuristic for this four-direction grid.

The A* evader is a hand-crafted escape rule using shortest-path distances. A* itself does not solve the full adversarial game. Its safety scores account for walls but ignore other pursuers as temporary blockers. An unreachable pursuer contributes infinite distance. Pursuer A* does treat teammates as blocked cells.

Greedy and evader safety ties use up, right, down, left, stay ordering. A* frontier ties use travelled cost then coordinate order. A* waits when no route is available. These deterministic choices make debugging easier but may cause loops.

## Explain the code

1. `MAP`, `is_open`, `neighbours`: world and valid adjacent cells.
2. `astar_path`: frontier, cost table and path reconstruction.
3. `Simulation`: positions, strategy selection, turn order and ending conditions.
4. `run_gui`: draws the current state; the simulation also runs independently.
5. `main`: command-line choices and repeated-match statistics.

The tests compare A* against breadth-first search and check legal movement, occupancy, terminal states and reproducibility across all strategy pairings.

## Interpreting results

Headless mode prints capture rate and mean turns across all matches. Deterministic strategies on this fixed map repeat the same match across seeds; those repetitions are not independent evidence of general performance. Broader evaluation needs multiple maps and starting positions. No performance results are claimed in advance.

## Suggested group workflow

Use one shared GitHub repository, individual accounts and small reviewed changes. For this milestone, split work into simulator rules, random/greedy, A*, visualisation, and testing/documentation. Everyone should understand the common rules and their own contribution. This is a suggested workflow; confirm individual submission and assessment requirements with the instructor.

## AI disclosure

This initial implementation, tests and accompanying explanations were generated with AI assistance in Codex. The team must review, run, understand and adapt them before submission. Follow the course's orange-category programming/data-analysis declaration rules and any additional instructor conditions. This README is working documentation, not a ready-to-submit report or presentation.

## Halloween interface

The mint ghost is the evader; the three numbered orange ghosts are the pursuers. Both teams use the same playful ghost design with raised arms, big eyes and a tongue. Stone blocks are obstacles. The ghost trail is visual history only. The side panel shows turn count and match status. The end banner reports capture or survival.

- **Start hunt / Pause hunt**: run or pause.
- **One turn**: pause and advance once.
- **Reset / Apply**: restart and apply selected strategies.
- **Pace**: 1–8 turns per second.
- **Space**: start/pause; **Right arrow**: one turn; **R**: reset.

Characters are drawn with Tkinter Canvas shapes, with no external images, fonts or additional packages required. Native controls can look slightly different on Windows and macOS. The simulation rules and baseline algorithms are unchanged.
