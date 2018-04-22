from cvxpy import *
import numpy as np
import scipy.io as sio
import time

start = time.time()


def app_inputs():
    mat = sio.loadmat('Testing_Data.mat')
    fxd = mat['fixed_customer_requests']
    flx = mat['flexible_customer_requests']
    flx_hrs = mat['flexible_customer_hours_requests']
    app = mat['Appliance_List_mat']
    app_once = mat['Appliance_List']
    prices_fix = mat['prices_fix']
    prices_flex = mat['prices_flex']
    solar = mat['Solar']
    return fxd, flx, flx_hrs, app, app_once, prices_fix, prices_flex, solar


def load_appliances():
    return np.genfromtxt('Appliance_List.xlsx')


def lp_solve(params):
    fixed, flex, hrs_flx, p_app, p_app_once, p_fix, p_flex, solar_profile = app_inputs()
    p_app_once = p_app_once/(60/params['sampling_time_min'])
    H = params['time_steps']
    solar_profile = solar_profile[:H]
    M = fixed.shape[1]  # appliances
    num_fix = fixed.shape[0]
    num_flex = flex.shape[0]
    eta = params['roundtrip_efficiency']

    # store the appliance index that each customer will use
    app_index = dict()
    for i, row in enumerate(flex):
        app_index[i] = np.nonzero(row)[0][0]

    # declare the variables

    D_flex = Variable(H)
    B_level = Variable(H)

    G_solar = Variable(H)
    X_fix = dict()
    X_flex = dict()
    for i in range(num_fix):
        X_fix[i] = Parameter(M, H)
    for i in range(num_flex):
        X_flex[i] = Bool(M, H)
    P_batt = Variable(H)
    D_curtailed = Variable(H)

    D_fix = Parameter(H)
    S_profile = Parameter(H)
    S_profile.value = solar_profile
    if params['case'] == 'size':
        S_capacity = Variable()
        B_capacity = Variable()
    elif params['case'] == 'schedule':
        S_capacity = Parameter()
        B_capacity = Parameter()
        S_capacity.value = params['solar_capacity']
        B_capacity.value = params['battery_capacity']


    # declare the parameters
    f = Parameter()
    f.value = params['max_state_of_charge_delta']
    U_fixed = fixed
    I_pv = Parameter()
    I_pv.value = params['pvcost_per_kw']
    # C_exp = Parameter()
    I_batt = Parameter()
    I_batt.value = params['battcost_per_kwh']

    L_once = Parameter(M)
    L_once.value = p_app_once

    # initialize earnings (9)
    C_exp_fix = 0
    C_exp_flex_store = []
    C_exp_flex = Variable()
    # cost of pv (7)
    C_batt = I_batt * B_capacity
    # cost of battery (8)
    C_pv = I_pv * S_capacity

    # formulate the problem
    constraints = []
    obj = Minimize(C_pv + C_batt - C_exp_fix - C_exp_flex)

    # build constraints iteratively
    # battery must be > 0
    constraints.append(B_level[:] >= params['soc_min'] * B_capacity * np.ones((H, 1)))
    constraints.append(B_level[:] <= B_capacity * np.ones((H, 1)))
    # start with 100% SOC
    constraints.append(B_level[0] == B_capacity)
    # supply = demand (3)
    constraints.append(P_batt[:] - D_fix[:] - D_flex[:] - D_curtailed[:] + G_solar[:] == np.zeros((H, 1)))
    # D_curtailed > 0
    constraints.append(D_curtailed[:] >= np.zeros((H, 1)))
    # charge/discharge limit (4)
    constraints.append(abs(P_batt[:]) <= B_capacity * f * np.ones((H, 1)))
    # solar generation (6)
    constraints.append(G_solar == S_profile * S_capacity)
    # battery level constraint (2)
    constraints.append(B_level[1:] == B_level[:-1] - eta * P_batt[1:])

    D_fix_store = np.zeros((H, 1))
    for h in range(1, H):
        D_flex_store = []
        for cust in range(num_fix):
            # profit from selling (9)
            C_exp_fix += np.sum(p_app_once.T * U_fixed[cust, :, h] * p_fix[cust, h])
            D_fix_store[h] = np.sum(np.dot(p_app_once.T, U_fixed[cust]))
            if cust < num_flex:
                # profit from selling (9)
                C_exp_flex_store.append(np.dot(L_once.T, X_flex[cust][:, h]) * p_flex[cust, h])
                # demand from flex customers (10) [variant]
                D_flex_store.append(sum_entries(np.dot(L_once.T, X_flex[cust][:, h])))
        constraints.append(D_flex[h] == sum(D_flex_store))
    for cust in range(num_flex):
        constraints.append(sum_entries(abs(diff(X_flex[cust][app_index[cust], :], axis=1)), axis=1) <= 2)
        constraints.append(X_flex[cust][app_index[cust], -1] == 0)
        constraints.append(X_flex[cust][app_index[cust], 0] == 0)
        constraints.append(sum_entries(X_flex[cust][app_index[cust], :], axis=1) == hrs_flx[cust])
    for cust in range(num_fix):
        # demand from fixed customers (10) [variant]
        X_fix[cust].value = U_fixed[cust]
    D_fix.value = D_fix_store
    constraints.append(C_exp_flex == sum(C_exp_flex_store))

    print()
    print(len(constraints), 'constraints formed:')
    print()
    prob = Problem(obj, constraints)

    prob.solve(solver=GUROBI, verbose=True, parallel=True)

    X_out = np.zeros((num_flex, H))
    for i in range(num_flex):
        X_out[i, :] = X_flex[i].value[app_index[i], :]

    print('optimal value:', prob.value)
    # name = 'production_center_optimal_val.csv'
    # np.savetxt(name, X_out, delimiter=',')
    # name = 'production_center_demand.csv'
    # np.savetxt(name, D_flex.value + D_fix.value)
    # name = 'production_center_curt.csv'
    # np.savetxt(name, D_curtailed.value)
    # name = 'production_center_battery.csv'
    # np.savetxt(name, B_level.value)
    # name = 'production_center_solar.csv'
    # np.savetxt(name, S_profile.value)
    # name = 'production_center_battery_power.csv'
    # np.savetxt(name, P_batt.value)


    print("Optimal var")
    print('C_exp_flex:', C_exp_flex.value)
    print('C_exp_fix:', C_exp_fix)
    print('Fixed_costs:', C_pv.value + C_batt.value)
    print('Solar_Capacity:', S_capacity.value)
    print('Battery Capacity:', B_capacity.value)

    # opt_params = []
    # opt_val = 1000
    # for scap in np.arange(3, 8, .6):
    #     for bcap in np.arange(4, 9, .5):
    #         try:
    #             S_capacity.value = scap
    #             B_capacity.value = bcap
    #             prob.solve(solver=GUROBI, verbose=True)
    #             if prob.status == OPTIMAL:
    #                 if prob.value < opt_val:
    #                     opt_params.append([scap, bcap])
    #         except Exception as e:
    #             print(e)
    # print('optimal sizing:', opt_params[-1])



def main():
    config = {'case': 'schedule',
              'solar_capacity': 6,
              'battery_capacity': 8.4,
              'horizon_hours': 4*24,
              'sampling_time_min': 15,
              'roundtrip_efficiency': 0.85,
              'max_state_of_charge_delta': .1,
              'pvcost_per_kw': 0.25,
              'battcost_per_kwh': 0.5,
              'soc_min': .2
              }

    config['time_steps'] = int(config['horizon_hours'] * (60/config['sampling_time_min']))

    lp_solve(config)


main()

print(time.time() - start)
