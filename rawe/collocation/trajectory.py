import matplotlib.pyplot as plt
import pickle
import numpy as np

import casadi as C
import collmaps

class Trajectory(object):
    """
    Trajectory contains x/z/u/p collmap, and output map and quadrature map.
    It can lookup values from these things.
    It is the thing which is saved and loaded.
    """
    def __init__(self,ocp,v_opt):
        self.dvMap = collmaps.VectorizedReadOnlyCollMap(ocp,'devectorized design vars',v_opt)
        self.outputMap = collmaps.OutputMap(ocp._outputMapGenerator, v_opt)
        self.quadratureMap = collmaps.QuadratureMap(ocp._quadratureManager, v_opt)

        self.nk = ocp.nk
        self.nicp = ocp.nicp
        self.deg = ocp.deg
        self.collPoly = ocp.collPoly

        # make time grid
        ocp.hfun.setInput(v_opt)
        ocp.hfun.evaluate()
        h = float(ocp.hfun.output())

        self.tgrid = np.resize([],(ocp.nk+1,ocp.nicp,ocp.deg+1))
        tf = 0.0
        for k in range(ocp.nk):
            for i in range(ocp.nicp):
                self.tgrid[k,i,:] = tf + h*np.array(ocp.lagrangePoly.tau_root)
                tf += h
        self.tgrid[ocp.nk,0,0] = tf

    def getDvs(self):
        return self.dvMap.vectorize()

    def lookup(self,name,timestep=None,nicpIdx=None,degIdx=None):
        try:
            return self.dvMap.lookup(name,timestep=timestep,nicpIdx=nicpIdx,degIdx=degIdx)
        except NameError:
            pass
        try: 
            return self.outputMap.lookup(name,timestep=timestep,nicpIdx=nicpIdx,degIdx=degIdx)
        except NameError:
            pass
        try: 
            return self.quadratureMap.lookup(name,timestep,nicpIdx,degIdx)
        except NameError:
            pass
        raise NameError("lookup fail, unrecognized name \""+name+"\"")

    def save(self,filename):
        assert isinstance(filename,str), "filename must be a string"

        print "saving trajectory as \"%s\"" % filename
        f=open(filename,'w')
        pickle.dump(self,f)
        f.close()

