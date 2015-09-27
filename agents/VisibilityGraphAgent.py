import sys
import math
import time

from bzrc import BZRC, Command

class VisibilityGraphAgent(object):
    """Class handles all command and control logic for a teams tanks."""

    def __init__(self, bzrc):
        self.bzrc = bzrc
        self.constants = self.bzrc.get_constants()
        self.commands = []
        self.visibilityGraph = {}
        self.init_graph()

    def init_graph(self):
        flags = self.bzrc.get_flags()
        self.obstacles = self.bzrc.get_obstacles()


        for flag in flags:
            self.visibilityGraph[(flag.x, flag.y)] = {}
            for key in self.visibilityGraph.keys():
                distance = math.sqrt(math.pow(key[0] - flag.x, 2) + math.pow(key[1] - flag.y, 2))
                self.visibilityGraph[key][(flag.x, flag.y)] = distance
                self.visibilityGraph[(flag.x, flag.y)][key] = distance

        for obstacle in self.obstacles:
            for corner in obstacle:
                self.visibilityGraph[corner] = {}
                for key in self.visibilityGraph.keys():
                    distance = math.sqrt(math.pow(key[0] - corner[0], 2) + math.pow(key[1] - corner[1], 2))
                    self.visibilityGraph[corner][key] = distance
                    self.visibilityGraph[key][corner] = distance

        self.removeEdges()
        print self.visibilityGraph

    def removeEdges(self):
        points = self.visibilityGraph.keys()
        for pi in range(0, len(points)):
            pnt1 = points[pi]
            for pj in range(0, pi):
                pnt2 = points[pj]
                for obstacle in self.obstacles:
                    for oi in range(0, len(obstacle)):
                        edge1 = obstacle[oi]
                        edge2 = obstacle[(oi + 1) % len(obstacle)]
                        if self.intersects(edge1, edge2, pnt1, pnt2):
                            self.visibilityGraph[pnt1][pnt2] = 0.0
                            self.visibilityGraph[pnt2][pnt1] = 0.0
                    self.visibilityGraph[obstacle[0]][obstacle[2]] = 0.0
                    self.visibilityGraph[obstacle[2]][obstacle[0]] = 0.0
                    self.visibilityGraph[obstacle[1]][obstacle[3]] = 0.0
                    self.visibilityGraph[obstacle[3]][obstacle[1]] = 0.0

                # remove edge if it intersects with an obstacle

    def intersects(self, edge1, edge2, point1, point2):
        #if the edges are the same, return false
        if edge1 == point1 and edge2 == point2 or edge1 == point2 and edge2 == point1:
            return False
        edet1 = (edge2[0] - edge1[0]) * (point1[1] - edge1[1]) - (edge2[1] - edge1[1]) * (point1[0] - edge1[0])
        edet2 = (edge2[0] - edge1[0]) * (point2[1] - edge1[1]) - (edge2[1] - edge1[1]) * (point2[0] - edge1[0])

        pdet1 = (point2[0] - point1[0]) * (edge1[1] - point1[1]) - (point2[1] - point1[1]) * (edge1[0] - point1[0])
        pdet2 = (point2[0] - point1[0]) * (edge2[1] - point1[1]) - (point2[1] - point1[1]) * (edge2[0] - point1[0])

        if (edet1 >= 0 and edet2 <= 0 or edet1 <= 0 and edet2 >= 0) and (pdet1 > 0 and pdet2 < 0 or pdet1 < 0 and pdet2 > 0):
            return True
        if (edet1 > 0 and edet2 < 0 or edet1 < 0 and edet2 > 0) and (pdet1 >= 0 and pdet2 <= 0 or pdet1 <= 0 and pdet2 >= 0):
            return True
        return False

    def tick(self, time_diff):
        """Some time has passed; decide what to do next."""
        mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
        self.mytanks = mytanks
        self.othertanks = othertanks
        self.flags = flags
        self.shots = shots
        self.enemies = [tank for tank in othertanks if tank.color !=
                        self.constants['team']]

        self.commands = []

        for tank in mytanks:
            self.attack_enemies(tank)

        results = self.bzrc.do_commands(self.commands)

    # def attack_enemies(self, tank):
    #     """Find the closest enemy and chase it, shooting as you go."""
    #     best_enemy = None
    #     best_dist = 2 * float(self.constants['worldsize'])
    #     for enemy in self.enemies:
    #         if enemy.status != 'alive':
    #             continue
    #         dist = math.sqrt((enemy.x - tank.x)**2 + (enemy.y - tank.y)**2)
    #         if dist < best_dist:
    #             best_dist = dist
    #             best_enemy = enemy
    #     if best_enemy is None:
    #         command = Command(tank.index, 0, 0, False)
    #         self.commands.append(command)
    #     else:
    #         self.move_to_position(tank, best_enemy.x, best_enemy.y)
    #
    # def move_to_position(self, tank, target_x, target_y):
    #     """Set command to move to given coordinates."""
    #     target_angle = math.atan2(target_y - tank.y,
    #                               target_x - tank.x)
    #     relative_angle = self.normalize_angle(target_angle - tank.angle)
    #     command = Command(tank.index, 1, 2 * relative_angle, True)
    #     self.commands.append(command)
    #
    # def normalize_angle(self, angle):
    #     """Make any angle be between +/- pi."""
    #     angle -= 2 * math.pi * int (angle / (2 * math.pi))
    #     if angle <= -math.pi:
    #         angle += 2 * math.pi
    #     elif angle > math.pi:
    #         angle -= 2 * math.pi
    #     return angle


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

    agent = VisibilityGraphAgent(bzrc)

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
