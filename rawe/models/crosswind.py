import casadi as C
from rawe.dae import Dae
from aero import aeroForcesTorques

def setupModel(dae, conf):
    #  PARAMETERS OF THE KITE :
    #  ##############
    m =  conf['mass'] #  mass of the kite               #  [ kg    ]
                 
    #   PHYSICAL CONSTANTS :
    #  ##############
    g = conf['g'] #  gravitational constant         #  [ m /s^2]
    
    #  PARAMETERS OF THE CABLE :
    #  ##############
     
    #INERTIA MATRIX (Kurt's direct measurements)
    j1 =  conf['j1']
    j31 = conf['j31']
    j2 =  conf['j2']
    j3 =  conf['j3']
    
    #Carousel Friction & inertia
    zt = conf['zt']

    ###########     model integ ###################
    e11 = dae['e11']
    e12 = dae['e12']
    e13 = dae['e13']

    e21 = dae['e21']
    e22 = dae['e22']
    e23 = dae['e23']

    e31 = dae['e31']
    e32 = dae['e32']
    e33 = dae['e33']

    x =   dae['x']
    y =   dae['y']
    z =   dae['z']

    dx  =  dae['dx']
    dy  =  dae['dy']
    dz  =  dae['dz']

    w1  =  dae['w1']
    w2  =  dae['w2']
    w3  =  dae['w3']

    delta = 0
    ddelta = 0
    rA = 0

    r = dae['r']
    dr = dae['dr']
    ddr = dae['ddr']
    
    # wind
    z0 = conf['z0']
    zt_roughness = conf['zt_roughness']
    zsat = 0.5*(z+C.sqrt(z*z))
    wind_x = dae['w0']*C.log((zsat+zt_roughness+2)/zt_roughness)/C.log(z0/zt_roughness)
