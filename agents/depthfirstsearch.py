import Queue as queue
import math
from collections import defaultdict

class DepthFirstSearch:
    def __init__(self):
        self.visibilityGraph = None

    def search(self, visibilityGraph, start, goal):
        self.visibilityGraph = visibilityGraph
        stack = []
        stack.insert(0, start)
        discovered = set()
        came_from = {}
        while stack:
            curr_node = stack.pop(0)
            if curr_node == goal:
                return self.rebuild_path(came_from, curr_node)
            if curr_node not in discovered:
                discovered.add(curr_node)
                for neighbor in visibilityGraph.keys():
                    if self.canVisit(curr_node, neighbor) and neighbor not in stack \
                                                and neighbor not in discovered:
                        came_from[neighbor] = curr_node
                        stack.insert(0, neighbor)

    def canVisit(self, curr, neighbor):
        return self.visibilityGraph[curr][neighbor] > 0

    def rebuild_path(self, came_from, current):
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        return total_path