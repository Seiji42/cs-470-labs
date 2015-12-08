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


import numpy as np

from bzrc import BZRC, Command

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc, type):
        self.bzrc = bzrc
        self.type = type
        self.constants = self.bzrc.get_constants()
        self.commands = []

        print self.constants

    def tick(self, time_diff):
        #print time_diff
        """Some time has passed; decide what to do next."""

        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = mytanks

        self.commands = []

        for tank in mytanks:
            if self.type == 'line':
                command = Command(tank.index, 1, 0, False)
                self.commands.append(command)
            elif self.type == 'wild':
                x = 6
                #do wild pidgeon movement
                # self.explore_grid(tank)
        results = self.bzrc.do_commands(self.commands)

    def explore_grid(self, tank):
        # mytank [index] [callsign] [status] [shots available] [time to reload] [flag] [x] [y] [angle] [vx] [vy] [angvel]
        truePos = float(self.constants['truepositive'])
        trueNeg = float(self.constants['truenegative'])

        sensor_top_left, sensor_grid = self.bzrc.get_occgrid(tank.index)

        translated_top_left = (sensor_top_left[0] + (self.world_size / 2), sensor_top_left[1] + (self.world_size / 2))

        # Grid Filter Madness
        for x in range(0, len(sensor_grid)):
            for y in range(0, len(sensor_grid[0])):
                worldX = translated_top_left[0] + x
                worldY = translated_top_left[1] + y

                if sensor_grid[x][y] == 1.0: # draw black ( need to equal zero)
                    bel_occ = truePos * (1.0 - self.grid[worldY][worldX])
                    bel_unocc = (1.0 - trueNeg) * self.grid[worldY][worldX]
                    self.grid[worldY][worldX] = 1.0 - (bel_occ / (bel_occ + bel_unocc))
                else: # draw white
                    bel_occ = (1.0 - truePos) * (1.0 - self.grid[worldY][worldX])
                    bel_unocc = trueNeg * self.grid[worldY][worldX]
                    self.grid[worldY][worldX] = 1.0 - (bel_occ / (bel_occ + bel_unocc))

                #Look around cell
                look_around_val = self.look_around_cell(x, y, sensor_grid)
                if look_around_val[1] >= self.occ_threshold:
                    #self.grid[worldY][worldX] = self.grid[worldY][worldX] * look_around_val[1]
                    self.grid[worldY][worldX] -= self.look_around_boost
                    if self.grid[worldY][worldX] < 0.0:
                        self.grid[worldY][worldX] = 0.0
                elif look_around_val[0] >= self.not_occ_threshold:
                    #self.grid[worldY][worldX] = self.grid[worldY][worldX] * look_around_val[0]
                    self.grid[worldY][worldX] += self.look_around_boost
                    if self.grid[worldY][worldX] > 1.0:
                        self.grid[worldY][worldX] = 1.0

                if self.grid[worldY][worldX] <= self.assume_obstacle:
                    self.grid[worldY][worldX] = 0.0
                elif self.grid[worldY][worldX] >= self.assume_free:
                    self.grid[worldY][worldX] = 1.0

        posX, posY = self.get_goal(tank)
        self.move_to_position(tank, posX, posY)
        return

    def get_goal(self, tank):
        scale = 50

        # print (tank.x)
        # print (tank.y)
        point_to_check = (int(scale * math.cos(tank.angle) + tank.x), int(scale * math.sin(tank.angle) + tank.y))

        # print(point_to_check)

        if self.check_point(point_to_check) != None:
            return point_to_check

        # print "getting new goal"
        for i in range(4, 2):
            pos_ang = (int(scale * math.cos(tank.angle + math.pi / i) + tank.x), int(scale * math.sin(tank.angle + math.pi / i) + tank.y))
            # print "positive"
            if self.check_point(pos_ang) != None:
                return pos_ang
            neg_ang = (int(scale * math.cos(tank.angle - math.pi / i) + tank.x), int(scale * math.sin(tank.angle - math.pi / i) + tank.y))
            # print "negative"
            if self.check_point(neg_ang) != None:
                return neg_ang

        for i in range(2, 4):
            pos_ang = (int(scale * math.cos(tank.angle + math.pi * (i - 1)/ i) + tank.x), int(scale * math.sin(tank.angle + math.pi * (i - 1) / i) + tank.y))
            # print "positive"
            if self.check_point(pos_ang) != None:
                return pos_ang
            neg_ang = (int(scale * math.cos(tank.angle - math.pi * (i - 1) / i) + tank.x), int(scale * math.sin(tank.angle - math.pi * (i - 1) / i) + tank.y))
            # print "negative"
            if self.check_point(neg_ang) != None:
                return neg_ang
        #need default value to return

    def check_point(self, point) :
        average_grid_size = 10
        if point[0] < 400 and point[0] > -400 and point[1] < 400 and point[1] > -400 and self.get_average((point[0] + self.world_size / 2, point[1] + self.world_size / 2), average_grid_size) > self.assume_obstacle:
            return point
        else:
            # print "need goal"
            return None

    def get_average(self, point, grid_size):
        """
        move point to be top left of grid
        if topleft of grid is out of self.grid
            get modified grid_width and grid_height
            and move top_left to be in self.grid
        while in grid
            calculate average
        return average
        """
        width = grid_size
        height = grid_size
        corner = {
            'x':point[0] - grid_size / 2,
            'y':point[1] - grid_size / 2
        }
        if (corner['x'] < 0):
            width = grid_size + corner['x']
            corner['x'] = 0
        if (corner['y'] < 0):
            height = grid_size + corner['y']
            corner['y'] = 0
        count = 0.0
        total = 0.0
        x_edge = self.world_size if corner['x'] + width > self.world_size else corner['x'] + width
        y_edge = self.world_size if corner['y'] + height > self.world_size else corner['y'] + height
        x = corner['x']
        while x < x_edge:
            y = corner['y']
            while y < y_edge:
                total += self.grid[y][x]
                count += 1.0
                y += 1.0
            x += 1.0
        return total / count

    def dist(self, x, y):
		return math.sqrt(x * x + y * y)

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



def main():
    # Process CLI arguments.
    try:
        execname, host, port, type = sys.argv
    except ValueError:
        execname = sys.argv[0]
        print >>sys.stderr, '%s: incorrect number of arguments' % execname
        print >>sys.stderr, 'usage: %s hostname port' % sys.argv[0]
        sys.exit(-1)

    # Connect.
    #bzrc = BZRC(host, int(port), debug=True)
    bzrc = BZRC(host, int(port))

    agent = Agent(bzrc, type)

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
