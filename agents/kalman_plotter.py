
class GnuPlotter(object):

    def __init__(self,filename):
        self.file_name = filename
        f = open(self.file_name, 'w+')
        f.write("set xrange [-400.0: 400.0]\n")
        f.write("set yrange [-400.0: 400.0]\n")
        f.write("set pm3d\n")
        f.write("set view map\n")
        f.write("unset key\n")
        f.write("set size square\n\n")

        # f.write("unset arrow\n")
        # f.write("set arrow from 0, 0 to -150, 0 nohead front lt 3\n")
        # f.write("set arrow from -150, 0 to -150, -50 nohead front lt 3\n")
        # f.write("set arrow from -150, -50 to 0, -50 nohead front lt 3\n")
        # f.write("set arrow from 0, -50 to 0, 0 nohead front lt 3\n")
        # f.write("set arrow from 200, 100 to 200, 330 nohead front lt 3\n")
        # f.write("set arrow from 200, 330 to 300, 330 nohead front lt 3\n")
        # f.write("set arrow from 300, 330 to 300, 100 nohead front lt 3\n")
        # f.write("set arrow from 300, 100 to 200, 100 nohead front lt 3\n")

        f.write("set palette model RGB functions 1-gray, 1-gray, 1-gray\n")
        f.write("set isosamples 100\n")

        f.close()

    def plot(self,rho,sigma_x,sigma_y, x, y):

        f = open(self.file_name, 'a')
        f.write("sigma_x = %f\n" % sigma_x)
        f.write("sigma_y = %f\n" % sigma_y)
        f.write("mu_x = %f\n" % x)
        f.write("mu_y = %f\n" % y)
        f.write("rho = %f\n" % rho)
        f.write("splot 1.0/(2.0 * pi * sigma_x * sigma_y * sqrt(1 - rho**2) ) \\\n")
        f.write("* exp(-1.0/2.0 * ((x-mu_x)**2 / sigma_x**2 + (y-mu_y)**2 / sigma_y**2 \\\n")
        f.write("- 2.0*rho*x*y/(sigma_x*sigma_y) ) ) with pm3d\n\n")
        f.close()
