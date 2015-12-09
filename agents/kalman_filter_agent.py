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
import operator

from numpy.linalg import inv
import numpy as np

from bzrc import BZRC, Command
from kalman_plotter import GnuPlotter as plotter

class Agent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.commands = []

        self.delta_t = 0.5
        self.friction = 0

        self.init_kalman_filter()
        self.pl = plotter()
        self.ticks = 0
        self.update_time = 0
        self.attack_state = "track"
        self.look_ahead_steps = 20.0
        self.look_ahead_sec = 9.0
        self.target_loc = (0,0)
        self.kalman_precision_wait = 10.0
        self.latency_adjustment = 0.0
        self.mu_t = None
        self.dead_reset = False

        print self.constants

    def init_kalman_filter(self):


        self.sigma_t = np.matrix('100.0 0 0 0 0 0;\
                                  0 2.0 0 0 0 0;\
                                  0 0 2.0 0 0 0;\
                                  0 0 0 100.0 0 0;\
                                  0 0 0 0 2.0 0;\
                                  0 0 0 0 0 2.0')

        self.sigma_x = np.matrix('0.1 0 0 0 0 0;\
                                  0 0.1 0 0 0 0;\
                                  0 0 1 0 0 0;\
                                  0 0 0 0.1 0 0;\
                                  0 0 0 0 0.1 0;\
                                  0 0 0 0 0 1')

        self.sigma_z = np.matrix('25.0 0;0 25.0');

        self.H = np.matrix('1.0 0 0 0 0 0;\
                            0 0 0 1.0 0 0');

        self.HT = self.H.transpose()

        self.F = self.create_F_matrix(self.delta_t)
        self.FT = self.F.transpose();

    def create_F_matrix(self, delta_t):
        F = np.matrix('1.0 0 0 0 0 0;\
                      0 1.0 0 0 0 0;\
                      0 0 1.0 0 0 0;\
                      0 0 0 1.0 0 0;\
                      0 0 0 0 1.0 0;\
                      0 0 0 0 0 1.0')
        F[0,1] = delta_t
        F[0,2] = (delta_t ** 2) / 2
        F[1,2] = delta_t
        F[3,4] = delta_t
        F[4,5] = delta_t
        F[3,5] = (delta_t ** 2) / 2
        F[2,1] = self.friction
        F[5,4] = -self.friction
        return F

    def update_kalman_filter(self, Z):
        K = self.update_K_matrix()
        #print K
        self.update_mu_t(K, Z)
        print self.mu_t
        self.update_sigma_t(K)
        #print self.sigma_t

    def update_K_matrix(self):
        precalc = ((self.F * self.sigma_t * self.FT) + self.sigma_x) * self.HT
        precalc2 = inv((self.H * precalc) + self.sigma_z)
        return precalc * precalc2

    def update_mu_t(self, K, Z):
        precalc = self.F * self.mu_t
        precalc2 = K * (Z - (self.H * self.F * self.mu_t))
        self.mu_t = precalc + precalc2

    def update_sigma_t(self, K):
        I = np.identity(6)
        precalc = I - (K * self.H)
        precalc2 = (self.F * self.sigma_t * self.FT) + self.sigma_x
        self.sigma_t = precalc * precalc2

    def tick(self, time_diff):
        #print time_diff
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = mytanks

        if self.mu_t == None and othertanks[0].status != 'dead':
            self.mu_t = np.matrix([[othertanks[0].x],[0],[0],[othertanks[0].y],[0],[0]])
            #self.mu_t = np.matrix([[0],[0],[0],[0],[0],[0]])
            self.dead_reset = False

        self.commands = []

        if othertanks[0].status == 'dead' and not self.dead_reset:
            self.mu_t = None
            self.init_kalman_filter()
            self.dead_reset = True

        if time_diff >= self.update_time and othertanks[0].status != 'dead':

            if len(othertanks) != 1:
                print 'Must have only one enemy'
                sys.exit(-1)
            Z = np.matrix([[float(othertanks[0].x)],[float(othertanks[0].y)]])# get z from enemy tank
            #Z = np.matrix([[0],[0]])
            self.update_kalman_filter(Z)
            self.pl.plot(self.sigma_t[0,3], self.sigma_t[0,0], self.sigma_t[3,3], self.mu_t[0,0], self.mu_t[3,0])
            self.update_time += self.delta_t

        if self.mu_t != None:
            shotspeed = float(self.constants['shotspeed'])
            dist = self.dist(mytanks[0].x - self.mu_t[0,0], mytanks[0].y - self.mu_t[3,0])
            time = dist / shotspeed
            F = self.create_F_matrix(time)
            new_mu = F * self.mu_t
            #print new_mu

            self.move_to_position(mytanks[0], new_mu[0,0], new_mu[3,0])

        results = self.bzrc.do_commands(self.commands)

    def dist(self, x, y):
		return math.sqrt(x * x + y * y)


    def attack_enemies(self, tank):
        """Find the closest enemy and chase it, shooting as you go."""
        best_enemy = None
        best_dist = 2 * float(self.constants['worldsize'])
        # for enemy in self.enemies:
        #     if enemy.status != 'alive':
        #         continue
        #     dist = math.sqrt((enemy.x - tank.x)**2 + (enemy.y - tank.y)**2)
        #     if dist < best_dist:
        #         best_dist = dist
        #         best_enemy = enemy
        best
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
        if abs(relative_angle) <= 0.01:
            command = Command(tank.index, 0, 2 * relative_angle, True)
        else:
            command = Command(tank.index, 0, 2 * relative_angle, False)
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
