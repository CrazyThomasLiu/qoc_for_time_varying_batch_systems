import copy
import pdb
import control
from algorithm.model_based_ocs import MBOCS
from env.time_variant_batch_sys import Time_varying_batch_system
import numpy as np
import matplotlib.pyplot as plt
# save the figure or not

save_figure=False
save_csv=False
batch_length = 100
batch_num=50
# cost function
Q = np.matrix([[200.,0.],[0.,100.]])
R = np.matrix([[0.01,0.],[0.,0.01]])
# the time-varying weighting matrix
Q_t = []
R_t = []
for time in range(batch_length):
    Q_t.append(copy.deepcopy(Q))
    R_t.append(copy.deepcopy(R))

"1. the real state space"
'1.1 the time-invariant parameters'
A= np.matrix([[0., 1.0,-1.0], [-0.6, -1.1,0.6],[-0.4, -1.2,0.5]])
B= np.matrix([[1.,2.], [10.,6.], [5.,3.]])
C= np.matrix([[1.0,1.5,1.],[1.0,0.5,0.5]])
n=3 # state
m=2 # input
q=2 # output
'1.2 the time-varying parameters'
A_t = []
B_t = []
C_t=  []
for time in range(batch_length):
    A_t.append(copy.deepcopy(A))
    B_t.append(copy.deepcopy(B))
    C_t.append(copy.deepcopy(C))
C_t.append(copy.deepcopy(C))
"1.3 add the system uncertainty"
A_t_env = []
B_t_env = []
C_t_env=  []
for time in range(batch_length):
    A_t_env.append(copy.deepcopy(A))
    A_t_env[time]=A_t[time]+A_t[time]*0.1*np.sin(time)
    B_t_env.append(copy.deepcopy(B))
    B_t_env[time] =B_t[time]+B_t[time] *0.2* np.cos(time)
    C_t_env.append(copy.deepcopy(C))
    C_t_env[time] = C_t[time] + C_t[time] * 0.05 * np.sin(2*time)
'1.3 add a additional parameter for the t+1'
C_t_env.append(copy.deepcopy(C))
C_t_env[batch_length] = C_t[batch_length] + C_t[batch_length] * 0.05 * np.sin(2*batch_length)

'1.4 the reference trajectory'

y_ref = np.ones((batch_length+1, q))
y_ref[0:51,0]=10.* y_ref[0:51,0]
y_ref[0:51,1]=20.* y_ref[0:51,1]
y_ref[51:101,0]=20.* y_ref[51:101,0]
y_ref[51:101,1]=30.* y_ref[51:101,1]

'1.5 calculate the reference trajectory model D_{t},H_{t}'
y_sum = np.zeros((batch_length+1, 1))

for time in range(batch_length+1):
    for output_dim in range(q):
        y_sum[time,0]+=y_ref[time,output_dim]

D_t= []
for time in range(batch_length):
    D_t.append(np.zeros((1,1)))
    D_t[time][0, 0] = y_sum[time + 1, 0] / y_sum[time, 0]
H_t= []
for time in range(batch_length+1):
    H_t.append(np.zeros((q,1)))
    for output_dim in range(q):
        H_t[time][output_dim, 0] = y_ref[time, output_dim] / y_sum[time, 0]
"2. compute the model-based optimal control law"
'2.1 initial the model-based control scheme'
'model-based optimal control policy without the time-varying system uncertainties'
mb_ocs = MBOCS(batch_length=batch_length, A_t=A_t, B_t=B_t, C_t=C_t,D_t=D_t,H_t=H_t,Q_t=Q_t, R_t=R_t)
'model-based optimal control policy with the time-varying system uncertainties'
full_ocs = MBOCS(batch_length=batch_length, A_t=A_t_env, B_t=B_t_env, C_t=C_t_env,D_t=D_t,H_t=H_t,Q_t=Q_t, R_t=R_t)
mb_ocs.control_law()
full_ocs.control_law()
"2.2 save the model-based control policy and the optimal control policy"
mb_ocs.save_K(name='initial_control_law')
full_ocs.save_K(name='optimal_control_law')
#pdb.set_trace()
"3. set the simulated env"
'3.1 the initial state'
x_k0 = np.array([[5.], [5.] ,[5.]])
sample_time = 1

"3.2 set the batch system"
def state_update(t, x, u, params):
    # get the parameter from the params
    # pdb.set_trace()
    # Map the states into local variable names
    # the state x_{k,t}
    z1 = np.array([x[0]])
    z2 = np.array([x[1]])
    z3 = np.array([x[2]])
    # the control signal u_{k,t}
    u1 = np.array([u[0]])
    u2 = np.array([u[1]])
    # Get the current time t state space
    A_t_env=params.get('A_t')
    B_t_env = params.get('B_t')
    # Compute the discrete updates
    dz1 = A_t_env[0,0]* z1 + A_t_env[0,1]* z2+A_t_env[0,2]* z3 +B_t_env[0,0]*u1+B_t_env[0,1]*u2
    dz2 = A_t_env[1,0]* z1 + A_t_env[1,1]* z2+A_t_env[1,2]* z3 +B_t_env[1,0]*u1+B_t_env[1,1]*u2
    dz3 = A_t_env[2, 0] * z1 + A_t_env[2, 1] * z2 + A_t_env[2, 2] * z3 + B_t_env[2, 0] * u1 + B_t_env[2, 1] * u2
    # pdb.set_trace()
    return [dz1, dz2, dz3]


