
import sys
import math
import time

from bzrc import BZRC, Command

class PotentialFieldsAgent(object):

	def __init__(self, bzrc, color):
		self.bzrc = bzrc
		self.constants = self.bzrc.get_constants()
		self.commands = []

		self.goal_field_radius = 30.0
		self.outside_goal_speed = 1.0
		self.color = color

	def tick(self, time_diff):
		"""Some time has passed; decide what to do next."""
		mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
		self.mytanks = mytanks
		self.othertanks = othertanks
		self.flags = flags
		self.shots = shots
		self.bases = self.bzrc.get_bases()
		self.commands = []


		self.calculate_potential_fields(mytanks[0])

		results = self.bzrc.do_commands(self.commands)

	def calculate_potential_fields(self, tank):


		vec = self.get_goal_vector(tank)
		print vec
		target_angle = math.atan2(vec[1], vec[0])
		relative_angle = self.normalize_angle(target_angle - tank.angle)



		command = Command(tank.index, self.dist(vec[0], vec[1]), 2 * relative_angle, False)
		self.commands.append(command)

	def get_goal_vector(self, tank):

		#print tank.flag
		if tank.flag != '-':
			for base in self.bases:
				if base.color == self.color:
					goal = ((base.corner3_x + base.corner1_x) / 2,
					(base.corner3_y + base.corner1_y) / 2)

		else:
			for flag in self.flags:
				if flag.poss_color != self.color and flag.color != self.color: #later add closest flag check?
					goal = (flag.x, flag.y)

		#print "goal ", goal
		x_dist = goal[0] - tank.x
		y_dist = goal[1] - tank.y

		#print x_dist
		#print y_dist

		length = self.dist(x_dist, y_dist)

		if length == 0:
			return (0,0)

		normalized_vec = [x_dist / length, y_dist / length]
		if self.quick_circle_collision(x_dist, y_dist, self.goal_field_radius):
			normalized_vec[0] = normalized_vec[0] / self.goal_field_radius
			normalized_vec[1] = normalized_vec[1] / self.goal_field_radius

		#print 'norm ', normalized_vec
		return normalized_vec


	def move_to_position(self, tank, target_x, target_y):
		"""Set command to move to given coordinates."""
		target_angle = math.atan2(target_y - tank.y,
									target_x - tank.x)
		relative_angle = self.normalize_angle(target_angle - tank.angle)
		command = Command(tank.index, 1, 2 * relative_angle, True)
		self.commands.append(command)

	def normalize_angle(self, angle):
		"""Make any angle be between +/- pi."""
		angle -= 2 * math.pi * int (angle / (2 * math.pi))
		if angle <= -math.pi:
			angle += 2 * math.pi
		elif angle > math.pi:
			angle -= 2 * math.pi
		return angle

	def dist(self, x, y):
		return math.sqrt(x * x + y * y)

	def quick_circle_collision(self, x, y, radius):
		return radius * radius >= x * x + y * y;


def main():
	# Process CLI arguments.
	try:
		execname, host, port, color = sys.argv
	except ValueError:
		execname = sys.argv[0]
		print >>sys.stderr, '%s: incorrect number of arguments' % execname
		print >>sys.stderr, 'usage: %s hostname port' % sys.argv[0]
		sys.exit(-1)

	# Connect.
	#bzrc = BZRC(host, int(port), debug=True)
	bzrc = BZRC(host, int(port))

	agent = PotentialFieldsAgent(bzrc, color)

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
