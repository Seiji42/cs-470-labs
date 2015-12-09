
from Gnuplot import GnuplotProcess

class GnuPlotter(object):

    def __init__(self):
        self.gnuprocess = GnuplotProcess(persist=False)
        self.gnuprocess.write(self.plot_file_base())


    def plot_file_base(self):
        header = ''
        header += "set xrange [-400.0: 400.0]\n"
        header += "set yrange [-400.0: 400.0]\n"
        header += "set pm3d\n"
        header += "set view map\n"
        header += "unset key\n"
        header += "set size square\n\n"

        header += "set palette model RGB functions 1-gray, 1-gray, 1-gray\n"
        header += "set isosamples 100\n"

        return header

    def plot(self,rho,sigma_x,sigma_y, x, y):

        # print rho
        # print sigma_x
        # print sigma_y
        # print x
        # print y
        plot = ''
        plot += "sigma_x = %f\n" % sigma_x
        plot += "sigma_y = %f\n" % sigma_y
        plot += "mu_x = %f\n" % x
        plot += "mu_y = %f\n" % y
        plot += "rho = %f\n" % rho
        plot += "splot 1.0/(2.0 * pi * sigma_x * sigma_y * sqrt(1 - rho**2) ) \\\n"
        plot += "* exp(-1.0/2.0 * ((x-mu_x)**2 / sigma_x**2 + (y-mu_y)**2 / sigma_y**2 \\\n"
        plot += "- 2.0*rho*x*y/(sigma_x*sigma_y) ) ) with pm3d\n\n"
        
        self.gnuprocess.write(plot)
        self.gnuprocess.flush()

    def remove(self):
        self.gnuprocess.write('exit')
        self.gnuprocess.flush()


