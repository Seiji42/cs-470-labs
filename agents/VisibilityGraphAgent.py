
import sys
import math
import time

from bzrc import BZRC, Command
from astarsearch import AStarSearch
from depthfirstsearch import DepthFirstSearch
from breadthfirstsearch import BreadthFirstSearch

class VisibilityGraphAgent(object):

	def __init__(self, bzrc, search):
		self.bzrc = bzrc
		self.constants = self.bzrc.get_constants()
		self.commands = []
		self.goal_point_radius = 30.0
		self.goal_field_radius = 30.0
		self.goal_attr_factor = 1
		self.outside_goal_speed = 1.0
		self.prev_angle_error = 0
		self.angle_P = 5
		self.angle_D = 5
		self.obstacle_inner_repulse = 0.7
		self.obstacle_outer_repulse = 0.5
		self.obstacle_outer_radius = 40
		self.inner_tangential_force = 0.3
		self.outer_tangential_force = 0.2

		self.visibilityGraph = {}
		self.curr_goal_point = None
		self.mytanks, self.othertanks, self.flags, self.shots = self.bzrc.get_lots_o_stuff()

		self.process_obstacles()
		self.goal = self.getGoal(self.flags, self.constants)
		self.goal = (self.goal.x, self.goal.y)
		self.position = (self.mytanks[0].x, self.mytanks[0].y)
		self.search = search
		self.search.obstacles = self.obstacles
		self.init_graph(self.position, self.goal)

	def init_graph(self, start, goal):
		flags = self.bzrc.get_flags()
		self.graph_obstacles = self.bzrc.get_obstacles()

		self.visibilityGraph[start] = {}
		self.visibilityGraph[start][start] = 0

		self.visibilityGraph[goal] = {}
		self.visibilityGraph[goal][goal] = 0

		distance = math.sqrt(math.pow(start[0] - goal[0], 2) + math.pow(start[1] - goal[1], 2))
		self.visibilityGraph[start][goal] = distance
		self.visibilityGraph[goal][start] = distance

		for obstacle in self.graph_obstacles:
			for corner in obstacle:
				self.visibilityGraph[corner] = {}
				for key in self.visibilityGraph.keys():
					distance = math.sqrt(math.pow(key[0] - corner[0], 2) + math.pow(key[1] - corner[1], 2))
					self.visibilityGraph[corner][key] = distance
					self.visibilityGraph[key][corner] = distance

		self.removeEdges()
		self.path = self.search.search(self.visibilityGraph, start, goal)
		total_cost = 0
		for point in range(0, len(self.path) - 1):
			total_cost = total_cost + self.visibilityGraph[self.path[point]][self.path[point + 1]]
		print total_cost


	def removeEdges(self):
		points = self.visibilityGraph.keys()
		for pi in range(0, len(points)):
			pnt1 = points[pi]
			for pj in range(0, pi):
				pnt2 = points[pj]
				for obstacle in self.graph_obstacles:
					for oi in range(0, len(obstacle)):
						edge1 = obstacle[oi]
						edge2 = obstacle[(oi + 1) % len(obstacle)]
						if self.intersects(edge1, edge2, pnt1, pnt2):
							self.visibilityGraph[pnt1][pnt2] = 0.0
							self.visibilityGraph[pnt2][pnt1] = 0.0
						if edge1[0] == edge2[0] and math.fabs(edge1[0]) == 400 \
							or edge1[1] == edge2[1] and math.fabs(edge1[1]) == 400:
							self.visibilityGraph[edge1][edge2] = 0.0
							self.visibilityGraph[edge2][edge1] = 0.0
					self.visibilityGraph[obstacle[0]][obstacle[2]] = 0.0
					self.visibilityGraph[obstacle[2]][obstacle[0]] = 0.0
					self.visibilityGraph[obstacle[1]][obstacle[3]] = 0.0
					self.visibilityGraph[obstacle[3]][obstacle[1]] = 0.0
					#check to see if edge is on edge of world
					#if so, remove

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
		self.bases = self.bzrc.get_bases()
		self.commands = []

		if not self.curr_goal_point:
			self.curr_goal_point = self.path.pop(len(self.path) - 1)

		if self.quick_circle_collision(mytanks[0].x - self.curr_goal_point[0], mytanks[0].y - self.curr_goal_point[1], self.goal_point_radius):
			self.curr_goal_point = self.path.pop(len(self.path) - 1)

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

	def getGoal(self, flags, constants):
		for flag in flags:
			if flag.color != constants['team']:
				return flag

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
			elif self.quick_circle_collision(x_dist, y_dist, obstacle.radius + self.obstacle_outer_radius):
				inner_circle_dist = length - obstacle.radius
				proportion = 1 - inner_circle_dist / self.obstacle_outer_radius
				result_vec[0] += normal_tangent[0] * proportion * self.outer_tangential_force
				result_vec[1] += normal_tangent[1] * proportion * self.outer_tangential_force
			else:
				continue


		return result_vec

	def calc_goal_vector(self, tank):

		#print "goal ", goal
		x_dist = self.curr_goal_point[0] - tank.x
		y_dist = self.curr_goal_point[1] - tank.y

		#print x_dist
		#print y_dist

		length = self.dist(x_dist, y_dist)

		if length == 0:
			return (0,0)

		proportion = 1
		normalized_vec = [x_dist / length, y_dist / length]
		if self.quick_circle_collision(x_dist, y_dist, self.goal_field_radius):
			proportion = length / self.goal_field_radius
		if proportion != 1:
			print 'proportion', proportion
		#print 'norm ', normalized_vec
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
		obstacles = self.bzrc.get_obstacles()
		self.obstacles = []

		for obstacle in obstacles:
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
				for i in range(0, len(temp_ob)):
					x, y = temp_ob[i]
					rot_x = x * cos_ang + y * sin_ang
					rot_y = x * -sin_ang + y * cos_ang
					x = rot_x - trans_x
					y = rot_y - trans_y
					temp_ob[i] = [x,y]

			if not temp_obstacles:
				self.create_obstacle(obstacle)
			else:
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
			new_ob.center[1] - new_ob.points[0][1])

		self.obstacles.append(new_ob)

class Obstacle(object):
	pass
def main():
	# Process CLI arguments.
	try:
		execname, host, port, search = sys.argv
	except ValueError:
		execname = sys.argv[0]
		print >>sys.stderr, '%s: incorrect number of arguments' % execname
		print >>sys.stderr, 'usage: %s hostname port' % sys.argv[0]
		sys.exit(-1)

	# Connect.
	#bzrc = BZRC(host, int(port), debug=True)
	bzrc = BZRC(host, int(port))

	if search == 'b':
		agent = VisibilityGraphAgent(bzrc, BreadthFirstSearch(False))
	elif search == 'd':
		agent = VisibilityGraphAgent(bzrc, DepthFirstSearch(False))
	elif search == 'a':
		agent = VisibilityGraphAgent(bzrc, AStarSearch(False))
	else:
		print >>sys.stderr, 'bad search value. must be a d or b'
		sys.exit(-1)

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




'''
heuristic changes
Manhattan
	-takes less steps than euclidian distance on simple map

random number between 500 and 600 *not admissible*

other things we can do:
euclidian of one step in advance


greedy breadth/depth search

depth limited search
'''