#    wind_x = dae['w0']
    dae['wind at altitude'] = wind_x

    dp_carousel_frame = C.veccat( [ dx - ddelta*y
                                  , dy + ddelta*(rA + x)
                                  , dz
                                  ]) - C.veccat([C.cos(delta)*wind_x,C.sin(delta)*wind_x,0])
    R_c2b = C.veccat( [dae[n] for n in ['e11', 'e12', 'e13',
                                        'e21', 'e22', 'e23',
                                        'e31', 'e32', 'e33']]
                      ).reshape((3,3))

    # Aircraft velocity w.r.t. inertial frame, given in its own reference frame
    # (needed to compute the aero forces and torques !)
    dpE = C.mul( R_c2b, dp_carousel_frame )

    (f1, f2, f3, t1, t2, t3) = aeroForcesTorques(dae, conf, dp_carousel_frame, dpE,
                                                 (dae['w1'], dae['w2'], dae['w3']),
                                                 (dae['e21'], dae['e22'], dae['e23']),
                                                 (dae['aileron'],dae['elevator'])
                                                 )
    if 'runHomotopy' in conf and conf['runHomotopy']:
        gamma_homotopy = dae.addP('gamma_homotopy')
        f1 = f1 * gamma_homotopy + dae.addZ('f1_homotopy')          * (1 - gamma_homotopy)
        f2 = f2 * gamma_homotopy + dae.addZ('f2_homotopy')          * (1 - gamma_homotopy)
        f3 = f3 * gamma_homotopy + (dae.addZ('f3_homotopy') - g*m)  * (1 - gamma_homotopy)
        t1 = t1 * gamma_homotopy + dae.addZ('t1_homotopy')          * (1 - gamma_homotopy)
        t2 = t2 * gamma_homotopy + dae.addZ('t2_homotopy')          * (1 - gamma_homotopy)
        t3 = t3 * gamma_homotopy + dae.addZ('t3_homotopy')          * (1 - gamma_homotopy)

    # mass matrix
    mm = C.SXMatrix(7, 7)
    mm[0,0] = m 
    mm[0,1] = 0 
    mm[0,2] = 0 
    mm[0,3] = 0 
    mm[0,4] = 0 
    mm[0,5] = 0 
    mm[0,6] = x + zt*e31

    mm[1,0] = 0 
    mm[1,1] = m 
    mm[1,2] = 0 
    mm[1,3] = 0 
    mm[1,4] = 0 
    mm[1,5] = 0 
    mm[1,6] = y + zt*e32
    
    mm[2,0] = 0 
    mm[2,1] = 0 
    mm[2,2] = m 
    mm[2,3] = 0 
    mm[2,4] = 0 
    mm[2,5] = 0 
    mm[2,6] = z + zt*e33
    
    mm[3,0] = 0 
    mm[3,1] = 0 
    mm[3,2] = 0 
    mm[3,3] = j1 
    mm[3,4] = 0 
    mm[3,5] = j31 
    mm[3,6] = -zt*(e21*x + e22*y + e23*z + zt*e21*e31 + zt*e22*e32 + zt*e23*e33)
    
    mm[4,0] = 0 
    mm[4,1] = 0 
    mm[4,2] = 0 
    mm[4,3] = 0 
    mm[4,4] = j2 
    mm[4,5] = 0 
    mm[4,6] = zt*(e11*x + e12*y + e13*z + zt*e11*e31 + zt*e12*e32 + zt*e13*e33)
    
    mm[5,0] = 0 
    mm[5,1] = 0 
    mm[5,2] = 0 
    mm[5,3] = j31 
    mm[5,4] = 0 
    mm[5,5] = j3 
    mm[5,6] = 0
    
    mm[6,0] = x + zt*e31 
    mm[6,1] = y + zt*e32 
    mm[6,2] = z + zt*e33 
    mm[6,3] = -zt*(e21*x + e22*y + e23*z + zt*e21*e31 + zt*e22*e32 + zt*e23*e33) 
    mm[6,4] = zt*(e11*x + e12*y + e13*z + zt*e11*e31 + zt*e12*e32 + zt*e13*e33) 
    mm[6,5] = 0 
    mm[6,6] = 0

    # right hand side
    zt2 = zt*zt
    rhs = C.veccat(
          [ f1 + ddelta*m*(dy + ddelta*rA + ddelta*x) + ddelta*dy*m 
          , f2 - ddelta*m*(dx - ddelta*y) - ddelta*dx*m 
          , f3 - g*m 
          , t1 - w2*(j3*w3 + j31*w1) + j2*w2*w3 
          , t2 + w1*(j3*w3 + j31*w1) - w3*(j1*w1 + j31*w3) 
          , t3 + w2*(j1*w1 + j31*w3) - j2*w1*w2
          , ddr*r-(zt*w1*(e11*x+e12*y+e13*z+zt*e11*e31+zt*e12*e32+zt*e13*e33)+zt*w2*(e21*x+e22*y+e23*z+zt*e21*e31+zt*e22*e32+zt*e23*e33))*(w3-ddelta*e33)-dx*(dx-zt*e21*(w1-ddelta*e13)+zt*e11*(w2-ddelta*e23))-dy*(dy-zt*e22*(w1-ddelta*e13)+zt*e12*(w2-ddelta*e23))-dz*(dz-zt*e23*(w1-ddelta*e13)+zt*e13*(w2-ddelta*e23))+dr*dr+(w1-ddelta*e13)*(e21*(zt*dx-zt2*e21*(w1-ddelta*e13)+zt2*e11*(w2-ddelta*e23))+e22*(zt*dy-zt2*e22*(w1-ddelta*e13)+zt2*e12*(w2-ddelta*e23))+zt*e23*(dz+zt*e13*w2-zt*e23*w1)+zt*e33*(w1*z+zt*e33*w1+ddelta*e11*x+ddelta*e12*y+zt*ddelta*e11*e31+zt*ddelta*e12*e32)+zt*e31*(x+zt*e31)*(w1-ddelta*e13)+zt*e32*(y+zt*e32)*(w1-ddelta*e13))-(w2-ddelta*e23)*(e11*(zt*dx-zt2*e21*(w1-ddelta*e13)+zt2*e11*(w2-ddelta*e23))+e12*(zt*dy-zt2*e22*(w1-ddelta*e13)+zt2*e12*(w2-ddelta*e23))+zt*e13*(dz+zt*e13*w2-zt*e23*w1)-zt*e33*(w2*z+zt*e33*w2+ddelta*e21*x+ddelta*e22*y+zt*ddelta*e21*e31+zt*ddelta*e22*e32)-zt*e31*(x+zt*e31)*(w2-ddelta*e23)-zt*e32*(y+zt*e32)*(w2-ddelta*e23))
          ] )
 
    dRexp = C.SXMatrix(3,3)

    dRexp[0,0] = e21*(w3 - ddelta*e33) - e31*(w2 - ddelta*e23) 
    dRexp[0,1] = e31*(w1 - ddelta*e13) - e11*(w3 - ddelta*e33) 
    dRexp[0,2] = e11*(w2 - ddelta*e23) - e21*(w1 - ddelta*e13) 

    dRexp[1,0] = e22*(w3 - ddelta*e33) - e32*(w2 - ddelta*e23) 
    dRexp[1,1] = e32*(w1 - ddelta*e13) - e12*(w3 - ddelta*e33) 
    dRexp[1,2] = e12*(w2 - ddelta*e23) - e22*(w1 - ddelta*e13) 

    dRexp[2,0] = e23*w3 - e33*w2 
    dRexp[2,1] = e33*w1 - e13*w3 
    dRexp[2,2] = e13*w2 - e23*w1
    
    c =(x + zt*e31)**2/2 + (y + zt*e32)**2/2 + (z + zt*e33)**2/2 - r**2/2
    
    cdot =dx*(x + zt*e31) + dy*(y + zt*e32) + dz*(z + zt*e33) + zt*(w2 - ddelta*e23)*(e11*x + e12*y + e13*z + zt*e11*e31 + zt*e12*e32 + zt*e13*e33) - zt*(w1 - ddelta*e13)*(e21*x + e22*y + e23*z + zt*e21*e31 + zt*e22*e32 + zt*e23*e33) - r*dr

    ddx = dae.ddt('dx')
    ddy = dae.ddt('dy')
    ddz = dae.ddt('dz')
    dw1 = dae.ddt('w1')
    dw2 = dae.ddt('w2')
