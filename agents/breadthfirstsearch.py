import Queue
import math
from collections import defaultdict
from GraphSearch import GraphSearch

class BreadthFirstSearch(GraphSearch):
    def __init__(self, plot):
        GraphSearch.__init__(self, plot)
        self.visibilityGraph = None

    def search(self, visibilityGraph, start, goal):
        self.visibilityGraph = visibilityGraph
        q = []
        q_set = set()
        q.append(start)
        q_set.add(start)
        discovered = set()
        came_from = {}
        while q:
            if self.plot:
                self.plot_graph(q_set, discovered, came_from, "BreadthFirstSearch")
            curr_node = q.pop(0)
            if curr_node == goal:
                discovered.add(goal)
                if self.plot:
                    self.plot_graph(q_set, discovered, came_from, "BreadthFirstSearch")
                return self.rebuild_path(came_from, curr_node)
            if curr_node not in discovered:
                discovered.add(curr_node)
                q_set.remove(curr_node)
                for neighbor in visibilityGraph.keys():
                    if self.canVisit(curr_node, neighbor) and neighbor not in q_set \
                                                and neighbor not in discovered:
                        came_from[neighbor] = curr_node
                        q.append(neighbor)
                        q_set.add(neighbor)

    def canVisit(self, curr, neighbor):
        return self.visibilityGraph[curr][neighbor] > 0

    def rebuild_path(self, came_from, current):
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        return total_path
