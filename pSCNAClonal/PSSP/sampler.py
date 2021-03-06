#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
# =============================================================================
#      FileName: sampler.py
#        Author: Chu Yanshuo
#         Email: chu@yanshuo.name
#      HomePage: http://yanshuo.name
#       Version: 0.0.1
#    LastChange: 2017-04-06 09:55:21
#       History: @author: Andrew Roth
# =============================================================================
'''
from __future__ import division

from collections import namedtuple

from pydp.base_measures import BaseMeasure


from pydp.partition import Partition

from pydp.samplers.atom import BaseMeasureAtomSampler
from pydp.samplers.concentration import GammaPriorConcentrationSampler
from pydp.samplers.partition import AuxillaryParameterPartitionSampler

from pydp.rvs import uniform_rvs


class DirichletProcessSampler(object):

    def __init__(
            self,
            cluster_density,
            alpha=None,
            alpha_shape=None,
            alpha_rate=None):
        self.base_measure = PyCloneBaseMeasure()

        self.partition_sampler = AuxillaryParameterPartitionSampler(
            self.base_measure, cluster_density)

        self.atom_sampler = BaseMeasureAtomSampler(
            self.base_measure, cluster_density)

        if alpha is None:
            self.alpha = 1

            self.update_alpha = True

            self.concentration_sampler =\
                GammaPriorConcentrationSampler(alpha_shape, alpha_rate)
        else:
            self.alpha = alpha

            self.update_alpha = False

        self.num_iters = 0

    @property
    def state(self):
        return {
            'alpha': self.alpha,
            'cellular_frequencies': [
                param.phi for param in self.partition.item_values],
            'labels': self.partition.labels,
            'phi': [
                param.phi for param in self.partition.cell_values]}

    def initialise_partition(self, data):
        self.partition = Partition()

        for item, _ in enumerate(data):
            self.partition.add_cell(self.base_measure.random())
            self.partition.add_item(item, item)

    def sample(self, data, results_db, num_iters, print_freq=100):
        self.initialise_partition(data)

        for i in range(num_iters):
            if i % print_freq == 0:
                print self.num_iters, self.partition.number_of_cells, self.alpha

            self.interactive_sample(data)

            results_db.update_trace(self.state)

            self.num_iters += 1

    def interactive_sample(self, data):
        if self.update_alpha:
            self.alpha = self.concentration_sampler.sample(
                self.alpha, self.partition.number_of_cells,
                self.partition.number_of_items)

        self.partition_sampler.sample(data, self.partition, self.alpha)

        self.atom_sampler.sample(data, self.partition)

    def _init_partition(self, base_measure):
        self.partition = Partition()

        for item, _ in enumerate(self.data):
            self.partition.add_cell(base_measure.random())

            self.partition.add_item(item, item)


class PyCloneBaseMeasure(BaseMeasure):

    def __init__(self):
        pass

    def random(self):
        phi = uniform_rvs(0, 1)
        return PyCloneParameter(phi)

    def log_p(self, data):
        return 1


PyCloneParameter = namedtuple('PyCloneParameter', ['phi'])
