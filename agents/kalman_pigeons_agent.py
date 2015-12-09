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
from random import randrange, uniform


import numpy as np

from bzrc import BZRC, Command

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc, type):
        self.bzrc = bzrc
        self.type = type
        self.constants = self.bzrc.get_constants()
        self.commands = []
        self.goal_change_time = 2
        self.update_time = 0
        self.forward_velocity = 0.5

        self.pigeon_goal = None

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""

        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = mytanks

        self.commands = []


        for tank in mytanks:
            if self.type == 'line':
                self.move_to_position(tank, 400, 400, 0.5, 0)
            elif self.type == 'wild':
                if self.update_time < time_diff:
                    self.update_time += 2
                    self.forward_velocity = uniform(1, 0.25)
                if self.pigeon_goal == None or self.dist(tank.x - self.pigeon_goal[0], tank.y - self.pigeon_goal[1]) < 10:
                    self.pigeon_goal = (randrange(-400, 401), randrange(-400, 401))
                self.move_to_position(tank, self.pigeon_goal[0], self.pigeon_goal[1], self.forward_velocity, randrange(-30,30))

        results = self.bzrc.do_commands(self.commands)

    def dist(self, x, y):
		return math.sqrt(x * x + y * y)

    def move_to_position(self, tank, target_x, target_y, speed, ang_noise):
        """Set command to move to given coordinates."""
        target_angle = math.atan2(target_y - tank.y,
                                  target_x - tank.x)
        relative_angle = self.normalize_angle(target_angle - tank.angle)
        command = Command(tank.index, self.forward_velocity, 2 * relative_angle, False)
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
