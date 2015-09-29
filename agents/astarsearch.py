import Queue as queue
import math
from collections import defaultdict

class AStarSearch:
    def __init__(self):
        self.visibilityGraph = None

    def search(self, visibilityGraph, start, goal):
        self.visibilityGraph = visibilityGraph
        frontier = queue.PriorityQueue()
        frontier_set =  set()
        frontier.put((0, 1, start))
        explored = set()
        g_score = defaultdict(lambda: float("inf"), {})
        g_score[start] = 0
        f_score = defaultdict(lambda: float("inf"), {})
        f_score[start] = g_score[start] + self.heuristic_cost_estimate(start, goal)
        came_from = {}

        while not frontier.empty():
            curr_node = frontier.get()[2]
            if curr_node == goal:
                return self.rebuild_path(came_from, goal)
            explored.add(curr_node)

            for neighbor in visibilityGraph[curr_node].keys():
                if neighbor in explored:
                    continue

                temp_g_score = g_score[curr_node] + self.dist(curr_node, neighbor)

                if self.canVisit(curr_node, neighbor):
                    if neighbor not in frontier_set or temp_g_score < g_score[neighbor]:
                        came_from[neighbor] = curr_node
                        g_score[neighbor] = temp_g_score
                        f_score[neighbor] = g_score[neighbor] + self.heuristic_cost_estimate(neighbor, goal)
                        if neighbor not in frontier_set:
                            frontier.put((f_score[neighbor], 1, neighbor))
                            frontier_set.add(neighbor)

    def canVisit(self, curr, neighbor):
        return self.visibilityGraph[curr][neighbor] > 0

    def rebuild_path(self, came_from, current):
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        return total_path

        '''
        init frontier to starting pos
        init explored set to empty
        loop do
        if frontier empty return failure
        choose leaf node and remove from frontier
        if leaf node contains goal return corresponding solution
        add node to explored set
        expand chosen node, adding the resulting nodes to the frontier only if not in frontier or explored set

        '''
    def heuristic_cost_estimate(self, start, goal):
        return self.dist(start, goal)
    def dist(self, p1, p2):
        delta = (p2[0] - p1[0], p2[1] - p1[1])
        return math.sqrt(delta[0] ** 2 + delta[1] ** 2)