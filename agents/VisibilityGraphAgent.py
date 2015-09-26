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
        obstacles = self.bzrc.get_obstacles()

        for flag in flags:
            self.visibilityGraph[(flag.x, flag.y)] = {}
            for key in self.visibilityGraph.keys():
                self.visibilityGraph[key][(flag.x, flag.y)] = 0
                self.visibilityGraph[(flag.x, flag.y)][key] = 0

        for obstacle in obstacles:
            for corner in obstacle:
                self.visibilityGraph[corner] = {}
                for key in self.visibilityGraph.keys():
                    self.visibilityGraph[corner][key] = 0
                    self.visibilityGraph[key][corner] = 0


        self.addObstacles(obstacles)
        self.addEdges()
        print self.visibilityGraph

    def addEdges(self):
        keys = self.visibilityGraph.keys()
        for i in range(0, len(keys)):
            for j in range (0, i):
                point1 = keys[i]
                point2 = keys[j]
                edgeVector = (point2[0]-point1[0], point2[1]-point1[1]) # translate to origin
                addEdge = True
                for key1 in self.visibilityGraph.keys():
                    for key2 in self.visibilityGraph.keys():
                        if self.visibilityGraph[key1][key2] > 0:
                            #translate points
                            keypoint1 = (key1[0]-point1[0], key1[1]-point1[1])
                            keypoint2 = (key2[0]-point1[0], key2[1]-point1[1])
                            if self.linesCross(keypoint1, keypoint2, edgeVector):
                                addEdge = False
                                break
                    if not addEdge:
                        break
                if addEdge:
                    distance = math.sqrt(math.pow(point1[0] - point2[0], 2) + math.pow(point1[1] - point2[1], 2))
                    self.visibilityGraph[point1][point2] = distance
                    self.visibilityGraph[point2][point1] = distance

    def linesCross(self, point1, point2, edge):
        dot1 = edge[0] * point1[0] + edge[1] * point1[1]
        dot2 = edge[0] * point2[0] + edge[1] * point2[1]

        #if dotproduct signs are different, the lines cross
        return dot1 <= 0 and dot2 >= 0 or dot1 >= 0 and dot2 <= 0

    def addObstacles(self, obstacles):
        for i in range(0, len(obstacles)):
            obstacle = obstacles[i]
            for j in range(0, len(obstacle)):
                cor = obstacle[j]
                for k in range(0, j):
                    cor2 = obstacle[k]
                    if cor2[0] != cor[0] and cor2[1] != cor[1]:
                        continue # if corners are oposite corners, skip
                    distance = math.sqrt(math.pow(cor2[0] - cor[0], 2) + math.pow(cor2[1] - cor[1], 2))
                    self.visibilityGraph[cor][cor2] = distance
                    self.visibilityGraph[cor2][cor] = distance

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
