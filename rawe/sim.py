import casadi as C

def getitemMsg(d,name,msg):
    try:
        return d[name]
    except KeyError:
        raise Exception('you forgot to put "'+name+'" in '+msg)

def maybeToScalar(x):
    if x.size() == 1:
        return x.at(0)
    else:
        return x

class Sim(object):
    def __init__(self, dae, ts):
#        x = C.DMatrix([x0[name] for name in self.xNames()])
    
#        print "creating outputs function"
#        (_,(fNoZ,outputNames)) = self.outputsFun()
#        fNoZ.init()
#    
#        print "creating communicator"
#        communicator = simutils.Communicator(fNoZ,outputNames)

        print "creating integrator"
        self.dae = dae
        self.integrator = C.IdasIntegrator(self.dae.casadiDae())
        self.integrator.setOption("reltol",1e-6)
        self.integrator.setOption("abstol",1e-8)
        self.integrator.setOption("t0",0)
        self.integrator.setOption("tf",ts)
        self.integrator.setOption('name','integrator')
        self.integrator.setOption("linear_solver",C.CSparse)
        self.integrator.init()
        
        print "creating outputs function"
        (fAll, (f0,outputs0names)) = self.dae.outputsFun()
        self.outputsFunAll = fAll
        self.outputsFun0 = f0
        self.outputs0names = outputs0names

    def step(self, x, u, p):
        xVec = C.veccat([getitemMsg(x,name,"the states") for name in self.dae.xNames()])
        uVec = C.veccat([getitemMsg(u,name,"the controls") for name in self.dae.uNames()])
        pVec = C.veccat([getitemMsg(p,name,"the parameters") for name in self.dae.pNames()])
        self.integrator.setInput(xVec,C.INTEGRATOR_X0)
        self.integrator.setInput(C.veccat([uVec,pVec]),C.INTEGRATOR_P)
        self.integrator.evaluate()
        xNext = C.DMatrix(self.integrator.output())
        ret = {}
        for k,name in enumerate(self.dae.xNames()):
            ret[name] = xNext[k].at(0)
        return ret

    def getOutputs(self, x, u, p):
        xVec = C.veccat([getitemMsg(x,name,"the states") for name in self.dae.xNames()])
        uVec = C.veccat([getitemMsg(u,name,"the controls") for name in self.dae.uNames()])
        pVec = C.veccat([getitemMsg(p,name,"the parameters") for name in self.dae.pNames()])
        self.outputsFun0.setInput(xVec, 0)
        self.outputsFun0.setInput(uVec, 1)
        self.outputsFun0.setInput(pVec, 2)
        self.outputsFun0.evaluate()
        ret = {}
        for k,name in enumerate(self.outputs0names):
            ret[name] = maybeToScalar(C.DMatrix(self.outputsFun0.output(k)))
        return ret
