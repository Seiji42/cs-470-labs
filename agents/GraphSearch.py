import matplotlib
import matplotlib.pyplot as plt

class GraphSearch(object):

    def __init__(self, plot):
        self.plot = plot
        self.plot_count = 1

    def plot_obstacles(self, ax):
        for obstacle in self.obstacles:
            obs = obstacle.points
            rect1 = matplotlib.patches.Rectangle((obs[1][0],obs[1][1]), \
                obs[2][0] - obs[1][0], obs[0][1] - obs[1][1], color='blue')
            ax.add_patch(rect1)

    def plot_graph(self,frontier, discovered, came_from, search_name):
        fig = plt.figure(self.plot_count)
        ax = fig.add_subplot(111)
        self.plot_obstacles(ax)
        self.plot_points(frontier, ax, 'ks')
        self.plot_points(discovered, ax, 'mH')
        self.plot_came_from(came_from, ax)
        name = search_name + str(self.plot_count) + '.png'
        plt.title(search_name + str(self.plot_count))
        fig.savefig('visibility_plots/' + name)   # save the figure to file
        plt.close(fig)
        self.plot_count = self.plot_count + 1

    def plot_came_from(self, came_from, ax):
        for key in came_from.keys():
            arrow = matplotlib.patches.Arrow(key[0], key[1], came_from[key][0] - key[0], came_from[key][1] - key[1], width=1.0, color='red')
            ax.add_patch(arrow)

    def plot_points(self, points, ax, style):
        for p in points:
            ax.plot([p[0]], [p[1]], style, ms=10)
