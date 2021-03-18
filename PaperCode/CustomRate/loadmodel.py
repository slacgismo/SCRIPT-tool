import pandas as pd
import numpy as np
import cvxpy as cvx
import boto3
s3 = boto3.resource('s3')


class LoadModel(object):
    """This class implements the charging control for a parking lot of EVs. It takes in input data on the start and end
    times for each session, and uses the uncontrolled load profile for each session to calculate the energy that must
    be delivered. There are numerous options for which control should be implemented, described in methods below such as
    `e19_controlled_load()'.
    """

    def __init__(self, num_sessions=1, charge_rate=6.6):
        """This method initializes many of the input and output variables used."""

        self.uncontrolled_total_load = np.zeros((1, ))  # The aggregate uncontrolled load profile
        self.controlled_total_load = np.zeros((1, ))
        self.num_sessions = num_sessions  # The number of sessions / number of cars in the parking lot that day
        self.power = np.zeros((96, num_sessions))  # The uncontrolled load profile for each session
        self.arrival_inds = np.zeros(
            (num_sessions,))  # The arrival time of each session, expressed as an index between 0 and 95
        self.departure_inds = np.zeros((num_sessions,))  # The index of the departure time for each vehicle
        self.energies = np.zeros((num_sessions,))  # The energy delivered in each uncontrolled session
        self.charge_rate = charge_rate  # The charge rate allowed. The default is level 2, 6.6 kW
        
    def input_data(self, uncontrolled_load, start_inds, end_inds):
        """Here the data about the uncontrolled load is provided and the data is preprocessed."""
        
        self.power = np.transpose(uncontrolled_load)  # Transpose due to shape in CountyData class
        self.uncontrolled_total_load = np.sum(uncontrolled_load, axis=0)  # Aggregate all the cars/sessions
        self.arrival_inds = start_inds
        self.departure_inds = end_inds
        for i in range(self.num_sessions):
            if self.departure_inds[i] >= 96:  # If the session ends the next day, find the corresponding time in 0 to 96
                # E.g. if arrival is 80 and departure is 100 (the powerflex data has this), the new departure ind is 4.
                # If arrival is 2 and departure is 100, we want to avoid making the interval from 2 - 4 (only 30min when
                # it really is 1 day), so we set the departure time for the sake of the control as arrival time - 1.
                multiple, self.departure_inds[i] = np.divmod(self.departure_inds[i], 96)
                if self.departure_inds[i] >= self.arrival_inds[i]:  # Do not make the session time shorter than it is
                    if self.arrival_inds[i] > 0:
                        self.departure_inds[i] = self.arrival_inds[i] - 1
                    else:
                        self.departure_inds[i] = 95
            if self.departure_inds[i] == self.arrival_inds[i]:  # Each session should be at least one time step
                self.departure_inds[i] = self.arrival_inds[i] + 1

            # Calculate the session length as an input to the energy calculation
            if self.departure_inds[i] > self.arrival_inds[i]:
                session_length = self.departure_inds[i] - self.arrival_inds[i]
            else:
                session_length = 96 - self.arrival_inds[i] + self.departure_inds[i]
            # Energy calculated per session in kWh, 0.25 since each time step is 15min or 0.25 hours.
            self.energies[i] = np.minimum(0.25*np.sum(uncontrolled_load, axis=1)[i], 0.25*self.charge_rate*(session_length))

    def sdge_controlled_load(self, method='median', summer=True, percentile=50, verbose=False):
        """Implements charging control with the SDG&E TOU rate schedule given in the sdge_values method below. See that
         method for an explanation of the rate schedule.
        """

        energy_prices = sdge_values(method=method, summer=summer, percentile=percentile)

        # schedule is the cvxpy variable for the `power', the rate for each vehicle at each time step in kW.
        schedule = cvx.Variable((96, self.num_sessions))
        # The objective is calculated using the energy price: sum_times (price * kW * 0.25)
        obj = cvx.matmul(cvx.sum(schedule, axis=1), energy_prices.reshape((np.shape(energy_prices)[0], 1)))

        constraints = [schedule >= 0]  # No V2G or discharging while plugged in
        for i in range(self.num_sessions):
            # No charging above the max rate:
            constraints += [schedule[:, i] <= np.maximum(np.max(self.power[:, i]), self.charge_rate)]
            if self.departure_inds[i] >= self.arrival_inds[i]:
                if self.arrival_inds[i] > 0:
                    # No charging before arrival
                    constraints += [schedule[np.arange(0, int(self.arrival_inds[i])), i] <= 0]
                if self.departure_inds[i] < 96:
                    # No charging after departure
                    constraints += [schedule[np.arange(int(self.departure_inds[i]), 96), i] <= 0]
            else:
                # In the case where the charging session runs over midnight, this is the form of the "no charging before
                # arrival or after departure" constraint:
                constraints += [schedule[np.arange(int(self.departure_inds[i]), int(self.arrival_inds[i])), i] <= 0]

        # Must deliver the right amount of energy to each vehicle (the same as was delivered in the uncontrolled case)
        constraints += [0.25 * cvx.sum(schedule, axis=0) == self.energies]

        # CVXPY setup for solving the problem.
        prob = cvx.Problem(cvx.Minimize(obj), constraints)
        result = prob.solve(solver=cvx.MOSEK)
        if verbose:
            print('The objective result is', result)

        # Save the controlled output. sdge_controlled_power has the rate for each vehicle at each time step.
        self.sdge_controlled_power = schedule.value
        self.controlled_total_load = np.sum(schedule.value, axis=1)

    def pge_cev_controlled_load(self, subscription_level=None, verbose=False):
        """Implements the charging control for the PG&E Commercial EV rate schedule. The subscription rate is
        implemented as a cap. Please refer to the first control method, `sdge_controlled_load', for comments on the
        optimization set up and constraints which are common between the two.
        """

        if subscription_level is None:
            # The subscription level should be given because this is a very weak backup constraint:
            subscription_level = np.max(self.uncontrolled_total_load)

        peak_inds, partpeak_inds, offpeak_inds, energy_prices, subscription_rate_per50kw = pge_cev_values()

        schedule = cvx.Variable((96, self.num_sessions))
        obj = cvx.matmul(cvx.sum(schedule, axis=1), energy_prices.reshape((np.shape(energy_prices)[0], 1)))
        # This does not affect the optimization as it is constant for a given subscription level, but here it is:
        obj += subscription_rate_per50kw * subscription_level/50

        constraints = [schedule >= 0]
        constraints += [cvx.sum(schedule, axis=1) <= subscription_level]  # Keep charging below subscription level
        for i in range(self.num_sessions):
            constraints += [schedule[:, i] <= np.maximum(np.max(self.power[:, i]), self.charge_rate)]
            if self.departure_inds[i] >= self.arrival_inds[i]:
                if self.arrival_inds[i] > 0:
                    constraints += [schedule[np.arange(0, int(self.arrival_inds[i])), i] <= 0]
                if self.departure_inds[i] < 96:
                    constraints += [schedule[np.arange(int(self.departure_inds[i]), 96), i] <= 0]
            else:
                constraints += [schedule[np.arange(int(self.departure_inds[i]), int(self.arrival_inds[i])), i] <= 0]

        constraints += [0.25 * cvx.sum(schedule, axis=0) == self.energies]

        prob = cvx.Problem(cvx.Minimize(obj), constraints)
        result = prob.solve(solver=cvx.MOSEK)
        if verbose:
            print('Given subscription level', subscription_level, 'the objective result is', result)

        self.pge_cev_controlled_power = schedule.value
        # The optimization may fail in this case if there is not enough flexibility to meet the subscription rate cap
        # constraint. In that case the output is saved as -1's to flag the problem without throwing an error.
        try:
            self.controlled_total_load = np.sum(schedule.value, axis=1)
        except:
            try:
                self.controlled_total_load = -1 * np.ones((96, ))
            except:
                donothing=1
                
    def simple_cap_controlled_load(self, cap_level, verbose=False):
        """Implements the charging control for a simple control set up with a cap on the total load. The value of the
        cap is set in the cap_level input. Please refer to the first control method, `sdge_controlled_load', for
        comments on the optimization set up and constraints which are common between the two.
        """
        schedule = cvx.Variable((96, self.num_sessions))
        obj = 1.0
        
        constraints = [schedule >= 0]
        constraints += [cvx.sum(schedule, axis=1) <= cap_level]  # Cap on total charging
        for i in range(self.num_sessions):
            constraints += [schedule[:, i] <= np.maximum(np.max(self.power[:, i]), self.charge_rate)]
            if self.departure_inds[i] >= self.arrival_inds[i]:
                if self.arrival_inds[i] > 0:
                    constraints += [schedule[np.arange(0, int(self.arrival_inds[i])), i] <= 0]
                if self.departure_inds[i] < 96:
                    constraints += [schedule[np.arange(int(self.departure_inds[i]), 96), i] <= 0]
            else:
                constraints += [schedule[np.arange(int(self.departure_inds[i]), int(self.arrival_inds[i])), i] <= 0]

        constraints += [0.25 * cvx.sum(schedule, axis=0) == self.energies]

        prob = cvx.Problem(cvx.Minimize(obj), constraints)
        result = prob.solve(solver=cvx.MOSEK)
        
        self.simple_cap_controlled_power = schedule.value
        # In case the cap is infeasible for a given case:
        try:
            self.controlled_total_load = np.sum(schedule.value, axis=1)
        except:
            try:
                self.controlled_total_load = -1 * np.ones((96, ))
            except:
                donothing=1   
                
    def minpeak_controlled_load(self, verbose=False):
        """Implements the charging control for a simple peak minimization control. Please refer to the first control
        method, `sdge_controlled_load', for comments on the optimization set up and constraints which are common
        between the two.
        """

        schedule = cvx.Variable((96, self.num_sessions))
        obj = cvx.max(cvx.sum(schedule, axis=1))  # Minimize the peak total load reached at any time during the day
        
        constraints = [schedule >= 0]
        for i in range(self.num_sessions):
            constraints += [schedule[:, i] <= np.maximum(np.max(self.power[:, i]), self.charge_rate)]
            if self.departure_inds[i] >= self.arrival_inds[i]:
                if self.arrival_inds[i] > 0:
                    constraints += [schedule[np.arange(0, int(self.arrival_inds[i])), i] <= 0]
                if self.departure_inds[i] < 96:
                    constraints += [schedule[np.arange(int(self.departure_inds[i]), 96), i] <= 0]
            else:
                constraints += [schedule[np.arange(int(self.departure_inds[i]), int(self.arrival_inds[i])), i] <= 0]

        constraints += [0.25 * cvx.sum(schedule, axis=0) == self.energies]

        prob = cvx.Problem(cvx.Minimize(obj), constraints)
        result = prob.solve(solver=cvx.MOSEK)
        
        self.minpeak_controlled_power = schedule.value
        # Not likely necessary since there is no cap constraint, but this was implemented just in case this method
        # throws an error:
        try:
            self.controlled_total_load = np.sum(schedule.value, axis=1)
        except:
            try:
                self.controlled_total_load = -1 * np.ones((96, ))
            except:
                donothing=1                   

    def pge_cev_demandcharge_controlled_load(self, subscription_level=None, verbose=False):
        """Implements the charging control for the PG&E CEV rate but treating the subscription rate like a demand charge
        rather than a cap. Please refer to the first control method, `sdge_controlled_load', for comments on the
        optimization set up and constraints which are common between the two.
        """

        peak_inds, partpeak_inds, offpeak_inds, energy_prices, subscription_rate_per50kw = pge_cev_values()

        schedule = cvx.Variable((96, self.num_sessions))
        obj = cvx.matmul(cvx.sum(schedule, axis=1), energy_prices.reshape((np.shape(energy_prices)[0], 1)))
        # Demand charge on the full time period, demand charge price based on the subscription level price:
        obj += (subscription_rate_per50kw / 50)*cvx.max(cvx.sum(schedule, axis=1))
        
        constraints = [schedule >= 0]
        for i in range(self.num_sessions):
            constraints += [schedule[:, i] <= np.maximum(np.max(self.power[:, i]), self.charge_rate)]
            if self.departure_inds[i] >= self.arrival_inds[i]:
                if self.arrival_inds[i] > 0:
                    constraints += [schedule[np.arange(0, int(self.arrival_inds[i])), i] <= 0]
                if self.departure_inds[i] < 96:
                    constraints += [schedule[np.arange(int(self.departure_inds[i]), 96), i] <= 0]
            else:
                constraints += [schedule[np.arange(int(self.departure_inds[i]), int(self.arrival_inds[i])), i] <= 0]

        constraints += [0.25 * cvx.sum(schedule, axis=0) == self.energies]

        prob = cvx.Problem(cvx.Minimize(obj), constraints)
        result = prob.solve(solver=cvx.MOSEK)
        if verbose:
            print('Given subscription level', subscription_level, 'the objective result is', result)

        self.pge_cev_demandcharge_controlled_power = schedule.value
        # Not likely necessary since there is no cap constraint, but this was implemented just in case this method
        # throws an error:
        try:
            self.controlled_total_load = np.sum(schedule.value, axis=1)
        except:
            try:
                self.controlled_total_load = -1 * np.ones((96, ))
            except:
                donothing=1
                
    def pge_cev_energyonly_controlled_load(self, subscription_level=None, verbose=False):
        """Implements the charging control for the PG&E CEV rate without including the subscription at all, just using
        the TOU rate from that schedule - it is up to date on reflecting peak solar and the duck curve issues.
        Please refer to the first control method, `sdge_controlled_load', for comments on the
        optimization set up and constraints which are common between the two.
        """

        peak_inds, partpeak_inds, offpeak_inds, energy_prices, subscription_rate_per50kw = pge_cev_values()

        schedule = cvx.Variable((96, self.num_sessions))
        # Just the energy prices in the objective function:
        obj = cvx.matmul(cvx.sum(schedule, axis=1), energy_prices.reshape((np.shape(energy_prices)[0], 1)))
        
        constraints = [schedule >= 0]
        for i in range(self.num_sessions):
            constraints += [schedule[:, i] <= np.maximum(np.max(self.power[:, i]), self.charge_rate)]
            if self.departure_inds[i] >= self.arrival_inds[i]:
                if self.arrival_inds[i] > 0:
                    constraints += [schedule[np.arange(0, int(self.arrival_inds[i])), i] <= 0]
                if self.departure_inds[i] < 96:
                    constraints += [schedule[np.arange(int(self.departure_inds[i]), 96), i] <= 0]
            else:
                constraints += [schedule[np.arange(int(self.departure_inds[i]), int(self.arrival_inds[i])), i] <= 0]

        constraints += [0.25 * cvx.sum(schedule, axis=0) == self.energies]

        prob = cvx.Problem(cvx.Minimize(obj), constraints)
        result = prob.solve(solver=cvx.MOSEK)
        if verbose:
            print('Given subscription level', subscription_level, 'the objective result is', result)

        self.pge_cev_energyonly_controlled_power = schedule.value
        # Not likely necessary since there is no cap constraint, but this was implemented just in case this method
        # throws an error:
        try:
            self.controlled_total_load = np.sum(schedule.value, axis=1)
        except:
            try:
                self.controlled_total_load = -1 * np.ones((96, ))
            except:
                donothing=1

    def e19_controlled_load(self, verbose=False):
        """Implements the charging control for the PG&E E19 rate schedule. This is not specific to EVs but has been how
        sites like Google campus traditionally are charged for their loads. It includes TOU and demand charges.
        Please refer to the first control method, `sdge_controlled_load', for comments on the
        optimization set up and constraints which are common between the two.
        """
        peak_inds, partpeak_inds, offpeak_inds, energy_prices, rate_demand_peak, rate_demand_partpeak, rate_demand_overall = e19_values()

        schedule = cvx.Variable((96, self.num_sessions))
        obj = cvx.matmul(cvx.sum(schedule, axis=1), energy_prices.reshape((np.shape(energy_prices)[0], 1)))  # TOU
        obj += rate_demand_overall * cvx.max(cvx.sum(schedule, axis=1))  # Demand charge on the whole day
        obj += rate_demand_peak * cvx.max(cvx.sum(schedule[peak_inds, :], axis=1))  # Peak period demand charge
        obj += rate_demand_partpeak * cvx.max(cvx.sum(schedule[partpeak_inds, :], axis=1))  # Shoulder period demand charge

        constraints = [schedule >= 0]
        for i in range(self.num_sessions):
            constraints += [schedule[:, i] <= np.maximum(np.max(self.power[:, i]), self.charge_rate)]
            if self.departure_inds[i] >= self.arrival_inds[i]:
                if self.arrival_inds[i] > 0:
                    constraints += [schedule[np.arange(0, int(self.arrival_inds[i])), i] <= 0]
                if self.departure_inds[i] < 96:
                    constraints += [schedule[np.arange(int(self.departure_inds[i]), 96), i] <= 0]
            else:
                constraints += [schedule[np.arange(int(self.departure_inds[i]), int(self.arrival_inds[i])), i] <= 0]

        constraints += [0.25 * cvx.sum(schedule, axis=0) == self.energies]

        prob = cvx.Problem(cvx.Minimize(obj), constraints)
        result = prob.solve(solver=cvx.MOSEK)
        # Not likely necessary since there is no cap constraint, but this was implemented just in case this method
        # throws an error:
        if verbose:
            print('The objective result: ', result)
        if schedule.value is None:
            print('Optimization failed')
        else:
            self.e19_controlled_power = schedule.value
            self.controlled_total_load = np.sum(schedule.value, axis=1)

    def sce_touev8_controlled_load(self, verbose=False, summer=True):
        """Implements the charging control for the SCE TOU-EV8 rate schedule which includes only a TOU rate, no demand
        charges or subscriptions.
        Please refer to the first control method, `sdge_controlled_load', for comments on the
        optimization set up and constraints which are common between the two.
        """

        peak_inds, partpeak_inds, offpeak_inds, superoffpeak_inds, energy_prices = sce_touev8_values(summer=summer)

        schedule = cvx.Variable((96, self.num_sessions))
        obj = cvx.matmul(cvx.sum(schedule, axis=1), energy_prices.reshape((np.shape(energy_prices)[0], 1)))

        constraints = [schedule >= 0]
        for i in range(self.num_sessions):
            constraints += [schedule[:, i] <= np.maximum(np.max(self.power[:, i]), self.charge_rate)]
            if self.departure_inds[i] >= self.arrival_inds[i]:
                if self.arrival_inds[i] > 0:
                    constraints += [schedule[np.arange(0, int(self.arrival_inds[i])), i] <= 0]
                if self.departure_inds[i] < 96:
                    constraints += [schedule[np.arange(int(self.departure_inds[i]), 96), i] <= 0]
            else:
                constraints += [schedule[np.arange(int(self.departure_inds[i]), int(self.arrival_inds[i])), i] <= 0]

        constraints += [0.25 * cvx.sum(schedule, axis=0) == self.energies]

        prob = cvx.Problem(cvx.Minimize(obj), constraints)
        result = prob.solve(solver=cvx.MOSEK)
        if verbose:
            print('The objective result: ', result)

        self.sce_touev8_controlled_power = schedule.value
        self.controlled_total_load = np.sum(schedule.value, axis=1)


