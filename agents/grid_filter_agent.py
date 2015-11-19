#!/usr/bin/python -tt

# An incredibly simple agent.  All we do is find the closest enemy tank, drive
# towards it, and shoot.  Note that if friendly fire is allowed, you will very
# often kill your own tanks with this code.

#################################################################
# NOTE TO STUDENTS
# This is a starting point for you.  You will need to greatly
# modify this code if you want to do anything useful.  But this
# should help you to know how to interact with BZRC in order to
# get the information you need.
#
# After starting the bzrflag server, this is one way to start
# this code:
# python agent0.py [hostname] [port]
#
# Often this translates to something like the following (with the
# port name being printed out by the bzrflag server):
# python agent0.py localhost 49857
#################################################################

import sys
import math
import time
import random
import OpenGL
OpenGL.ERROR_CHECKING = False
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import numpy as np

from bzrc import BZRC, Command

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.occ_size = 100
        self.goal_time = 12
        self.commands = []
        self.goal_data = []
        self.starting_prob = 0.2
        self.grid = np.ones((int(self.constants['worldsize']), int(self.constants['worldsize'])))
        self.grid.fill(self.starting_prob)
        self.test_grid = np.ones((int(self.constants['worldsize']), int(self.constants['worldsize'])))
        self.test_grid.fill(self.starting_prob)
        self.init_window(800,800)
        self.flag = True
        self.world_size = world_size = int(self.constants['worldsize'])
        self.occ_threshold = 0.75
        self.not_occ_threshold = 0.75
        self.goal_radius = 50
        self.look_around_boost = 0.5
        print self.constants

    def tick(self, time_diff):
        #print time_diff
        """Some time has passed; decide what to do next."""

        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = mytanks
        if len(self.goal_data) == 0:
            for tank in self.mytanks:
                randX = random.randrange(8) * 100 - 400 + random.randrange(100)
                randY = random.randrange(8) * 100 - 400 + random.randrange(100)
                self.goal_data.append((1, (randX, randY)))
        else:
            for tank in self.mytanks:
                xdiff = self.goal_data[tank.index][1][0] - tank.x
                ydiff = self.goal_data[tank.index][1][1] - tank.y
                if self.goal_data[tank.index][0] * self.goal_time < time_diff or xdiff ** 2 + ydiff ** 2 <= self.goal_radius ** 2:
                    randX = random.randrange(8) * 100 - 400 + random.randrange(100)
                    randY = random.randrange(8) * 100 - 400 + random.randrange(100)
                    if random.randrange(1) == 1:
                        self.goal_data[tank.index] = (self.goal_data[tank.index][0] + 1, (randX, randY))
                    else:
                        self.goal_data[tank.index] = (self.goal_data[tank.index][0] + 1, (randX, randY))
        # Don't need these

        # self.othertanks = othertanks
        # self.flags = flags
        # self.shots = shots
        # self.enemies = [tank for tank in othertanks if tank.color !=
        #                 self.constants['team']]

        self.commands = []

        for tank in mytanks:
            self.explore_grid(tank)
        #print self.grid
            # self.attack_enemies(tank)

        self.update_grid(self.grid)
        self.draw_grid()

        results = self.bzrc.do_commands(self.commands)

    def explore_grid(self, tank):
        # mytank [index] [callsign] [status] [shots available] [time to reload] [flag] [x] [y] [angle] [vx] [vy] [angvel]
        truePos = float(self.constants['truepositive'])
        trueNeg = float(self.constants['truenegative'])

        #print str(tank.index)
        tank_pos, sensor = self.bzrc.get_occgrid(tank.index)
        #sensor_size = 100#int(self.constants["occ_grid"])
        # Grid Filter Madness
        for x in range(0, len(sensor)):
            for y in range(0, len(sensor[0])):
                worldX = tank_pos[0] + (self.world_size / 2) - (self.occ_size / 2) + x
                worldY = tank_pos[1] + (self.world_size / 2) - (self.occ_size / 2) + y

                #print "x,y: %d,%d pos: %d,%d world: %d,%d" % (x,y,tank_pos[0],tank_pos[1],worldX,worldY)

                if worldX >= self.world_size or worldX < 0 or worldY >= self.world_size or worldY < 0:
                    continue

                look_around_val = self.look_around_cell(x, y, sensor)
                if sensor[x][y] == 1: # draw black ( need to equal zero)
                    bel_occ = truePos * (1 - self.grid[worldY][worldX])
                    bel_unocc = (1-trueNeg) * self.grid[worldY][worldX]

                    #Look around cell
                    self.grid[worldY][worldX] = 1 - (bel_occ / (bel_occ + bel_unocc))


                else: # draw white
                    bel_occ = (1-truePos) * (1 - self.grid[worldY][worldX])
                    bel_unocc = trueNeg * self.grid[worldY][worldX]
                    self.grid[worldY][worldX] = 1 - (bel_occ / (bel_occ + bel_unocc))

                if look_around_val[1] >= self.occ_threshold:
                    #self.grid[worldY][worldX] = self.grid[worldY][worldX] * look_around_val[1]
                    self.grid[worldY][worldX] -= self.look_around_boost
                    if self.grid[worldY][worldX] < 0:
                        self.grid[worldY][worldX] = 0
                elif look_around_val[0] >= self.not_occ_threshold:
                    #self.grid[worldY][worldX] = self.grid[worldY][worldX] * look_around_val[0]
                    self.grid[worldY][worldX] += self.look_around_boost
                    if self.grid[worldY][worldX] > 1:
                        self.grid[worldY][worldX] = 1

        # move tank
            posX = self.goal_data[tank.index][1][0]
            posY = self.goal_data[tank.index][1][1]
            self.move_to_position(tank, posX, posY)
        return

    def look_around_cell(self, x, y, sensor):
        ones = 0
        zeros = 0
        count = 0.0
        for i in (-1,0,1):
            for j in (-1,0,1):
                if i == 0 and j == 0:
                    continue
                if self.cell_in_sensor(x + i, y + j, sensor):
                    count += 1
                    if sensor[x + i][y + j] == 1:
                        ones += 1
                    else:
                        zeros += 1

        return (zeros / count, ones / count)

    def cell_in_map(self,x,y):
        return x >= 0 and y >= 0 and x < self.world_size and y < self.world_size

    def cell_in_sensor(self,x,y,sensor):
        return x >= 0 and y >= 0 and x < len(sensor) and y < len(sensor[0])

    def attack_enemies(self, tank):
        """Find the closest enemy and chase it, shooting as you go."""
        best_enemy = None
        best_dist = 2 * float(self.constants['worldsize'])
        for enemy in self.enemies:
            if enemy.status != 'alive':
                continue
            dist = math.sqrt((enemy.x - tank.x)**2 + (enemy.y - tank.y)**2)
            if dist < best_dist:
                best_dist = dist
                best_enemy = enemy
        if best_enemy is None:
            command = Command(tank.index, 0, 0, False)
            self.commands.append(command)
        else:
            self.move_to_position(tank, best_enemy.x, best_enemy.y)

    def move_to_position(self, tank, target_x, target_y):
        """Set command to move to given coordinates."""
        target_angle = math.atan2(target_y - tank.y,
                                  target_x - tank.x)
        relative_angle = self.normalize_angle(target_angle - tank.angle)
        command = Command(tank.index, 1, 2 * relative_angle, False)
        self.commands.append(command)

    def normalize_angle(self, angle):
        """Make any angle be between +/- pi."""
        angle -= 2 * math.pi * int (angle / (2 * math.pi))
        if angle <= -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle

    def draw_grid(self):
        # This assumes you are using a numpy array for your grid
        width, height = self.grid.shape
        glRasterPos2f(-1, -1)
        glDrawPixels(width, height, GL_LUMINANCE, GL_FLOAT, self.grid)
        glFlush()
        glutSwapBuffers()

    def update_grid(self, new_grid):
        global grid
        #for y in range(0,800):
            #for x in range(0,800):
                #self.grid[y][x] = 1 - self.test_grid[y][x]
        #self.grid = new_grid

    def init_window(self, width, height):
        global window
        global grid
        glutInit(())
        glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH)
        glutInitWindowSize(width, height)
        glutInitWindowPosition(0, 0)
        window = glutCreateWindow("Grid filter")
        glutDisplayFunc(self.draw_grid)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        #glutMainLoop()


def main():
    # Process CLI arguments.
    try:
        execname, host, port = sys.argv
    except ValueError:
        execname = sys.argv[0]
        print >>sys.stderr, '%s: incorrect number of arguments' % execname
        print >>sys.stderr, 'usage: %s hostname port' % sys.argv[0]
        sys.exit(-1)

    # Connect.
    #bzrc = BZRC(host, int(port), debug=True)
    bzrc = BZRC(host, int(port))

    agent = Agent(bzrc)

    prev_time = time.time()

    # Run the agent
    try:
        while True:
            time_diff = time.time() - prev_time
            agent.tick(time_diff)
    except KeyboardInterrupt:
        print "Exiting due to keyboard interrupt."
        bzrc.close()


if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4
