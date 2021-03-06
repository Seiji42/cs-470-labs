from __future__ import division
from itertools import cycle
from numpy import linspace
from bzrc import Answer
from bzrc import BZRC
from VisibilityGraphAgent import VisibilityGraphAgent
import sys
import matplotlib
import matplotlib.pyplot as plt
from astarsearch import AStarSearch
from depthfirstsearch import DepthFirstSearch
from breadthfirstsearch import BreadthFirstSearch

WORLDSIZE = 800

def draw_line(p1, p2, ax):
    '''Return a string to tell Gnuplot to draw a line from point p1 to
    point p2 in the form of a set command.'''
    x1, y1 = p1
    x2, y2 = p2
    arrow = matplotlib.patches.Arrow(x1, y1, x2 - x1, y2 - y1, width=1.0, color='green')
    ax.add_patch(arrow)

def draw_obstacles(obstacles, ax):
    for obstacle in obstacles:
        obs = obstacle.points
        rect1 = matplotlib.patches.Rectangle((obs[1][0],obs[1][1]), \
            obs[2][0] - obs[1][0], obs[0][1] - obs[1][1], color='blue')
        ax.add_patch(rect1)

def plot_path(path, ax):
    '''Return a Gnuplot command to plot a field.'''
    s = 'unset arrow\n'
    for i in range(0, len(path) - 1):
        draw_line(path[i], path[i + 1], ax)
    return s

def plot_goal(goal):
    plt.plot([goal[0]], [goal[1]], 'gv', ms=10)
    return
def plot_position(position):
    plt.plot([position[0]], [position[1]], 'ro', ms=10)
    return

if __name__ == '__main__':
    HOST = 'localhost'
    PORT = sys.argv[1]
    bzrc = BZRC(HOST, int(PORT))
    search = AStarSearch(True)
    title = 'A* Search'
    if sys.argv[2] == 'b':
        search = BreadthFirstSearch(True)
        title = "Breadth First Search"
    elif sys.argv[2] == 'd':
        search = DepthFirstSearch(True)
        title = "Depth First Search"
    elif sys.argv[2] != 'a':
        print "You must enter a search type: [a]star, [b]readth first, [d]epth first"

    agent = VisibilityGraphAgent(bzrc, search)
    fig = plt.figure()
    plt.axis([-WORLDSIZE / 2, WORLDSIZE / 2, -WORLDSIZE / 2, WORLDSIZE / 2])
    ax = fig.add_subplot(111)
    draw_obstacles(agent.obstacles, ax)
    plot_path(agent.path, ax)
    plot_goal(agent.goal)
    plot_position(agent.position)
    plt.title(title)
    plt.show()