def pge_cev_values():
    rate_energy_peak = 0.30267
    rate_energy_partpeak = 0.11079
    rate_energy_offpeak = 0.08882

    subscription_rate_per50kw = 183.86
    peak_inds = np.arange(int(16*4), int(22*4))  # Peak from 4pm to 10pm
    # Partpeak from 10pm to 9am and 2pm to 4pm
    partpeak_inds = np.concatenate((np.arange(int(22*4), int(24*4)), np.arange(0, int(9*4)), np.arange(int(14*4), int(16*4))))
    offpeak_inds = np.arange(int(9*4), int(14*4))  # Offpeak from 9am to 2pm (peak solar)

    # energy_prices is ((96,)) shape
    energy_prices = np.concatenate(
        (np.repeat(rate_energy_partpeak, int(9 * 4)), np.repeat(rate_energy_offpeak, int(5 * 4)),
         np.repeat(rate_energy_partpeak, int(2 * 4)), np.repeat(rate_energy_peak, int(6 * 4)),
         np.repeat(rate_energy_partpeak, int(2 * 4))))

    return peak_inds, partpeak_inds, offpeak_inds, energy_prices, subscription_rate_per50kw


def e19_values():
    rate_energy_peak = 0.16997
    rate_energy_partpeak = 0.12236
    rate_energy_offpeak = 0.09082
    rate_demand_peak = 21.23
    rate_demand_partpeak = 5.85
    rate_demand_overall = 19.10

    # Peak is 12pm to 6pm, partpeak is 8:30am to 12pm and 6pm to 9:30pm, offpeak is 9:30pm to 8:30am
    energy_prices = np.concatenate(
        (np.repeat(rate_energy_offpeak, int(8.5 * 4)), np.repeat(rate_energy_partpeak, int(3.5 * 4)),
         np.repeat(rate_energy_peak, int(6 * 4)), np.repeat(rate_energy_partpeak, int(3.5 * 4)),
         np.repeat(rate_energy_offpeak, int(2.5 * 4))))

    peak_inds = np.arange(int(12 * 4), int(18 * 4))
    partpeak_inds = np.concatenate((np.arange(int(8.5 * 4), int(12 * 4)), np.arange(int(18 * 4), int(21.5 * 4))))
    offpeak_inds = np.concatenate((np.arange(0, int(8.5 * 4)), np.arange(int(21.5 * 4), int(24 * 4))))

    return peak_inds, partpeak_inds, offpeak_inds, energy_prices, rate_demand_peak, rate_demand_partpeak, rate_demand_overall