def output_update(t, x, u, params):
    # Parameter setup
    # pdb.set_trace()
    # Compute the discrete updates
    # the state x_{k,t}
    z1 = np.array([x[0]])
    z2 = np.array([x[1]])
    z3 = np.array([x[2]])
    # Get the current time t state space
    C_t_env=params.get('C_t')
    y1 = C_t_env[0,0]* z1 + C_t_env[0,1]* z2+C_t_env[0,2]* z3
    y2 = C_t_env[1, 0] * z1 + C_t_env[1, 1] * z2 + C_t_env[1, 2] * z3
    return [y1,y2]

batch_sys = control.NonlinearIOSystem(
    state_update, output_update, inputs=('u1','u2'), outputs=('y1','y2'),
    states=('dz1', 'dz2', 'dz3'), dt=1, name='linear_MIMO')

#controlled_system = TwoDimSys(batch_length=batch_length, sample_time=sample_time, sys=batch_sys, x_k0=x_k0, x_t0=x_t0)
#controlled_system = Time_varying_injection_molding(batch_length=batch_length, sample_time=sample_time, sys=batch_sys,x_k0=x_k0,A_t=A_t, B_t=B_t, C_t=C_t,D_t=D_t)
controlled_system = Time_varying_batch_system(batch_length=batch_length, sample_time=sample_time, sys=batch_sys,x_k0=x_k0,A_t=A_t_env, B_t=B_t_env, C_t=C_t_env)




#pdb.set_trace()

"4. simulations"

"4.1 reset the system"
x_tem,y_out=controlled_system.reset()

"4.2 simulations"
fig_y=np.zeros((q,batch_length+1))
fig_u=np.zeros((m,batch_length))
fig_y[:,0:1]=y_out[:,0]   # the matrix and array
for time in range(batch_length):
    state = np.block([[x_tem],
                      [y_sum[time + 1]]])
    control_signal = -mb_ocs.K[time]@state
    x_tem,y_out= controlled_system.step(control_signal)
    fig_y[:,time+1] = y_out[:, 0]
    fig_u[:, time:time+1] = control_signal[:, 0]


"5. plot the figures"
"set the global parameters"
config = {
    "font.family": 'sans-serif',
    "font.serif": ['Arial'],
    "font.size": 12,
    "mathtext.fontset": 'stix',
}
plt.rcParams.update(config)

fig, ((ax0, ax1),(ax2,ax3)) = plt.subplots(2, 2, sharex=True, constrained_layout=True)
"5.1 plot the output response"
"output 1"
time=range(0,batch_length+1)
ax0.plot(time, y_ref[0:,0], label='smoothed')
ax0.plot(time, fig_y[0],linestyle='dotted')


ax0.grid()
xlable = 'Time:$t$'
ylable = 'Output:$y^{1}$'
font = {'family': 'Arial',
         'weight': 'bold',
         'size': 16,
         }
ax0.set_ylabel('Output:$y^{1}$',font)
#plt.xlabel(xlable,font)
#plt.ylabel(ylable,font)
#plt.legend(['Reference Trajectory','Output Response'],loc='upper right')
#plt.legend(['Reference Trajectory','Output Response'])
ax0.legend(['Reference Trajectory','Q-learning-based Optimal Controller'])
#plt.show()
#pdb.set_trace()

"output 2"
ax1.plot(time, y_ref[0:,1], label='smoothed')
ax1.plot(time, fig_y[1],linestyle='dotted')


ax1.grid()
xlable = 'Time:$t$'
ylable = 'Output:$y^{2}$'
ax1.set_ylabel('Output:$y^{2}$',font)
#plt.xlabel(xlable,font)
#plt.ylabel(ylable,font)
#plt.legend(['Reference Trajectory','Output Response'],loc='upper right')
#plt.legend(['Reference Trajectory','Output Response'])
ax1.legend(['Reference Trajectory','Q-learning-based Optimal Controller'])
"5.2 plot the control signal"
"control signal 1"
#pdb.set_trace()

time=range(1,batch_length+1)
ax2.plot(time, fig_u[0], label='smoothed')

ax2.grid()
xlable = 'Time:$t$'
ylable = 'Control Signal:$u^{1}$'
ax2.set_ylabel('Control Signal:$u^{1}$',font)
ax2.set_xlabel('Time:$t$',font)
#plt.legend(['Reference Trajectory','Output Response'],loc='upper right')
#plt.legend(['Reference Trajectory','Output Response'])
"control signal 2"
time=range(1,batch_length+1)
ax3.plot(time, fig_u[1], label='smoothed')

ax3.grid()
xlable = 'Time:$t$'
ylable = 'Control Signal:$u^{2}$'
ax3.set_ylabel('Control Signal:$u^{2}$',font)
ax3.set_xlabel('Time:$t$',font)
#plt.xlabel(xlable,font)
#plt.ylabel(ylable,font)
#plt.legend(['Reference Trajectory','Output Response'],loc='upper right')
#plt.legend(['Reference Trajectory','Output Response'])

if save_figure==True:
    #plt.savefig('Injection_molding_output.pdf')
    #plt.savefig('mb_ocs.jpg',dpi=700)
    plt.savefig('MIMO.pdf')
plt.show()

pdb.set_trace()
a=2