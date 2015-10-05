
import sys
import math
import time

from bzrc import BZRC, Command

class PotentialFieldsAgent(object):

	def __init__(self, bzrc):
		self.bzrc = bzrc
		self.constants = self.bzrc.get_constants()
		self.commands = []

		self.obstacles = []

		self.goal_field_radius = 50.0
		self.goal_attr_factor = 1
		self.outside_goal_speed = 1.0
		self.prev_angle_error = 0
		self.angle_P = 5
		self.angle_D = 5
		self.obstacle_inner_repulse = 0.6
		self.obstacle_outer_repulse = 0.3
		self.obstacle_radius_extension = 20
		self.inner_tangential_force = 0.6
		self.outer_tangential_force = 0.4
		self.obstacle_outer_radius = 40
		self.mytanks, self.othertanks, self.flags, self.shots = self.bzrc.get_lots_o_stuff()

		self.process_obstacles()

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
			vec = self.calculate_potential_fields(tank)
			target_angle = math.atan2(vec[1], vec[0])
			angle_error = target_angle - tank.angle
			if self.prev_angle_error == 0:
				self.prev_angle_error = angle_error
			relative_angle = self.normalize_angle(angle_error)
			angle_velocity = 0
			if time_diff != 0:
				angle_velocity = self.angle_P * relative_angle + \
					self.angle_D * self.normalize_angle((angle_error - self.prev_angle_error) / time_diff)
				self.prev_angle_error = angle_error


			command = Command(tank.index, self.dist(vec[0], vec[1]), angle_velocity, False)
			self.commands.append(command)

		results = self.bzrc.do_commands(self.commands)

	def calculate_potential_fields(self, tank):
		vec = self.calc_goal_vector(tank)

		ob_vec = self.calc_obstacles_vector(tank)
		vec[0] += ob_vec[0]
		vec[1] += ob_vec[1]

		tan_vec = self.calc_tangential_vector(tank)
		vec[0] += tan_vec[0]
		vec[1] += tan_vec[1]

		return vec[0],vec[1]

	def calc_obstacles_vector(self, tank):
		result_vec = [0,0]
		for obstacle in self.obstacles:

			x_dist = tank.x - obstacle.center[0]
			y_dist = tank.y - obstacle.center[1]

			if self.quick_circle_collision(x_dist, y_dist, obstacle.radius):
				length = self.dist(x_dist, y_dist)
				if length == 0:
					return [0,0]
				normalized_vec = [x_dist / length, y_dist / length]
				result_vec[0] += normalized_vec[0] * self.obstacle_inner_repulse #INFINITE REPULSION
				result_vec[1] += normalized_vec[1] * self.obstacle_inner_repulse
			elif self.quick_circle_collision(x_dist, y_dist, obstacle.radius + self.obstacle_outer_radius):
				length = self.dist(x_dist, y_dist)
				if length == 0:
					return [0,0]
				inner_circle_dist = length - obstacle.radius

				proportion = 1 - inner_circle_dist / self.obstacle_outer_radius
				normalized_vec = [x_dist / length, y_dist / length]
				result_vec[0] += normalized_vec[0] * proportion * self.obstacle_outer_repulse
				result_vec[1] += normalized_vec[1] * proportion * self.obstacle_outer_repulse

				# do the potential field thingy for the obstacle. closer to the edge is 0, closer to obstacle radius is 1

			else:
				continue


		return result_vec

	def calc_tangential_vector(self, tank):
		result_vec = [0,0]
		for obstacle in self.obstacles:

			x_dist = tank.x - obstacle.center[0]
			y_dist = tank.y - obstacle.center[1]

			length = self.dist(x_dist, y_dist)
			if length == 0:
				return [0,0]
			normalized_vec = [x_dist / length, y_dist / length]
			normal_tangent = [-normalized_vec[1], normalized_vec[0]]

			if self.quick_circle_collision(x_dist, y_dist, obstacle.radius):
				result_vec[0] += normal_tangent[0] * self.inner_tangential_force
				result_vec[1] += normal_tangent[1] * self.inner_tangential_force
			elif self.quick_circle_collision(x_dist, y_dist, obstacle.radius + self.goal_field_radius):
				inner_circle_dist = length - obstacle.radius
				proportion = 1 - inner_circle_dist / self.obstacle_outer_radius
				result_vec[0] += normal_tangent[0] * proportion * self.outer_tangential_force
				result_vec[1] += normal_tangent[1] * proportion * self.outer_tangential_force
			else:
				continue


		return result_vec

	def calc_goal_vector(self, tank):

		if tank.flag != '-':
			for base in self.bases:
				if base.color == self.constants['team']:
					goal = ((base.corner3_x + base.corner1_x) / 2,
					(base.corner3_y + base.corner1_y) / 2)

		else:
			for flag in self.flags:
				if flag.poss_color != self.constants['team'] and flag.color != self.constants['team']: #later add closest flag check?
					goal = (flag.x, flag.y)

		x_dist = goal[0] - tank.x
		y_dist = goal[1] - tank.y

		length = self.dist(x_dist, y_dist)

		if length == 0:
			return (0,0)

		proportion = 1
		normalized_vec = [x_dist / length, y_dist / length]
		if self.quick_circle_collision(x_dist, y_dist, self.goal_field_radius):
			proportion = length / self.goal_field_radius
		return [normalized_vec[0] * self.goal_attr_factor * proportion, normalized_vec[1] * self.goal_attr_factor * proportion]


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

	def process_obstacles(self):
		'''
		store obstacles locally
		for each obstacle
			translate to center and rotate corners
			get width and height and divide width by height
			if resulting ratio is greater than 2
				width is larger than height
				counter = 0
				while counter + height < width
					create obstacle
					counter += height
				create obstacle with remaining portion of obstacle
			elif ratio is less than 1/2
				height is larger than width
				counter = 0
				while counter + width < height
					create obstacle
					counter += width
				create obstacle with remaining portion of obstacle
			else
				push obstacle
		'''
		obstacles = self.bzrc.get_obstacles()

		for obstacle in obstacles:
			"""
			transform
			divide
			untransform
			push
			"""
			#transform
			trans_x = 0 - obstacle[0][0]
			trans_y = 0 - obstacle[0][1]
			rot_angle = self.normalize_angle(math.atan2(obstacle[0][0] - obstacle[1][0], obstacle[0][1] - obstacle[1][1]))
			sin_ang = math.sin(rot_angle)
			cos_ang = math.cos(rot_angle)

			trans_points = []
			for i in range(0, len(obstacle)):
				x, y = obstacle[i]
				x = x + trans_x
				y = y + trans_y
				rot_x = x * cos_ang - y * sin_ang
				rot_y = x * sin_ang + y * cos_ang
				trans_points.append([rot_x, rot_y])

			# divide
			ob_wid = math.fabs(trans_points[0][0] - trans_points[3][0])
			ob_hgt = math.fabs(trans_points[0][1] - trans_points[1][1])

			len_to_wid = ob_wid / ob_hgt

			temp_obstacles = []

			if len_to_wid >= 2:
				#length is greater than width
				temp_obstacles = self.divide_obstacle_l(ob_wid, ob_hgt, trans_points)
			elif len_to_wid <= 0.5:
				#width is greater than length
				temp_obstacles = self.divide_obstacle_h(ob_wid, ob_hgt, trans_points)

			#untransform
			for temp_ob in temp_obstacles:
				for corner in temp_ob:
					x, y = corner
					rot_x = x * cos_ang + y * sin_ang
					rot_y = x * -sin_ang + y * cos_ang
					x = rot_x - trans_x
					y = rot_y - trans_y
					corner = [x,y]

			if not temp_obstacles:
				self.create_obstacle(obstacle)
			else:
				print "many"
				for temp_ob in temp_obstacles:
					self.create_obstacle(temp_ob)

	def divide_obstacle_l(self, ob_wid, ob_hgt, trans_points):
		final_obstacle_list = []
		counter = 0
		# make smaller obstacles
		while counter + ob_hgt < ob_wid:
			point1 = [trans_points[0][0] - counter, trans_points[0][1]]
			point2 = [trans_points[1][0] - counter, trans_points[1][1]]
			point3 = [trans_points[1][0] - counter - ob_hgt, trans_points[1][1]]
			point4 = [trans_points[0][0] - counter - ob_hgt, trans_points[0][1]]

			obstacle_points = [point1, point2, point3, point4]

			final_obstacle_list.append(obstacle_points)
			counter = counter + ob_hgt

		# make obstacle with leftover portion
		point1 = [trans_points[0][0] - counter, trans_points[0][1]]
		point2 = [trans_points[1][0] - counter, trans_points[1][1]]

		obstacle_points = [point1, point2, trans_points[2], trans_points[3]]

		final_obstacle_list.append(obstacle_points)

		return final_obstacle_list

	def divide_obstacle_h(self, ob_wid, ob_hgt, trans_points):

		final_obstacle_list = []
		counter = 0
		# make smaller obstacles
		while counter + ob_wid < ob_hgt:
			point1 = [trans_points[0][0], trans_points[0][1] - counter]
			point2 = [trans_points[0][0], trans_points[0][1] - counter - ob_wid]
			point3 = [trans_points[3][0], trans_points[3][1] - counter - ob_wid]
			point4 = [trans_points[3][0], trans_points[3][1] - counter]

			obstacle_points = [point1, point2, point3, point4]

			final_obstacle_list.append(obstacle_points)
			counter = counter + ob_wid

		# make obstacle with leftover portion
		point1 = [trans_points[0][0], trans_points[0][1] - counter]
		point2 = [trans_points[3][0], trans_points[3][1] - counter]

		obstacle_points = [point1, trans_points[1], trans_points[2], point2]

		final_obstacle_list.append(obstacle_points)

		return final_obstacle_list

	def create_obstacle(self, points):
		new_ob = Obstacle()
		new_ob.points = points

		new_ob.center = [(new_ob.points[0][0] + new_ob.points[2][0])/ 2, \
			(new_ob.points[0][1] + new_ob.points[2][1])/ 2]
		new_ob.radius = self.dist(new_ob.center[0] - new_ob.points[0][0], \
			new_ob.center[1] - new_ob.points[0][1]) + self.obstacle_radius_extension

		self.obstacles.append(new_ob)



class Obstacle(object):
	pass
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

	agent = PotentialFieldsAgent(bzrc)

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
