conf = {#[env]
     'g': 9.81,  #  gravitational constant #  [ m /s^2]
     'rho': 1.23,  #  density of the air #  [ kg/m^3]

     #[aero]
     'alpha0deg': 0,

     #ROLL DAMPING
     'rD': 0.3e-2 ,
     'pD': 0,#1e-3,
     'yD': 0,#1e-3,

     #WIND-TUNNEL PARAMETERS
     #Lift (report p. 67)
     'cLA': 5.064,
     'cLe': -1.924,
     'cL0': 0.239,

     #Drag (report p. 70)
     'cDA': -0.195,
     'cDA2': 4.268,
     'cDB2': 0,

     'cD0': 0.026,

     #Roll (report p. 72)
     'cRB': -0.062,
     'cRAB': -0.271 ,
     'cRr': -5.637e-1,

     #Pitch (report p. 74)
     'cPA': 0.293,
     'cPe': -4.9766e-1,

     'cP0': 0.03,

     #Yaw (report p. 76)
     'cYB': 0.05,
     'cYAB': 0.229,

     #[kite]
     #'mass':  0.626  #  mass of the kite   #  [ kg],
     'mass':  7.0,

     #TAIL LENGTH
     'lT': 0.4,

     # how alpha/beta computed
     'alpha_beta_computation':'closed_form',

     'sref': 0.66,
     'bref': 2.5171, #sqrt(sref*AR),
     'cref': 0.2622, #sqrt(sref/AR),

     'zt': -0.01,

     #INERTIA MATRIX (Kurt's direct measurements)
     'j1': 0.0163,
    'j31': 0.0006,
    'j2': 0.0078,
    'j3': 0.0229,
    
    #[carousel]
    #'rArm': 1.085 #(dixit Kurt),
    'rArm': 2,
    
    #Carousel Friction & inertia
    'jCarousel': 1e2,
    'cfric': 0,#100,
    
    #[wind shear]
    'z0': 100,
    'zt_roughness': 0.1
    }