def sce_touev8_values(summer=True):
    rate_energy_peak = 0.37
    rate_energy_partpeak = 0.26
    rate_energy_offpeak = 0.13
    rate_energy_superoffpeak = 0.08

    if summer:
        # Peak is 3pm to 8pm, offpeak is 8pm to 3pm.
        energy_prices = np.concatenate(
            (np.repeat(rate_energy_offpeak, int(15 * 4)), np.repeat(rate_energy_peak, int(5 * 4)),
             np.repeat(rate_energy_offpeak, int(4 * 4))))

        peak_inds = np.arange(int(15 * 4), int(20 * 4))
        partpeak_inds = []
        offpeak_inds = np.concatenate((np.arange(0, int(15 * 4)), np.arange(int(20 * 4), int(24 * 4))))
        superoffpeak_inds = []
    else:
        energy_prices = np.concatenate(
            (np.repeat(rate_energy_offpeak, int(7 * 4)), np.repeat(rate_energy_superoffpeak, int(8 * 4)),
             np.repeat(rate_energy_partpeak, int(5 * 4)), np.repeat(rate_energy_offpeak, int(4 * 4))))
        peak_inds = []
        partpeak_inds = np.arange(int(15 * 4), int(20 * 4))
        offpeak_inds = np.concatenate((np.arange(0, int(7 * 4)), np.arange(int(20 * 4), int(24 * 4))))
        superoffpeak_inds = np.arange(int(7 * 4), int(15 * 4))

    return peak_inds, partpeak_inds, offpeak_inds, superoffpeak_inds, energy_prices