# thing which facilitates plotting
class TrajectoryPlotter(Trajectory):
    """
    A Trajectory that can plot itself
    """
    def subplot(self,names,title=None,style=None):
        assert isinstance(names,list)
        
        fig = plt.figure()
        if title is None:
            if isinstance(names,str):
                title = names
            else:
                assert isinstance(names,list)
                if len(names) == 1:
                    title = names[0]
                else:
                    title = str(names)
        fig.canvas.set_window_title(str(title))
                    
        plt.clf()
        n = len(names)
        if style is None:
            style = [None]*n
        for k,name in enumerate(names):
            plt.subplot(n,1,k+1)
            if k==0:
                self._plot(name,title,style=style[k])
            else:
                self._plot(name,None,style=style[k])

    def plot(self,names,title=None,style=None):
        fig = plt.figure()
        if title is None:
            if isinstance(names,str):
                title = names
            else:
                assert isinstance(names,list)
                if len(names) == 1:
                    title = names[0]
                else:
                    title = str(names)
        
        fig.canvas.set_window_title(str(title))
        plt.clf()
        self._plot(names,title,style=style)

    def _plot(self,names,title,style=None,showLegend=True):
        if isinstance(names,str):
            names = [names]
        assert isinstance(names,list)
        
        legend = []
        for name in names:
            assert isinstance(name,str)
            legend.append(name)

            # if it's a differential state
            if name in self.dvMap._xNames:
                ys = []
                ts = []
                for i in range(self.dvMap._nk):
                    for k in range(self.dvMap._nicp):
                        for j in range(self.dvMap._deg+1):
                            ys.append(self.dvMap.lookup(name,timestep=i,nicpIdx=k,degIdx=j))
                            ts.append(self.tgrid[i,k,j])
                        ys.append(np.nan*ys[-1])
                        ts.append(ts[-1])
                ys.append(self.dvMap.lookup(name,timestep=-1,nicpIdx=0,degIdx=0))
                ts.append(self.tgrid[-1,0,0])
                if style is None:
                    plt.plot(ts,ys)
                else:
                    plt.plot(ts,ys,style)
                
            # if it's an algebraic var
            elif name in self.dvMap._zNames:
                ys = []
                ts = []
                for i in range(self.dvMap._nk):
                    for k in range(self.dvMap._nicp):
                        for j in range(1,self.dvMap._deg+1):
                            ys.append(self.dvMap.lookup(name,timestep=i,nicpIdx=k,degIdx=j))
                            ts.append(self.tgrid[i,k,j])
                        ys.append(np.nan*ys[-1])
                        ts.append(ts[-1])
                if style is None:
                    plt.plot(ts,ys)
                else:
                    plt.plot(ts,ys,style)

            # if it's a control
            elif name in self.dvMap._uNames:
                ys = []
                ts = []
                for i in range(self.dvMap._nk):
                    y = self.dvMap.lookup(name,timestep=i)
                    t0 = self.tgrid[i,0,0]
                    t1 = self.tgrid[i+1,0,0]
                    ys.extend([y,y,np.nan*y])
                    ts.extend([t0,t1,t1])
                if style is None:
                    plt.plot(ts,ys)
                else:
                    plt.plot(ts,ys,style)

            # if it's an output defined everywhere
            elif name in self.outputMap._outputs0:
                ys = []
                ts = []
                for i in range(self.dvMap._nk):
                    for k in range(self.dvMap._nicp):
                        for j in range(self.dvMap._deg+1):
                            ys.append(self.outputMap.lookup(name,timestep=i,nicpIdx=k,degIdx=j))
                            ts.append(self.tgrid[i,k,j])
                        ys.append(np.nan*ys[-1])
                        ts.append(ts[-1])
                if style is None:
                    plt.plot(ts,ys)
                else:
                    plt.plot(ts,ys,style)

            # if it's an output defined only on collocation points
            elif name in self.outputMap._outputs:
                ys = []
                ts = []
                for i in range(self.dvMap._nk):
                    for k in range(self.dvMap._nicp):
                        for j in range(1,self.dvMap._deg+1):
                            ys.append(self.outputMap.lookup(name,timestep=i,nicpIdx=k,degIdx=j))
                            ts.append(self.tgrid[i,k,j])
                        ys.append(np.nan*ys[-1])
                        ts.append(ts[-1])
                if style is None:
                    plt.plot(ts,ys)
                else:
                    plt.plot(ts,ys,style)

            # if it's a quadrature state
            elif name in self.quadratureMap._quadMap:
                ys = []
                ts = []
                for i in range(self.quadratureMap._nk):
                    for k in range(self.quadratureMap._nicp):
                        for j in range(self.quadratureMap._deg+1):
                            ys.append(self.quadratureMap.lookup(name,timestep=i,nicpIdx=k,degIdx=j))
                            ts.append(self.tgrid[i,k,j])
                        ys.append(np.nan*ys[-1])
                        ts.append(ts[-1])
                if style is None:
                    plt.plot(ts,ys)
                else:
                    plt.plot(ts,ys,style)

            # throw error on parameter
            elif name in self.dvMap._pNames:
                raise ValueError("can't plot a parameter (\""+name+"\")")

            # throw error on unrecognized
            else:
                raise ValueError("unrecognized name \""+name+"\"")
        
        if title is not None:
            assert isinstance(title,str), "title must be a string"
            plt.title(title)
        plt.xlabel('time [s]')
        if showLegend is True:
            plt.legend(legend)
        plt.grid()
