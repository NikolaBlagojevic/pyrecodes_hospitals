import math
import numpy as np
from pyrecodes_hospitals import ProbabilityDistribution

class TestProbabilityDistribution():

    def test_deterministic(self):
        parameters = {'Value': 5}
        dist = ProbabilityDistribution.Deterministic(parameters)
        assert dist.sample() == 5

    def test_lognormal(self):
        bool_list = []
        num_samples = 100000
        parameters_list = [{'Median': 1, 'Dispersion': 0}, {'Median': 1, 'Dispersion': 1},
                           {'Median': 0.1, 'Dispersion': 1}, {'Median': 5, 'Dispersion': 0.5}]
        target_medians = [1, 1, 0.1, 5]
        target_dispersions = [0, 1, 1, 0.5]
        for target_median, target_dispersion, parameters in zip(target_medians, target_dispersions, parameters_list):
            dist = ProbabilityDistribution.Lognormal(parameters)
            samples = []
            for _ in range(num_samples):
                samples.append(dist.sample())
            bool_list.append(math.isclose(target_median, np.median(samples), abs_tol=0.03))
            bool_list.append(math.isclose(target_dispersion, np.std(np.log(samples)), abs_tol=0.03))
        assert all(bool_list)
