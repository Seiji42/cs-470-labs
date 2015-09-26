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
        # self.addObstacles()
        # self.addEdges()
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

                # remove edge if it intersects with an obstacle

    def intersects(self, edge1, edge2, point1, point2):
        #if the edges are the same, return false
        if edge1 == point1 and edge2 == point2 or edge1 == point2 and edge2 == point1:
            return False
        edet1 = (edge2[0] - edge1[0]) * (point1[1] - edge1[1]) - (edge2[1] - edge1[1]) * (point1[0] - edge1[0])
        edet2 = (edge2[0] - edge1[0]) * (point2[1] - edge1[1]) - (edge2[1] - edge1[1]) * (point2[0] - edge1[0])

        pdet1 = (point2[0] - point1[0]) * (edge1[1] - point1[1]) - (point2[1] - point1[1]) * (edge1[0] - point1[0])
        pdet2 = (point2[0] - point1[0]) * (edge2[1] - point1[1]) - (point2[1] - point1[1]) * (edge2[0] - point1[0])

        if (edet1 >= 0 and edet2 >= 0) or (edet1 <= 0 and edet2 <= 0) or (pdet1 >= 0 and pdet2 >= 0) or (pdet1 <= 0 and pdet2 <=     0):
            return False
        # elif (det1 > 0 and det2 < 0) or (det1 < 0 and det2 > 0):
        #     return True
        else:
            #if both match, return False
            #if one matches ?
            #if none match return false
            #need to figure this out quick
            return True
    # def addObstacles(self):
    #     """
    #     loop through the obstacles
    #         loop through the corners
    #             make edge to connecting corners
    #             loop through previous obstacles
    #                 loop through previous obstacle corners
    #                     try to add new edge
    #     """
    #     # used later to reduce number of comparisons between obstacles
    #     #loop through obstacles
    #     for oi in range(0, len(self.obstacles)):
    #         obstacle = self.obstacles[oi]
    #         #loop through corners
    #         for ci in range(0, len(obstacle)):
    #             cnr = obstacle[ci]
    #             #loop through previous corners
    #             for cj in range(0, ci):
    #                 cnr2 = obstacle[cj]
    #                 #skip edge if corners are not adjacent
    #                 if cnr2[0] != cnr[0] and cnr2[1] != cnr[1]:
    #                     continue
    #                 #add euclidean distance as huristic
    #                 distance = math.sqrt(math.pow(cnr2[0] - cnr[0], 2) + math.pow(cnr2[1] - cnr[1], 2))
    #                 self.visibilityGraph[cnr][cnr2] = distance
    #                 self.visibilityGraph[cnr2][cnr] = distance
    #             #loop through previous obstacles
    #             for oj in range(0, oi):
    #                 obstacle2 = self.obstacles[oj]
    #                 for c2i in range(0, len(obstacle2)):
    #                     prev_cnr = obstacle2[c2i]
    #                     #check that the corners aren't the same
    #                     if prev_cnr != cnr:
    #                         self.addEdge(cnr, prev_cnr)
    #
    # def addEdge(self, new_pnt, old_pnt):
    #     """
    #     loop through all obstacle edges
    #         check to see if new edge intersects with obstacle edge
    #     if doesn't intersect with any obstacle edge, add edge
    #     """
    #
    #     addEdge = True
    #     # print "new_pnt " + str(new_pnt)
    #     # print "old_pnt " + str(old_pnt)
    #
    #     for oi in range(0, len(self.obstacles)):
    #
    #         obstacle = self.obstacles[oi]
    #         #loop through corners
    #         for ci in range(0, len(obstacle)):
    #             cnr = obstacle[ci]
    #             cnr2 = obstacle[(ci + 1) % len(obstacle)]
    #
    #             # print "cnr " + str(cnr)
    #             #
    #             # print "cnr2 " + str(cnr2)
    #             # print str(self.linesCross(cnr, cnr2, new_pnt, old_pnt))
    #             if(self.linesCross(cnr, cnr2, new_pnt, old_pnt)):
    #                 addEdge = False
    #                 break
    #         if not addEdge:
    #             break
    #
    #     if addEdge:
    #         distance = math.sqrt(math.pow(old_pnt[0] - new_pnt[0], 2) + math.pow(old_pnt[1] - new_pnt[1], 2))
    #         self.visibilityGraph[new_pnt][old_pnt] = distance
    #         self.visibilityGraph[old_pnt][new_pnt] = distance
    #
    #     # loop through visibilityGraph to see if edge can be added
    # def linesCross(self, edge1, edge2, pnt1, pnt2):
    #     share_point = edge1 == pnt1 or edge1 == pnt2 or edge2 == pnt1 or edge2 == pnt2
    #     # if they don't share points, just check for sign being completely oposite
    #     # if they do share points
    #     # use share_point to determine which check to use
    #     edge_vect = (edge2[0] - edge1[0], edge2[1] - edge1[1])
    #     pnt1_vect = (pnt1[0] - edge1[0], pnt1[1] - edge1[1])
    #     pnt2_vect = (pnt2[0] - edge1[0], pnt2[1] - edge1[1])
    #
    #     det1 = edge_vect[0] * pnt1_vect[1] - edge_vect[1] * pnt1_vect[0]
    #     print det1
    #     det2 = edge_vect[0] * pnt2_vect[1] - edge_vect[1] * pnt2_vect[0]
    #     print det2
    #
    #     if det1 < 0 and det2 > 0 or det1 > 0 and det2 < 0:
    #         print "opposite"
    #         return True
    #     elif det1 > 0 and det2 > 0 or det1 < 0 and det2 < 0:
    #         print "same"
    #         return False
    #     else:
    #         print "?"
    #         return False
    #     # elif det1 == 0 and det2 == 0:
    #     #     return share_point
    #     # else:
    #     #     return not share_point

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