#    ddx = dae['ddx']
#    ddy = dae['ddy']
#    ddz = dae['ddz']
#    dw1 = dae['dw1']
#    dw2 = dae['dw2']
    dddelta = 0
    
    cddot = -(w1-ddelta*e13)*(zt*e23*(dz+zt*e13*w2-zt*e23*w1)+zt*e33*(w1*z+zt*e33*w1+ddelta*e11*x+ddelta*e12*y+zt*ddelta*e11*e31+zt*ddelta*e12*e32)+zt*e21*(dx+zt*e11*w2-zt*e21*w1-zt*ddelta*e11*e23+zt*ddelta*e13*e21)+zt*e22*(dy+zt*e12*w2-zt*e22*w1-zt*ddelta*e12*e23+zt*ddelta*e13*e22)+zt*e31*(x+zt*e31)*(w1-ddelta*e13)+zt*e32*(y+zt*e32)*(w1-ddelta*e13))+(w2-ddelta*e23)*(zt*e13*(dz+zt*e13*w2-zt*e23*w1)-zt*e33*(w2*z+zt*e33*w2+ddelta*e21*x+ddelta*e22*y+zt*ddelta*e21*e31+zt*ddelta*e22*e32)+zt*e11*(dx+zt*e11*w2-zt*e21*w1-zt*ddelta*e11*e23+zt*ddelta*e13*e21)+zt*e12*(dy+zt*e12*w2-zt*e22*w1-zt*ddelta*e12*e23+zt*ddelta*e13*e22)-zt*e31*(x+zt*e31)*(w2-ddelta*e23)-zt*e32*(y+zt*e32)*(w2-ddelta*e23))-ddr*r+(zt*w1*(e11*x+e12*y+e13*z+zt*e11*e31+zt*e12*e32+zt*e13*e33)+zt*w2*(e21*x+e22*y+e23*z+zt*e21*e31+zt*e22*e32+zt*e23*e33))*(w3-ddelta*e33)+dx*(dx+zt*e11*w2-zt*e21*w1-zt*ddelta*e11*e23+zt*ddelta*e13*e21)+dy*(dy+zt*e12*w2-zt*e22*w1-zt*ddelta*e12*e23+zt*ddelta*e13*e22)+dz*(dz+zt*e13*w2-zt*e23*w1)+ddx*(x+zt*e31)+ddy*(y+zt*e32)+ddz*(z+zt*e33)-dr*dr+zt*(dw2-dddelta*e23)*(e11*x+e12*y+e13*z+zt*e11*e31+zt*e12*e32+zt*e13*e33)-zt*(dw1-dddelta*e13)*(e21*x+e22*y+e23*z+zt*e21*e31+zt*e22*e32+zt*e23*e33)-zt*dddelta*(e11*e23*x-e13*e21*x+e12*e23*y-e13*e22*y+zt*e11*e23*e31-zt*e13*e21*e31+zt*e12*e23*e32-zt*e13*e22*e32)

