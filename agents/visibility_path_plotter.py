from __future__ import division
from itertools import cycle
from numpy import linspace
from bzrc import Answer
from bzrc import BZRC
from VisibilityGraphAgent import VisibilityGraphAgent
import sys

FILENAME = 'test_fields.gpi'
WORLDSIZE = 800
SAMPLES = 25
VEC_LEN =  0.75 * WORLDSIZE / SAMPLES

def generate_field_function(scale):
    def function(x, y):
        '''User-defined field function.'''
        sqnorm = (x**2 + y**2)
        if sqnorm == 0.0:
            return 0, 0
        else:
            return x*scale/sqnorm, y*scale/sqnorm
    return function

def gpi_point(x, y, vec_x, vec_y):
    '''Create the centered gpi data point (4-tuple) for a position and
    vector.  The vectors are expected to be less than 1 in magnitude,
    and larger values will be scaled down.'''
    r = (vec_x ** 2 + vec_y ** 2) ** 0.5
    if r > 1:
        vec_x /= r
        vec_y /= r
    return (x - vec_x * VEC_LEN / 2, y - vec_y * VEC_LEN / 2,
            vec_x * VEC_LEN, vec_y * VEC_LEN)

def gnuplot_header(minimum, maximum):
    '''Return a string that has all of the gnuplot sets and unsets.'''
    s = ''
    s += 'set xrange [%s: %s]\n' % (minimum, maximum)
    s += 'set yrange [%s: %s]\n' % (minimum, maximum)
    # The key is just clutter.  Get rid of it:
    s += 'unset key\n'
    # Make sure the figure is square since the world is square:
    s += 'set size square\n'
    # Add a pretty title (optional):
    #s += "set title 'Potential Fields'\n"
    return s

def draw_line(p1, p2, color):
    '''Return a string to tell Gnuplot to draw a line from point p1 to
    point p2 in the form of a set command.'''
    x1, y1 = p1
    x2, y2 = p2
    return 'set arrow from %s, %s to %s, %s nohead lt 3 linecolor rgb \"%s\"\n' % (x1, y1, x2, y2, color)

def draw_obstacles(obstacles):
    '''Return a string which tells Gnuplot to draw all of the obstacles.'''
    s = 'unset arrow\n'

    for obstacle in obstacles:
        obs = obstacle.points
        last_point = obs[0]
        for cur_point in obs[1:]:
            s += draw_line(last_point, cur_point, "blue")
            last_point = cur_point
        s += draw_line(last_point, obs[0], "blue")
    return s

def plot_path(function, path, color):
    '''Return a Gnuplot command to plot a field.'''
    s = 'unset arrow\n'
    for i in range(0, len(path) - 1):
        s += draw_line(path[i], path[i + 1], color)
    return s


if __name__ == '__main__':
    FILENAME = sys.argv[1]
    HOST = 'localhost'
    PORT = '55744'
    bzrc = BZRC(HOST, int(PORT))
    agent = VisibilityGraphAgent(bzrc)
    outfile = open(FILENAME, 'w')
    print >>outfile, gnuplot_header(-WORLDSIZE / 2, WORLDSIZE / 2)
    print >>outfile, draw_obstacles(agent.obstacles)
    field_function = generate_field_function(150)
    #print >>outfile, plot_field(agent.calculate_potential_fields)
    #print >>outfile, plot_field(agent.calc_goal_vector)
    #print >>outfile, plot_field(agent.calc_tangential_vector)
    print >>outfile, plot_path(field_function, agent.path, "red")