def sdge_values(method='median', summer=True, percentile=50):

    # This csv includes all the prices from the  month of july - the prices were dynamic, not based on a preset TOU
    # time. They are organized into days in rate_days and then energy_prices is calculated by either taking the median
    # across the days, some other percentile, or picking a random particular day.
    if summer:
        try:
            sdge = pd.read_csv('sdge_pricing_july2019.csv', header=None)
        except:
            sdge = pd.read_csv('/Users/spowell2/Documents/sdge_pricing_july2019.csv', header=None)

        weekdays = [1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 22, 23, 24, 25, 26, 29, 30, 31, 32, 33]
        rate_days = np.zeros((24, max(weekdays) + 1))
        ct = 0
        for i in range(max(weekdays) + 1):
            if i in weekdays:
                rate_days[:, ct] = sdge.loc[np.arange(i * 24, (i + 1) * 24), 2]
                ct += 1
    else:
        print('Get winter prices from sdge.')

    if method == 'median':
        energy_prices = np.median(rate_days, axis=1)
    elif method == 'percentile':
        energy_prices = np.percentile(rate_days, percentile, axis=1)
    elif method == 'random':
        energy_prices = rate_days[:, int(np.random.choice(np.arange(0, np.shape(rate_days)[1])))]

    energy_prices = np.repeat(energy_prices, 4)  # Extend to 15min intervals

    return energy_prices