#    cddot = (zt*w1*(e11*x + e12*y + e13*z + zt*e11*e31 + zt*e12*e32 + zt*e13*e33) + zt*w2*(e21*x + e22*y + e23*z + zt*e21*e31 + zt*e22*e32 + zt*e23*e33))*(w3 - ddelta*e33) + dx*(dx + zt*e11*w2 - zt*e21*w1 - zt*ddelta*e11*e23 + zt*ddelta*e13*e21) + dy*(dy + zt*e12*w2 - zt*e22*w1 - zt*ddelta*e12*e23 + zt*ddelta*e13*e22) + dz*(dz + zt*e13*w2 - zt*e23*w1) + ddx*(x + zt*e31) + ddy*(y + zt*e32) + ddz*(z + zt*e33) - (w1 - ddelta*e13)*(e21*(zt*dx - zt**2*e21*(w1 - ddelta*e13) + zt**2*e11*(w2 - ddelta*e23)) + e22*(zt*dy - zt**2*e22*(w1 - ddelta*e13) + zt**2*e12*(w2 - ddelta*e23)) + zt*e33*(z*w1 + ddelta*e11*x + ddelta*e12*y + zt*e33*w1 + zt*ddelta*e11*e31 + zt*ddelta*e12*e32) + zt*e23*(dz + zt*e13*w2 - zt*e23*w1) + zt*e31*(w1 - ddelta*e13)*(x + zt*e31) + zt*e32*(w1 - ddelta*e13)*(y + zt*e32)) + (w2 - ddelta*e23)*(e11*(zt*dx - zt**2*e21*(w1 - ddelta*e13) + zt**2*e11*(w2 - ddelta*e23)) + e12*(zt*dy - zt**2*e22*(w1 - ddelta*e13) + zt**2*e12*(w2 - ddelta*e23)) - zt*e33*(z*w2 + ddelta*e21*x + ddelta*e22*y + zt*e33*w2 + zt*ddelta*e21*e31 + zt*ddelta*e22*e32) + zt*e13*(dz + zt*e13*w2 - zt*e23*w1) - zt*e31*(w2 - ddelta*e23)*(x + zt*e31) - zt*e32*(w2 - ddelta*e23)*(y + zt*e32)) + zt*(dw2 - dddelta*e23)*(e11*x + e12*y + e13*z + zt*e11*e31 + zt*e12*e32 + zt*e13*e33) - zt*(dw1 - dddelta*e13)*(e21*x + e22*y + e23*z + zt*e21*e31 + zt*e22*e32 + zt*e23*e33) - zt*dddelta*(e11*e23*x - e13*e21*x + e12*e23*y - e13*e22*y + zt*e11*e23*e31 - zt*e13*e21*e31 + zt*e12*e23*e32 - zt*e13*e22*e32)
#      where
#        dw1 = dw @> 0
#        dw2 = dw @> 1
#        {-
#        dw3 = dw @> 2
#        -}
#        ddx = ddX @> 0
#        ddy = ddX @> 1
#        ddz = ddX @> 2
#        dddelta = dddelta' @> 0

    dae['c'] =  c
    dae['cdot'] = cdot
    dae['cddot'] = cddot
    return (mm, rhs, dRexp)
        
def crosswindModel(conf,extraParams=[]):
    dae = Dae()
    for ep in extraParams:
        dae.addP(ep)
        
