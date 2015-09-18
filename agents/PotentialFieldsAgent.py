
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
		self.prev_angle_error = 0
		self.angle_P = 5
		self.angle_D = 5

		self.get_obstacles()

	def tick(self, time_diff):
		"""Some time has passed; decide what to do next."""
		mytanks, othertanks, flags, shots = self.bzrc.get_lots_o_stuff()
		self.mytanks = mytanks
		self.othertanks = othertanks
		self.flags = flags
		self.shots = shots
		self.bases = self.bzrc.get_bases()
		self.commands = []

		for tank in self.mytanks:
			self.calculate_potential_fields(tank, time_diff)

		results = self.bzrc.do_commands(self.commands)

	def calculate_potential_fields(self, tank, time_diff):

		vec = self.get_goal_vector(tank)
		ob_vec = self.calc_obstacles_vector(tank)
		vec[0] += ob_vec[0]
		vec[1] += ob_vec[1]
		#print vec
		target_angle = math.atan2(vec[1], vec[0])
		angle_error = target_angle - tank.angle
		if self.prev_angle_error == 0:
			self.prev_angle_error = angle_error
		relative_angle = self.normalize_angle(angle_error)
		print time_diff
		angle_velocity = 0
		if time_diff != 0:
			angle_velocity = self.angle_P * relative_angle + \
				self.angle_D * self.normalize_angle((angle_error - self.prev_angle_error) / time_diff)
			self.prev_angle_error = angle_error

		print angle_velocity

		command = Command(tank.index, self.dist(vec[0], vec[1]), angle_velocity, False)
		self.commands.append(command)

	def calc_obstacles_vector(self, tank):
		result_vec = [0,0]
		for obstacle in self.obstacles:
			x_dist = tank.x - obstacle.center[0]
			y_dist = tank.y - obstacle.center[1]
			if self.quick_circle_collision(x_dist, y_dist, obstacle.radius):
				result_vec[0] += x_dist * 1000 #INFINITE REPULSION
				result_vec[1] += y_dist * 1000
			elif self.quick_circle_collision(x_dist, y_dist, obstacle.radius + self.goal_field_radius):
				length = self.dist(x_dist, y_dist)
				inner_circle_dist = length - self.goal_field_radius

				if inner_circle_dist == 0:
					return (0,0)
				proportion = 1 - inner_circle_dist / self.goal_field_radius
				normalized_vec = [x_dist / length, y_dist / length]
				result_vec[0] += normalized_vec[0] * proportion
				result_vec[1] += normalized_vec[1] * proportion

				# do the potential field thingy for the obstacle. closer to the edge is 0, closer to obstacle radius is 1

			else:
				continue
			# add vector to result vector


	def get_obstacles(self):
		obstacles = self.bzrc.get_obstacles()
		self.obstacles = []
		for obstacle in obstacles:
			obstacle.center = [(obstacle[0][0] + obstacle[2][0])/ 2, (obstacle[0][1] + obstacle[2][1])/ 2]
			obstacle.radius = self.dist(obstacle.center[0] - obstacle[0][0], obstacle.center[1] - obstacle[0][1])
			self.obstacles.append(obstacle)
	# 		length = self.dist(obsacle.corner1_x - obstacle.corner2_x, obsacle.corner1_y - obstacle.corner2_y)
	# 		width = self.dist(obsacle.corner1_x - obstacle.corner4_x, obsacle.corner1_y - obstacle.corner4_y)
	#
	# 		long_Side = max(length, width)
			"""

		if obtacle is not squarish, divide into many squarish obstacles

		determine shorter side (length vs width)
		divide longer by shorter
		if value is greater than 2

			divide obstacle into sections based on the ratio of long side to short side
		else
			make a circle around obstacle
		"""



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
			prev_time = time.time()
			agent.tick(time_diff)
	except KeyboardInterrupt:
		print "Exiting due to keyboard interrupt."
		bzrc.close()


if __name__ == '__main__':
	main()

# vim: et sw=4 sts=4
