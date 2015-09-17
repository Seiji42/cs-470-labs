import sys
import math
import time

from bzrc import BZRC, Command

class DumbAgent:
    def __init__(self, bzrc, botid):
        self.bzrc = bzrc
        self.botid = botid
        self.lastTurn = 0
        self.targetAngle = 0
        self.constants = self.bzrc.get_constants()
        self.commands = []

    def tick(self, time_diff):

        self.commands = []
        shoot = False

        if time_diff % 2 <= 0.5 or time_diff % 2 >= 1.5:
            shoot = True

        tank = self.bzrc.get_mytanks()[self.botid]
        if time_diff % 8 <= 0.1 or time_diff % 8 >= 7.9:
            self.targetAngle = tank.angle + math.pi / 3

        relative_angle = self.normalize_angle(self.targetAngle - tank.angle)
        print relative_angle
        command = Command(tank.index, 1, 2 * relative_angle, shoot)
        self.commands.append(command)

        results = self.bzrc.do_commands(self.commands)

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

    agent = DumbAgent(bzrc,0)

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
