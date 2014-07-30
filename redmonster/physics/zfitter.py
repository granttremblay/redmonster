# Subgrid refinement and error estimation of redshift value found by redmonster.physics.zfinder.py .
# Interpolates both between redshift pixel lags and between model parameters.
#
# Tim Hutchinson, May 2014
# t.hutchinson@utah.edu

import numpy as n
from redmonster.math.misc import quadfit
import matplotlib as m
from matplotlib import pyplot as p
m.interactive(True)
from redmonster.math import grid_spline as gs

class Zfitter:

    def __init__(self, zchi2, zbase):
        self.zchi2 = zchi2
        self.zbase = zbase
        self.best_z = n.zeros(zchi2.shape[0])
        self.z_err = n.zeros(zchi2.shape[0])
        #self.zwarning = zwarning if zwarning else n.zeros(zchi2.shape[0])
        self.zwarning = n.zeros(zchi2.shape[0])

    def z_refine2(self):
        for ifiber in xrange(self.zchi2.shape[0]):
            zminpos = n.where(self.zchi2[ifiber] == n.min(self.zchi2[ifiber]))
            vecpos = ()
            for i in xrange(len(zminpos)-1):
                vecpos += (zminpos[i][0],)
            bestzvec = self.zchi2[(ifiber,)+vecpos]
            posinvec = zminpos[-1][0]
            if (posinvec == 0) or (posinvec == bestzvec.shape[0]-1): # Flag and skip interpolation fit if best chi2 is at edge of z-range
                self.flag_z_fitlimit(ifiber)
                self.best_z[ifiber] = bestzvec[posinvec]
            else:
                xp = n.linspace(self.zbase[posinvec-1], self.zbase[posinvec+1], 1000)
                f = quadfit(self.zbase[posinvec-1:posinvec+2], bestzvec[posinvec-1:posinvec+2])
                fit = quad_for_fit(xp, f[0], f[1], f[2])
                #p.plot(xp, fit, color='red')
                #p.plot(self.zbase[posinvec-1:posinvec+2], bestzvec[posinvec-1:posinvec+2], 'ko', hold=True)
                self.best_z[ifiber] = xp[n.where(fit == n.min(fit))[0][0]]
                self.z_err[ifiber] = self.estimate_z_err(xp, fit)
                #print self.best_z[ifiber]
                self.flag_small_dchi2(ifiber, bestzvec) # Flag fibers with small delta chi2 in redshift

    def z_refine(self):
        for ifiber in xrange(self.zchi2.shape[0]):
            bestzvec = n.zeros( self.zchi2.shape[-1])
            for iz in xrange(self.zchi2.shape[-1]):
                bestzvec[iz] = n.min( self.zchi2[ifiber,...,iz] )
            posinvec = n.where( bestzvec == n.min(bestzvec) )[0][0]
            if (posinvec == 0) or (posinvec == bestzvec.shape[0]-1): # Flag and skip interpolation fit if best chi2 is at edge of z-range
                self.flag_z_fitlimit(ifiber)
                self.best_z[ifiber] = -1.
                self.z_err[ifiber] = -1.
            else:
                xp = n.linspace(self.zbase[posinvec-1], self.zbase[posinvec+1], 1000)
                f = quadfit(self.zbase[posinvec-1:posinvec+2], bestzvec[posinvec-1:posinvec+2])
                fit = quad_for_fit(xp, f[0], f[1], f[2])
                p.plot(xp, fit, color='red')
                p.plot(self.zbase[posinvec-1:posinvec+2], bestzvec[posinvec-1:posinvec+2], 'ko', hold=False)
                self.best_z[ifiber] = xp[n.where(fit == n.min(fit))[0][0]]
                self.z_err[ifiber] = self.estimate_z_err(xp, fit)
                #print self.best_z[ifiber]
                self.flag_small_dchi2(ifiber, bestzvec) # Flag fibers with small delta chi2 in redshift

    def estimate_z_err(self, xp, fit):
        fitminloc = n.where(fit == n.min(fit)) # Index of lowest chi2
        z_err = abs(xp[fitminloc]-xp[abs(n.min(fit)+1-fit).argmin()]) # abs() of difference between z_(chi2_min) and z_(chi2_min_+1)
        return z_err

    def flag_small_dchi2(self, ifiber, zvector, threshold=46.6, width=15): # zvector: vector of chi2(z) values of best template
        flag_val = int('0b100',2) # From BOSS zwarning flag definitions
        do_flag = False
        globminloc = n.where(zvector == n.min(zvector))[0][0]
        globmin = zvector[globminloc]
        zspline = gs.GridSpline(zvector)
        zminlocs = n.round(zspline.get_min())
        zminvals = zspline.get_val(zminlocs)
        small_dchi2 = n.where(zminvals < (globmin+threshold))[0]
        if len(small_dchi2) > 0:
            for i in small_dchi2:
                if abs(zminvals[i] - globminloc) < threshold: do_flag = False
        if do_flag: self.zwarning[ifiber] = int(self.zwarning[ifiber]) ^ flag_val

    def flag_z_fitlimit(self, ifiber):
        flag_val = int('0b100000',2) # From BOSS zwarning flag definitions
        self.zwarning[ifiber] = int(self.zwarning[ifiber]) ^ flag_val


# -----------------------------------------------------------------------------

def quad_for_fit(x, a, b, c):
    return a*(x**2) + b*x + c