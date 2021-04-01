import numpy as np
import torch
from scipy.integrate import odeint
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt

def perturbPoints(grid, v0, vf, sig=0.5):
    #stochastic perturbation of the evaluation points    
    #force t[0]=t0
    delta_v = grid[1] - grid[0]  
    noise = delta_v * torch.randn_like(grid)*sig
    v = grid + noise
    v.data[2] = torch.ones(1, 1)*(-1)
    v.data[v<v0]=v0 - v.data[v<v0]
    v.data[v>vf]=2*vf - v.data[v>vf]
    return v


def generate_dataloader( t_0, t_final, train_size, batch_size, perturb=True, shuffle=True):
    # Generate a dataloader with perturbed points starting from a grid_explorer
    grid = torch.linspace(t_0, t_final, train_size).reshape(-1, 1)
    
    if perturb:
        grid = perturbPoints(grid, t_0, t_final, sig=0.3 * t_final)
    grid.requires_grad = True

    t_dl = DataLoader(dataset=grid, batch_size=batch_size, shuffle=shuffle)
    return t_dl

def f(u, t, beta, gamma):
    s, i, r = u  # unpack current values of u
    N = s + i + r
    derivs = [-(beta * i * s) / N, (beta * i * s) / N - gamma * i, gamma * i]  # list of dy/dt=f functions
    return derivs


# Scipy Solver
def SIR_solution(t, s_0, i_0, r_0, beta, gamma):
    u_0 = [s_0, i_0, r_0]

    # Call the ODE solver
    sol_sir = odeint(f, u_0, t, args=(beta, gamma))
    s = sol_sir[:, 0]
    i = sol_sir[:, 1]
    r = sol_sir[:, 2]

    return s, i, r

    
def test_model(model, t_0, t_final, i0, r0, beta0=0.25, gamma0=0.1, n_test = 1000):  
   # test the model with a given set of parameters and intial conditions      
   t = torch.linspace(t_0, t_final, n_test).reshape(-1,1)
   t.requires_grad = True
   
   s0 = 1 - i0 - r0
   i_0 = i0*torch.ones(n_test)
   r_0 = r0*torch.ones(n_test)
   beta = beta0*torch.ones(n_test)
   gamma = gamma0*torch.ones(n_test)
   i_0 = i_0.reshape((-1, 1))
   r_0 = r_0.reshape((-1, 1))
   beta = beta.reshape((-1, 1))
   gamma = gamma.reshape((-1, 1))
   s_0 = 1 - (i_0 + r_0)
   
   initial_conditions = [s_0, i_0, r_0]
   params_bundle = [beta, gamma]

   s, i, r = model.parametric_solution(t, t_0, initial_conditions, params_bundle)

   t = t.detach().numpy()
   s = s.detach().numpy()
   i = i.detach().numpy()
   r = r.detach().numpy() 
   t = t.reshape((n_test,))   
     
   s_exact, i_exact, r_exact = SIR_solution(t, s0, i0, r0, beta0, gamma0)
                                                     
   lineW = 3
   plt.plot(t, s_exact,'--b', label=' S Ground Truth', linewidth=lineW);
   plt.plot(t, s ,'-b', label='S Network',linewidth=lineW, alpha=.5);
   plt.plot(t, r_exact,'--g', label=' R Ground Truth', linewidth=lineW);
   plt.plot(t, r ,'-g', label='R Network',linewidth=lineW, alpha=.5);
   plt.plot(t, i_exact,'--r', label=' I Ground Truth', linewidth=lineW);
   plt.plot(t, i ,'-r', label='I Network',linewidth=lineW, alpha=.5);
   plt.legend()
   
   plt.savefig('solutions_i0={},r0={},beta0={},gamma0={}.png'.format(i0, r0, beta0, gamma0))
   plt.tight_layout()
   plt.close()

    
    
    
    

