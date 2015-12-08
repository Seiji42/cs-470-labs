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
        self.look_ahead_steps = 16
        self.target_loc = (0,0)
        self.kalman_precision_wait = 4

        self.mu_t = None

        print self.constants

    def init_kalman_filter(self):

        #self.mu_t = np.zeros([6,1])

        self.sigma_t = np.zeros([6,6])
        self.sigma_t[0,0] = 10
        self.sigma_t[1,1] = 10
        self.sigma_t[2,2] = 10
        self.sigma_t[3,3] = 10
        self.sigma_t[4,4] = 10
        self.sigma_t[5,5] = 10

        self.sigma_x = np.zeros([6,6])
        self.sigma_x[0,0] = 10
        self.sigma_x[1,1] = 10
        self.sigma_x[2,2] = 10
        self.sigma_x[3,3] = 10
        self.sigma_x[4,4] = 10
        self.sigma_x[5,5] = 10

        self.sigma_z = np.zeros([2,2])
        self.sigma_z[0,0] = 25
        self.sigma_z[1,1] = 25

        self.H = np.zeros([2,6])
        self.H[0,0] = 1
        self.H[1,3] = 1

        self.F = np.zeros([6,6])
        np.fill_diagonal(self.F, 1)
        self.F[0,1] = self.delta_t
        self.F[0,2] = self.delta_t ** 2 / 2
        self.F[1,2] = self.delta_t
        self.F[3,4] = self.delta_t
        self.F[4,5] = self.delta_t
        self.F[3,5] = self.delta_t ** 2 / 2
        self.F[2,1] = -self.friction
        self.F[5,4] = -self.friction

    def update_kalman_filter(self, Z):
        K = self.update_K_matrix()
        self.update_mu_t(K, Z)
        print self.mu_t
        self.update_sigma_t(K)
        #print self.sigma_t

    def update_K_matrix(self):
        precalc = np.dot(np.add(np.dot(np.dot(self.F, self.sigma_t), self.F.transpose()), self.sigma_x), self.H.transpose())
        precalc2 = inv(np.add(np.dot(self.H, precalc), self.sigma_z))
        return np.dot(precalc, precalc2)

    def update_mu_t(self, K, Z):
        precalc = np.dot(self.F, self.mu_t)
        precalc2 = np.dot(K, np.subtract(Z, np.dot(np.dot(self.H, self.F), self.mu_t)))
        self.mu_t = np.add(precalc, precalc2)

    def update_sigma_t(self, K):
        I = np.identity(6)
        precalc = np.subtract(I, np.dot(K, self.H))
        precalc2 = np.add(np.dot(np.dot(self.F, self.sigma_t), self.F.transpose()), self.sigma_x)
        self.sigma_t = np.dot(precalc, precalc2)

    def tick(self, time_diff):
        #print time_diff
        """Some time has passed; decide what to do next."""

        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = mytanks

        if self.mu_t == None:
            self.mu_t = np.zeros([6,1])
            self.mu_t[0] = othertanks[0].x
            self.mu_t[3] = othertanks[0].y

        self.commands = []

        if time_diff >= self.update_time and othertanks[0].status != 'dead':
            if len(othertanks) != 1:
                print 'Must have only one enemy'
                sys.exit(-1)
            Z = np.zeros([2,1]) # get z from enemy tank
            Z[0,0] = float(othertanks[0].x)
            Z[1,0] = float(othertanks[0].y)
            self.update_kalman_filter(Z)
            self.pl.plot(self.sigma_t[0,3], self.sigma_t[0,0], self.sigma_t[3,3], self.mu_t[0,0], self.mu_t[3,0])
            self.update_time += self.delta_t       
        
        self.move_to_position(mytanks[0], self.mu_t[0], self.mu_t[3])
        # if self.attack_state == 'track':
            
        #     if time_diff >= self.kalman_precision_wait:
        #         self.attack_state = 'target'
        #         target_mu = np.array(self.mu_t, copy=True)

        #         for t in range(0, self.look_ahead_steps):
        #             target_mu = np.dot(self.F, target_mu)

        #         self.target_loc = (target_mu[0], target_mu[3])
        #         self.move_to_position(mytanks[0], self.target_loc[0], self.target_loc[1])
                
        #         shotspeed = float(self.constants['shotspeed'])
        #         dist = self.dist(mytanks[0].x - self.target_loc[0], mytanks[0].y - self.target_loc[1])

        #         self.bullet_travel_time = dist / shotspeed
        #         self.enemy_arrive_time = time_diff + self.look_ahead_steps * self.delta_t
        #         self.fire_time = self.enemy_arrive_time - self.bullet_travel_time
            
        #     else:
        #         self.move_to_position(mytanks[0], self.mu_t[0], self.mu_t[3])

        # elif self.attack_state == 'target':
        #     if time_diff >= self.fire_time: 
        #         command = Command(mytanks[0].index, 0, 0, True)
        #         self.commands.append(command)
        #         self.attack_state = ' '
        #     else:
        #         self.move_to_position(mytanks[0], self.target_loc[0], self.target_loc[1])



        results = self.bzrc.do_commands(self.commands)
        self.ticks += 1

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
        command = Command(tank.index, 0, 2 * relative_angle, True)
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
