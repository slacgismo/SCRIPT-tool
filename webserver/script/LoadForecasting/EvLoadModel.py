import numpy as np
import scipy
import scipy.interpolate
import pickle
import matplotlib.pyplot as plt
import s3fs
import boto3
from scipy.interpolate import splev, splrep
from sklearn.preprocessing import normalize
from sklearn.linear_model import LinearRegression
import copy


class EVLoadModel(object):
    def __init__(self, config):

        self.config = config

        self.num_segments = len(config.categories_dict['Segment'])
        self.labels = list(set(self.config.categories_dict['Label']))
        self.num_labels = len(self.labels)
        self.load_segments = {}

        self.control_object = None
        self.sampled_loads_dict = {}
        self.sampled_controlled_loads_dict = {}
        self.discontinuity_dict = {}

        self.controlled_load_segments_dict = None
        if self.config.sample_fast:
            dim1 = self.config.num_time_steps
        else:
            dim1 = self.config.fast_num_time_steps
        self.ev_segmented_load = np.zeros((dim1, self.num_segments))
        self.controlled_segmented_load = np.zeros((dim1, self.num_segments))
        self.ev_labeled_load = np.zeros((dim1, self.num_labels))
        self.basic_load = np.zeros((dim1, ))
        self.total_load = np.zeros((dim1, ))
        self.nonEV_load = np.zeros((dim1, ))
        self.controlled_load = np.zeros((dim1, ))
        self.controlled_load_segment = np.zeros((dim1,))

    def calculate_basic_load(self, verbose=True, energies_given=None):

        for segment_number in range(len(self.config.categories_dict['Segment'])):
            num_vehicles = self.config.categories_dict['Vehicles'][segment_number]
            if verbose:
                print('Calculating for segment: ', self.config.categories_dict['Segment'][segment_number])
                print('Num vehicles:', num_vehicles)

            if num_vehicles > 0:
                num_ts = self.config.categories_dict['Num Time Steps'][segment_number]

                if self.config.mixed_distributions:
                    # print('Mixed distributions')
                    sample_output = None
                    for key, val in self.config.mixed_distribution_proportions.items():
                        if val > 0:
                            key1 = self.config.gmm_folder_path + self.config.categories_dict['GMM Sub Path'][segment_number]
                            key1 = key1.replace('allbatt', key)
                            response = self.config.s3client.get_object(Bucket=self.config.gmm_bucket, Key=key1)
                            joint_gmm = pickle.loads(response['Body'].read())
                            num_here = int(np.round(num_vehicles * val))
                            if num_here > 0:
                                if sample_output is not None:
                                    sample_output = np.concatenate((sample_output, joint_gmm.sample(num_here)[0]))
                                else:
                                    sample_output = joint_gmm.sample(num_here)[0]
                else:
                    key = self.config.gmm_folder_path + self.config.categories_dict['GMM Sub Path'][segment_number]
                    if self.config.gmm_bucket is None:
                        joint_gmm = pickle.load(open(key, "rb"))
                    else:
                        response = self.config.s3client.get_object(Bucket=self.config.gmm_bucket, Key=key)
                        joint_gmm = pickle.loads(response['Body'].read())
                    if self.config.reweight_gmms:
                        joint_gmm = self.rebalance_gmm(joint_gmm, segment_number)

                    sample_output = joint_gmm.sample(num_vehicles)[0]

                sample_output = sample_output[np.random.choice(np.shape(sample_output)[0], np.shape(sample_output)[0], replace=False), :]

                start_times = (self.config.categories_dict['Start Time Scaler'][segment_number] * np.mod(
                    sample_output[:, 0], 24 * 3600)).astype(int)
                energies = np.clip(np.abs(sample_output[:, 1]), 0,
                                   self.config.categories_dict['Energy Clip'][segment_number])

                end_times, load = EVLoadModel.end_times_and_load(self, start_times, energies,
                                                                 self.config.categories_dict['Rate'][segment_number],
                                                                 time_steps_per_hour=
                                                                 self.config.categories_dict['Time Steps Per Hour'][
                                                                     segment_number],
                                                                 num_time_steps=
                                                                 self.config.categories_dict['Num Time Steps'][
                                                                     segment_number])

            else:
                start_times = None
                end_times = None
                energies = None
                if self.config.categories_dict['Time Steps Per Hour'][segment_number] >= 60:
                    load = np.zeros((self.config.fast_num_time_steps, ))
                else:
                    load = np.zeros((self.config.num_time_steps, ))

            self.load_segments[self.config.categories_dict['Segment'][segment_number]] = {'Num Vehicles': num_vehicles,
                                                                                          'Start Times': start_times,
                                                                                          'End Times': end_times,
                                                                                          'Energies': energies,
                                                                                          'Load': load}

        self.sum_and_sample_load(load_segments_dict=self.load_segments)

    def sum_and_sample_load(self, overwrite=True, load_segments_dict=None, discontinuity_dict={}):

        if load_segments_dict is None:
            load_segments_dict = copy.deepcopy(self.load_segments)
        ev_segmented_load = np.zeros(np.shape(self.ev_segmented_load))

        sampled_loads_dict = {}
        for segment_number in range(len(self.config.categories_dict['Segment'])):
            load = load_segments_dict[self.config.categories_dict['Segment'][segment_number]]['Load']
            if self.config.sample_fast:
                if self.config.categories_dict['Time Steps Per Hour'][segment_number] < 60:
                    ev_segmented_load_here = load
                else:
                    ev_segmented_load_here = load[np.arange(0, self.config.fast_num_time_steps, int(
                        self.config.fast_time_steps_per_hour / self.config.time_steps_per_hour))]
            else:
                if np.shape(load_segments_dict[self.config.categories_dict['Segment'][segment_number]]['Load'])[0] < 1440:
                    if self.config.categories_dict['Segment'][segment_number] in discontinuity_dict.keys():
                        ev_segmented_load_here = self.extend_to_fast(load, discontinuity_dict[self.config.categories_dict['Segment'][segment_number]])
                    else:
                        ev_segmented_load_here = self.extend_to_fast(load)
                else:
                    ev_segmented_load_here = load

            sampled_loads_dict[self.config.categories_dict['Segment'][segment_number]] = ev_segmented_load_here
            ev_segmented_load[:, segment_number] = ev_segmented_load_here

        if overwrite:
            self.ev_segmented_load = ev_segmented_load
            self.basic_load = np.sum(self.ev_segmented_load, axis=1)
            self.sampled_loads_dict = copy.deepcopy(sampled_loads_dict)
            self.sampled_loads_dict['Total'] = self.basic_load

        else:
            return ev_segmented_load, np.sum(ev_segmented_load, axis=1), sampled_loads_dict

    def extend_to_fast(self, load, discontinuity_hour=None):

        if discontinuity_hour is None:
            xset1 = np.arange(0, self.config.fast_num_time_steps + 1,
                              int(self.config.fast_time_steps_per_hour / 4))  # 1 min to 15 min intervals
            xset2 = np.arange(0, self.config.fast_num_time_steps + 1)
            xset3 = np.arange(0, self.config.fast_num_time_steps)
            spl = splrep(xset1, np.append(load, load[0]))
            output = splev(xset2, spl)[xset3]

        else:

            slow_discontinuity_ind = int(discontinuity_hour * self.config.time_steps_per_hour)
            fast_discontinuity_ind = int(discontinuity_hour * self.config.fast_time_steps_per_hour)
            output = np.zeros((self.config.fast_num_time_steps, ))

            xset1 = np.arange(0, self.config.fast_num_time_steps + 1,
                              int(self.config.fast_time_steps_per_hour / self.config.time_steps_per_hour))
            xset2 = np.arange(0, self.config.fast_num_time_steps + 1)
            xset3 = np.arange(0, self.config.fast_num_time_steps)

            spl1 = splrep(xset1[np.arange(0, slow_discontinuity_ind + 1)],
                          np.append(load[np.arange(0, slow_discontinuity_ind)], load[slow_discontinuity_ind-1]))
            output[np.arange(0, fast_discontinuity_ind)] = splev(xset2[np.arange(0, fast_discontinuity_ind + 1)], spl1)[
                xset3[np.arange(0, fast_discontinuity_ind)]]

            spl2 = splrep(xset1[np.arange(slow_discontinuity_ind, self.config.num_time_steps+1)],
                          np.append(load[np.arange(slow_discontinuity_ind, self.config.num_time_steps)], load[0]))
            output[np.arange(fast_discontinuity_ind, self.config.fast_num_time_steps)] = \
            splev(xset2[np.arange(fast_discontinuity_ind, self.config.fast_num_time_steps + 1)], spl2)[
                xset3[np.arange(0, self.config.fast_num_time_steps - fast_discontinuity_ind)]]

        return output

    def plot_labeled_load(self, plotting_data=None, other_labels=None, save_str=None, force_mw=False, set_ylim=None):

        if plotting_data is None:
            plotting_data = self.ev_segmented_load

        x = (24 / np.shape(plotting_data)[0]) * np.arange(0, np.shape(plotting_data)[0])
        mark = np.zeros(np.shape(x))
        scaling = 1
        unit = 'kW'
        if (np.max(plotting_data) > 1e5) or force_mw:
            scaling = 1 / 1000
            unit = 'MW'
        plt.figure(figsize=(8, 5))
        for segment_number in range(len(self.config.categories_dict['Segment'])):
            plt.plot(x, scaling * (mark + plotting_data[:, segment_number]))
            plt.fill_between(x, scaling * mark, scaling * (mark + plotting_data[:, segment_number]), alpha=0.5)
            mark += plotting_data[:, segment_number]
        plt.plot(x, scaling * mark, 'k')
        if other_labels is None:
            plt.legend(labels=self.config.categories_dict['Label'], fontsize=12, loc='upper left')
        else:
            plt.legend(labels=other_labels, fontsize=12, loc=(0,1.05), ncol=3)
        plt.xlim([0, np.max(x)])
        if set_ylim is None:
            plt.ylim([0, 1.1 * np.max(scaling * mark)])
        else:
            plt.ylim([0, set_ylim])
        plt.ylabel(unit, fontsize=14)
        plt.xlabel('Hour', fontsize=14)
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        if save_str is not None:
            plt.tight_layout()
            plt.savefig(save_str, bbox_inches='tight')
        plt.show()

    def end_times_and_load(self, start_times, energies, rate, time_steps_per_hour=None, num_time_steps=None):

        if time_steps_per_hour is None:
            time_steps_per_hour = self.config.time_steps_per_hour
        if num_time_steps is None:
            num_time_steps = self.config.num_time_steps
        num = np.shape(start_times)[0]
        load = np.zeros((num_time_steps,))
        end_times = np.zeros(np.shape(start_times)).astype(int)

        lengths = (time_steps_per_hour * energies / rate).astype(int)
        extra_charges = energies - lengths * rate / time_steps_per_hour
        inds1 = np.where((start_times + lengths) > num_time_steps)[0]
        inds2 = np.delete(np.arange(0, np.shape(end_times)[0]), inds1)

        end_times[inds1] = (np.minimum(start_times[inds1].astype(int)+lengths[inds1]-num_time_steps, num_time_steps)).astype(int)
        end_times[inds2] = (start_times[inds2] + lengths[inds2]).astype(int)
        inds3 = np.where(end_times >= num_time_steps)[0]
        inds4 = np.delete(np.arange(0, np.shape(end_times)[0]), inds3)

        for i in range(len(inds1)):
            idx = int(inds1[i])
            load[np.arange(int(start_times[idx]), num_time_steps)] += rate * np.ones((num_time_steps - int(start_times[idx]),))
            load[np.arange(0, end_times[idx])] += rate * np.ones((end_times[idx],))
        for i in range(len(inds2)):
            idx = int(inds2[i])
            load[np.arange(int(start_times[idx]), end_times[idx])] += rate * np.ones((lengths[idx],))
        load[0] += np.sum(extra_charges[inds3] * time_steps_per_hour)
        for i in range(len(inds4)):
            load[end_times[int(inds4[i])]] += extra_charges[int(inds4[i])] * time_steps_per_hour

        return end_times, load

    def apply_control(self, control_rule='PGEe19', segment='Work'):

        response = self.config.s3client.get_object(Bucket=self.config.control_bucket,
                                                   Key=self.config.control_folder_path+'/control_'+str(control_rule)+'_rerun.p')
        self.control_object = pickle.loads(response['Body'].read())

        x = self.load_segments[segment]['Load'].copy()
        if x.shape[0] == self.config.fast_num_time_steps:  # must be 96 since thats how the model was trained
            x = x[np.arange(0, self.config.fast_num_time_steps, int(self.config.fast_time_steps_per_hour / 4))]
        rescale_load, normalizing_coefficient = normalize(np.reshape(x, (1, -1)), norm='max', axis=1,
                                                          return_norm=True)
        self.controlled_load_segment = normalizing_coefficient * self.control_object.predict(rescale_load).ravel()

        if self.controlled_load_segments_dict is None:
            self.controlled_load_segments_dict = copy.deepcopy(self.load_segments)
        self.controlled_load_segments_dict[segment]['Load'] = self.controlled_load_segment.ravel()
        segmented_load, total_load, sampled_load_dict = self.sum_and_sample_load(overwrite=False,
                                                                                 load_segments_dict=self.controlled_load_segments_dict,
                                                                                 discontinuity_dict=self.discontinuity_dict)

        self.controlled_segmented_load = segmented_load
        self.controlled_load = total_load
        self.sampled_controlled_loads_dict = sampled_load_dict

    def timer_control(self, segment='Residential L2', percent=0.4, start_hour=23):

        segment_number = np.where(np.array(self.config.categories_dict['Segment']) == segment)[0][0]

        num_starts = self.load_segments[segment]['Start Times'].shape[0]
        which_starts = np.random.choice(np.arange(0, num_starts), int(percent * num_starts))
        new_start_times = np.copy(self.load_segments[segment]['Start Times'])
        new_start_times[which_starts] = int(start_hour * self.config.categories_dict['Time Steps Per Hour'][segment_number])

        end_times, load = EVLoadModel.end_times_and_load(self, new_start_times, self.load_segments[segment]['Energies'],
                                                                    self.config.categories_dict['Rate'][segment_number],
                                                                    time_steps_per_hour=
                                                                    self.config.categories_dict['Time Steps Per Hour'][
                                                                        segment_number],
                                                                    num_time_steps=
                                                                    self.config.categories_dict['Num Time Steps'][
                                                                        segment_number])

        if self.controlled_load_segments_dict is None:
            self.controlled_load_segments_dict = copy.deepcopy(self.load_segments)
        self.controlled_load_segments_dict[segment]['Load'] = load
        self.controlled_load_segments_dict[segment]['Start Times'] = new_start_times
        self.controlled_load_segments_dict[segment]['End Times'] = end_times
        self.discontinuity_dict[segment] = start_hour
        segmented_load, total_load, sampled_load_dict = self.sum_and_sample_load(overwrite=False,
                                                                                 load_segments_dict=self.controlled_load_segments_dict,
                                                                                 discontinuity_dict=self.discontinuity_dict)

        self.controlled_segmented_load = segmented_load
        self.controlled_load = total_load
        self.sampled_controlled_loads_dict = sampled_load_dict

    def rebalance_gmm(self, joint_gmm, segment_number):

        new_weights = self.config.new_gmm_weights[segment_number]

        all_inds = np.arange(0, np.shape(joint_gmm.weights_)[0])
        total_rem = 1
        for key, val in new_weights.items():
            joint_gmm.weights_[key] = val
            total_rem -= val
        other_keys = np.delete(all_inds, list(new_weights.keys()))
        joint_gmm.weights_[other_keys] = joint_gmm.weights_[other_keys] * total_rem / sum(joint_gmm.weights_[other_keys])
        return joint_gmm

    def special_timers(self, segment='Residential L2', percents=None, start_hours=None):

        # for multiple timers with fraction of drivers each
        if percents is None:
            percents = [0.1, 0.1]; start_hours = [22, 23]
        segment_number = np.where(np.array(self.config.categories_dict['Segment']) == segment)[0][0]

        num_starts = self.load_segments[segment]['Start Times'].shape[0]

        all_inds = np.arange(0, num_starts)
        new_start_times = np.copy(self.load_segments[segment]['Start Times'])
        for seg in range(len(percents)):
            which_starts = np.random.choice(all_inds, int(percents[seg]*num_starts))
            new_start_times[which_starts] = int(
                start_hours[seg] * self.config.categories_dict['Time Steps Per Hour'][segment_number])
            all_inds = np.copy(np.delete(all_inds, which_starts))

        end_times, load = EVLoadModel.end_times_and_load(self, new_start_times, self.load_segments[segment]['Energies'],
                                                         self.config.categories_dict['Rate'][segment_number],
                                                         time_steps_per_hour=
                                                         self.config.categories_dict['Time Steps Per Hour'][
                                                             segment_number],
                                                         num_time_steps=
                                                         self.config.categories_dict['Num Time Steps'][
                                                             segment_number])

        if self.controlled_load_segments_dict is None:
            self.controlled_load_segments_dict = copy.deepcopy(self.load_segments)
        self.controlled_load_segments_dict[segment]['Load'] = load
        self.controlled_load_segments_dict[segment]['Start Times'] = new_start_times
        self.controlled_load_segments_dict[segment]['End Times'] = end_times
        segmented_load, total_load, sampled_load_dict = self.sum_and_sample_load(overwrite=False,
                                                                                 load_segments_dict=self.controlled_load_segments_dict)
        self.controlled_segmented_load = segmented_load
        self.controlled_load = total_load
        self.sampled_controlled_loads_dict = sampled_load_dict
