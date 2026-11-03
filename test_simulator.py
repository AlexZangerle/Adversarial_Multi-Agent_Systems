"""Check path correctness and the rules that all strategies must obey."""
import unittest
from collections import deque
from simulator import MAP, STRATEGIES, Simulation, astar_path, is_open, neighbours


class SimulatorTests(unittest.TestCase):
    def test_astar_matches_breadth_first_search(self):
        start = (1, 1)
        distances = {start: 0}
        queue = deque([start])
        while queue:
            cell = queue.popleft()
            for other in neighbours(cell):
                if other not in distances:
                    distances[other] = distances[cell] + 1
                    queue.append(other)
        for goal, distance in distances.items():
            path = astar_path(start, goal)
            self.assertEqual(len(path) - 1, distance)
            self.assertEqual(path[0], start)
            self.assertEqual(path[-1], goal)
            for a, b in zip(path, path[1:]):
                self.assertIn(b, neighbours(a))

    def test_blocked_route(self):
        self.assertEqual(astar_path((1, 1), (2, 1), [(2, 1)]), [])
        self.assertEqual(astar_path((1, 1), (3, 1), [(2, 1), (1, 2)]), [])

    def test_all_baselines_obey_rules(self):
        for evader in STRATEGIES:
            for pursuers in STRATEGIES:
                for seed in range(5):
                    sim = Simulation(evader, pursuers, seed, 30)
                    while sim.status == "running":
                        previous_e, previous_p = sim.evader, sim.pursuers[:]
                        sim.step()
                        self.assertIn(sim.evader, neighbours(previous_e) + [previous_e])
                        self.assertNotIn(sim.evader, previous_p)
                        self.assertTrue(all(is_open(p) for p in sim.pursuers))
                        self.assertEqual(len(set(sim.pursuers)), 3)
                        for before, after in zip(previous_p, sim.pursuers):
                            self.assertIn(after, neighbours(before) + [before])
                    self.assertLessEqual(sim.steps, 30)
                    self.assertEqual(sim.evader in sim.pursuers, sim.status == "captured")
                    snapshot = (sim.steps, sim.evader, sim.pursuers[:], sim.status)
                    sim.step()
                    self.assertEqual(snapshot, (sim.steps, sim.evader, sim.pursuers, sim.status))

    def test_seed_reproducibility(self):
        a = Simulation("random", "random", 42, 40)
        b = Simulation("random", "random", 42, 40)
        for _ in range(40):
            a.step()
            b.step()
            self.assertEqual((a.evader, a.pursuers, a.status), (b.evader, b.pursuers, b.status))

    def test_capture_and_timeout(self):
        sim = Simulation("random", "greedy")
        sim.evader = (1, 1)
        sim.pursuers = [(2, 1), (1, 2), (3, 1)]
        sim.step()
        self.assertEqual(sim.status, "captured")
        sim = Simulation("greedy", "astar", max_steps=1)
        sim.step()
        self.assertEqual(sim.status, "escaped")


if __name__ == "__main__":
    unittest.main()