#    dae.addZ( [ "ddx"
#              , "ddy"
#              , "ddz"
#              , "dw1"
#              , "dw2"
#              , "dw3"
#              , "nu"
#              ] )
    dae.addZ("nu")
    dae.addX( [ "x"   # state 0
              , "y"   # state 1
              , "z"   # state 2
              , "e11" # state 3
              , "e12" # state 4
              , "e13" # state 5
              , "e21" # state 6
              , "e22" # state 7
              , "e23" # state 8
              , "e31" # state 9
              , "e32" # state 10
              , "e33" # state 11
              , "dx"  # state 12
              , "dy"  # state 13
              , "dz"  # state 14
              , "w1"  # state 15
              , "w2"  # state 16
              , "w3"  # state 17
              , "r" # state 20
              , "dr" # state 21
              , "aileron"
              , "elevator"
              ] )
    dae.addU( [ "daileron"
              , "delevator"
              , 'ddr'
              ] )
    dae.addP( ['w0'] )
    
    dae['ddx'] = dae.ddt('dx')
    dae['ddy'] = dae.ddt('dy')
    dae['ddz'] = dae.ddt('dz')
    dae['dw1'] = dae.ddt('w1')
    dae['dw2'] = dae.ddt('w2')
    dae['dw3'] = dae.ddt('w3')
    
    dae['aileron(deg)'] = dae['aileron']*180/C.pi
    dae['elevator(deg)'] = dae['elevator']*180/C.pi
    dae['daileron(deg/s)'] = dae['daileron']*180/C.pi
    dae['delevator(deg/s)'] = dae['delevator']*180/C.pi

    dae['tether tension'] = dae['r']*dae['nu']
    dae['winch power'] = -dae['tether tension']*dae['dr']

    dae['dcm'] = C.vertcat([C.horzcat([dae['e11'],dae['e12'],dae['e13']]),
                            C.horzcat([dae['e21'],dae['e22'],dae['e23']]),
                            C.horzcat([dae['e31'],dae['e32'],dae['e33']])])
    
    (massMatrix, rhs, dRexp) = setupModel(dae, conf)

    
    ode = C.veccat([
        C.veccat([dae.ddt(name) for name in ['x','y','z']]) - C.veccat([dae['dx'],dae['dy'],dae['dz']]),
        C.veccat([dae.ddt(name) for name in ["e11","e12","e13",
                                             "e21","e22","e23",
                                             "e31","e32","e33"]]) - dRexp.trans().reshape([9,1]),
#        C.veccat([dae.ddt(name) for name in ['dx','dy','dz']]) - C.veccat([dae['ddx'],dae['ddy'],dae['ddz']]),
#        C.veccat([dae.ddt(name) for name in ['w1','w2','w3']]) - C.veccat([dae['dw1'],dae['dw2'],dae['dw3']]),
        dae.ddt('r') - dae['dr'],
        dae.ddt('dr') - dae['ddr'],
        dae.ddt('aileron') - dae['daileron'],
        dae.ddt('elevator') - dae['delevator']
        ])

    # acceleration
#    ddx = dae['ddx']
#    ddy = dae['ddy']
#    ddz = dae['ddz']
    ddx = dae.ddt('dx')
    ddy = dae.ddt('dy')
    ddz = dae.ddt('dz')
    dae['accel (g)'] = C.sqrt(ddx**2 + ddy**2 + (ddz + 9.8)**2)/9.8
    dae['accel without gravity (g)'] = C.sqrt(ddx**2 + ddy**2 + ddz**2)/9.8
    dae['accel'] = C.sqrt(ddx**2 + ddy**2 + (ddz+9.8)**2)
    dae['accel without gravity'] = C.sqrt(ddx**2 + ddy**2 + ddz**2)

    # line angle
    dae['cos(line angle)'] = \
      (dae['e31']*dae['x'] + dae['e32']*dae['y'] + dae['e33']*dae['z']) / C.sqrt(dae['x']**2 + dae['y']**2 + dae['z']**2)
    dae['line angle (deg)'] = C.arccos(dae['cos(line angle)'])*180.0/C.pi

    # add local loyd's limit
    def addLoydsLimit():
        w = dae['wind at altitude']
        cL = dae['cL']
        cD = dae['cD']
        rho = conf['rho']
        S = conf['sref']
        loyds = 2/27.0*rho*S*w**3*cL**3/cD**2
        loyds2 = 2/27.0*rho*S*w**3*(cL**2/cD**2 + 1)**(1.5)*cD
        dae["loyd's limit"] = loyds
        dae["loyd's limit (exact)"] = loyds2
        dae['-(winch power)'] = -dae['winch power']
    addLoydsLimit()
    
    psuedoZVec = C.veccat([dae.ddt(name) for name in ['dx','dy','dz','w1','w2','w3']]+[dae['nu']])
    alg = C.mul(massMatrix, psuedoZVec) - rhs
    dae.setResidual( [ode, alg] )
    
    return dae
