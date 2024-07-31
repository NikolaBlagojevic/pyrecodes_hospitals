import pytest
import math
import copy
import numpy as np
from pyrecodes_hospitals import Relation
from pyrecodes_hospitals import ComponentRecoveryModel


class TestComponentRecoveryActivity():

    @pytest.fixture
    def recovery_activity(self):
        return ComponentRecoveryModel.ConcreteRecoveryActivity('DummyActivity')

    def test_init(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        bool_list = []
        bool_list.append(recovery_activity.name == 'DummyActivity')
        bool_list.append(recovery_activity.level == 0.0)
        bool_list.append(recovery_activity.time_steps == [])
        bool_list.append(recovery_activity.demand_met == 1.0)
        bool_list.append(recovery_activity.demand == {})
        bool_list.append(recovery_activity.preceding_activities_finished == False)
        assert all(bool_list)

    def test_set_name(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        bool_list = [recovery_activity.name == 'DummyActivity']
        recovery_activity.set_name('AnotherDummyActivity')
        bool_list.append(recovery_activity.name == 'AnotherDummyActivity')
        assert all(bool_list)

    def test_set_level(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        bool_list = []
        bool_list.append(recovery_activity.level == 0.0)
        recovery_activity.set_level(0.4)
        bool_list.append(recovery_activity.level == 0.4)
        assert all(bool_list)

    def test_set_too_high_level(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        with pytest.raises(ValueError):
            recovery_activity.set_level(1.5)

    def test_set_negative_level(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        with pytest.raises(ValueError):
            recovery_activity.set_level(-1.5)

    def test_deterministic_sample_duration(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        distribution = {'Deterministic': {'Value': 5}}
        deterministic_sample = recovery_activity.sample_duration(distribution)
        assert math.isclose(deterministic_sample, 5)

    def test_lognormal_sample_duration(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        distribution = {'Lognormal': {'Median': 2, 'Dispersion': 1}}
        lognormal_samples = [recovery_activity.sample_duration(distribution) for _ in range(100000)]
        assert math.isclose(np.median(lognormal_samples), 2, abs_tol=0.05) and math.isclose(
            np.std(np.log(lognormal_samples)), 1, abs_tol=0.01)

    def test_set_deterministic_duration(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        distribution = {'Deterministic': {'Value': 5}}
        recovery_activity.set_duration(distribution)
        assert math.isclose(recovery_activity.duration, 5) and math.isclose(recovery_activity.rate, 1 / 5)

    def test_set_negative_duration(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        distribution = {'Deterministic': {'Value': -5}}
        with pytest.raises(ValueError):
            recovery_activity.set_duration(distribution)

    def test_set_empty_preceding_activities(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        preceding_activities = []
        recovery_activity.set_preceding_activities(preceding_activities)
        assert recovery_activity.preceding_activities == []

    def test_set_two_preceding_activities(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        preceding_activities = ['Activity 1', 'Acitivity 2']
        recovery_activity.set_preceding_activities(preceding_activities)
        assert recovery_activity.preceding_activities == ['Activity 1', 'Acitivity 2']

    def test_set_preceding_activities_twice(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        preceding_activities = ['Activity 1', 'Acitivity 2']
        recovery_activity.set_preceding_activities(preceding_activities)
        recovery_activity.set_preceding_activities(preceding_activities)
        assert recovery_activity.preceding_activities == ['Activity 1', 'Acitivity 2']

    def test_initial_preceding_activities_finished(self,
                                                   recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        assert recovery_activity.preceding_activities_finished == False

    def test_set_preceding_activities_finished(self,
                                               recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        recovery_activity.set_preceding_activities_finished(True)
        assert recovery_activity.preceding_activities_finished == True

    def test_set_demand(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        demand = [{'Resource': 'Resource 1', 'Amount': 5}, {'Resource': 'Resource 2', 'Amount': 3}]
        recovery_activity.set_demand(demand)
        assert all([recovery_activity.demand['Resource 1'].initial_amount == 5,
                    recovery_activity.demand['Resource 1'].current_amount == 5,
                    recovery_activity.demand['Resource 2'].initial_amount == 3,
                    recovery_activity.demand['Resource 2'].current_amount == 3])

    def test_set_demand_met(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        recovery_activity.set_demand_met(0.5)
        assert recovery_activity.demand_met == 0.5

    def test_set_invalid_demand_met(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        with pytest.raises(ValueError):
            recovery_activity.set_demand_met(-0.5)

    def test_get_demand(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        demand = [{'Resource': 'Resource 1', 'Amount': 5}, {'Resource': 'Resource 2', 'Amount': 3}]
        recovery_activity.set_demand(demand)
        demand = recovery_activity.get_demand()
        assert all([demand['Resource 1'].initial_amount == 5,
                    demand['Resource 1'].current_amount == 5,
                    demand['Resource 2'].initial_amount == 3,
                    demand['Resource 2'].current_amount == 3])

    def test_recover_without_set_duration(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        with pytest.raises(AttributeError):
            recovery_activity.recover(0)

    def test_recover_demand_not_met(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        recovery_activity.set_duration({'Deterministic': {'Value': 5}})
        recovery_activity.set_demand_met(0.0)
        recovery_activity.recover(0)
        assert recovery_activity.level == 0 and recovery_activity.time_steps == []

    def test_recover_full_demand_met(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        recovery_activity.set_duration({'Deterministic': {'Value': 5}})
        recovery_activity.set_demand_met(1.0)
        bool_list = []
        for time_step in range(3):
            recovery_activity.recover(time_step)
        bool_list.append(math.isclose(recovery_activity.level, 0.6))
        bool_list.append(recovery_activity.time_steps == [0, 1, 2])
        for time_step in range(3, 5):
            recovery_activity.recover(time_step)
        bool_list.append(recovery_activity.level == 1.0)
        bool_list.append(recovery_activity.time_steps == [0, 1, 2, 3, 4])
        for time_step in range(5, 10):
            recovery_activity.recover(time_step)
        bool_list.append(recovery_activity.level == 1.0)
        bool_list.append(recovery_activity.time_steps == [0, 1, 2, 3, 4])
        assert all(bool_list)

    def test_recover_partial_demand_met(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        recovery_activity.set_duration({'Deterministic': {'Value': 5}})
        recovery_activity.set_demand_met(0.5)
        bool_list = []
        for time_step in range(3):
            recovery_activity.recover(time_step)
        bool_list.append(math.isclose(recovery_activity.level, 0.3))
        bool_list.append(recovery_activity.time_steps == [0, 1, 2])
        for time_step in range(3, 5):
            recovery_activity.recover(time_step)
        bool_list.append(math.isclose(recovery_activity.level, 0.5))
        bool_list.append(recovery_activity.time_steps == [0, 1, 2, 3, 4])
        for time_step in range(5, 10):
            recovery_activity.recover(time_step)
        bool_list.append(math.isclose(recovery_activity.level, 1.0))
        bool_list.append(recovery_activity.time_steps == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        assert all(bool_list)

    def test_recover_with_negative_time_steps(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        recovery_activity.set_duration({'Deterministic': {'Value': 5}})
        with pytest.raises(ValueError):
            for time_step in range(-5, 0):
                recovery_activity.recover(time_step)

    def test_activity_finished_false(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        recovery_activity.set_duration({'Deterministic': {'Value': 5}})
        for time_step in range(4):
            recovery_activity.recover(time_step)
        assert recovery_activity.activity_finished() == False

    def test_activity_finished_false(self, recovery_activity: ComponentRecoveryModel.ConcreteRecoveryActivity):
        recovery_activity.set_duration({'Deterministic': {'Value': 5}})
        for time_step in range(5):
            recovery_activity.recover(time_step)
        assert recovery_activity.activity_finished() == True


class TestNoRecoveryActivityComponentRecoveryModel():

    @pytest.fixture()
    def recovery_model(self):
        return ComponentRecoveryModel.NoRecoveryActivity()

    def test_set_parameters(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters({})
        assert recovery_model.recovery_activities == {}

    def test_set_initial_damage_level(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_initial_damage_level(0.0)
        assert recovery_model.get_damage_level() == 0.0

    def test_set_nonzero_initial_damage_level(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        with pytest.raises(ValueError):
            recovery_model.set_initial_damage_level(0.5)

    def test_get_functionality_level(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        assert recovery_model.get_functionality_level() == 1.0

    def test_get_demand(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        assert recovery_model.get_demand() == {}


class TestSingleRecoveryActivityComponentRecoveryModel():
    recovery_model_parameters = {"Type": "SingleRecoveryActivity",
                                 "Parameters": {"Repair": {"Duration": {"Deterministic": {"Value": 10}},
                                                           "Demand": [{"Resource": "RepairCrew", "Amount": 10}], }},
                                 "DamageFunctionalityRelation": {"Type": "ReverseLinear"}}

    @pytest.fixture()
    def recovery_model(self):
        target_recovery_model = getattr(ComponentRecoveryModel,
                                        self.recovery_model_parameters['Type'])
        recovery_model = target_recovery_model()
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        return recovery_model

    def test_set_duration_parameters(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        assert math.isclose(recovery_model.recovery_activity.rate,
                            1 / self.recovery_model_parameters['Parameters']['Repair']['Duration']['Deterministic'][
                                'Value'])

    def test_set_demand_parameters(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        assert recovery_model.recovery_activity.demand['RepairCrew'].initial_amount == 10

    def test_set_parameters_wrong(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        temp_recovery_model_parameters = copy.deepcopy(self.recovery_model_parameters)
        temp_recovery_model_parameters['Parameters']['Repair']['Duration']['Deterministic']['Value'] = -0.1
        with pytest.raises(ValueError):
            recovery_model.set_parameters(temp_recovery_model_parameters['Parameters'])

    def test_set_damage_level(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        damage_level = 0.3
        recovery_model.set_initial_damage_level(damage_level)
        assert math.isclose(recovery_model.get_damage_level(), damage_level)

    def test_set_damage_level_error_negative(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        damage_level = -0.3
        with pytest.raises(ValueError):
            recovery_model.set_initial_damage_level(damage_level)

    def test_set_damage_level_error_above_one(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        damage_level = 1.3
        with pytest.raises(ValueError):
            recovery_model.set_initial_damage_level(damage_level)

    def test_set_damage_functionality(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_damage_functionality(self.recovery_model_parameters['DamageFunctionalityRelation'])
        damage_functionality_type = self.recovery_model_parameters['DamageFunctionalityRelation']['Type']
        assert isinstance(recovery_model.damage_to_functionality_relation, getattr(Relation, damage_functionality_type))

    def test_set_activities_demand_to_met(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_activities_demand_to_met()
        assert recovery_model.recovery_activity.demand_met == 1.0

    def test_get_demand_no_damage(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        demand = recovery_model.get_demand()
        assert demand == {}
    
    def test_get_demand_with_damage(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_initial_damage_level(0.1)
        demand = recovery_model.get_demand()
        assert demand['RepairCrew'].current_amount == 10 and demand['RepairCrew'].initial_amount == 10

    def test_get_functionality_level(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        damage_level = 0.4
        recovery_model.set_initial_damage_level(damage_level)
        recovery_model.set_damage_functionality(self.recovery_model_parameters['DamageFunctionalityRelation'])
        assert math.isclose(recovery_model.get_functionality_level(), 0.6)

    def test_get_damage_level(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        damage_level = 0.4
        recovery_model.set_initial_damage_level(damage_level)
        assert recovery_model.get_damage_level() == damage_level

    def test_recover_once(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        damage_level = 0.6
        recovery_model.set_initial_damage_level(damage_level)
        recovery_model.recover(0)
        assert math.isclose(recovery_model.get_damage_level(),
                            0.6 - 0.6 / 10) and recovery_model.recovery_activity.time_steps == [0]

    def test_recover_partially(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        damage_level = 0.6
        recovery_model.set_initial_damage_level(damage_level)
        for time_step in range(6):
            recovery_model.recover(time_step)
        assert math.isclose(recovery_model.get_damage_level(), 0.6 - 6 * 0.6 / 10,
                            abs_tol=1e-10) and recovery_model.recovery_activity.time_steps == list(range(6))

    def test_recover_fully(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        damage_level = 0.6
        recovery_model.set_initial_damage_level(damage_level)
        for time_step in range(10):
            recovery_model.recover(time_step)
        assert math.isclose(recovery_model.get_damage_level(), 0,
                            abs_tol=1e-10) and recovery_model.recovery_activity.time_steps == list(range(10))

    def test_recover_fully_partial_demand_met(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        damage_level = 0.6
        partial_demand_met = 0.1
        recovery_model.set_initial_damage_level(damage_level)
        recovery_model.recovery_activity.demand_met = partial_demand_met
        for time_step in range(100):
            recovery_model.recover(time_step)
        assert math.isclose(recovery_model.get_damage_level(), 0,
                            abs_tol=1e-10) and recovery_model.recovery_activity.time_steps == list(range(100))

    def test_recover_partially_partial_demand_met(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        damage_level = 0.6
        partial_demand_met = 0.1
        recovery_model.set_initial_damage_level(damage_level)
        recovery_model.recovery_activity.demand_met = partial_demand_met
        for time_step in range(10):
            recovery_model.recover(time_step)
        assert math.isclose(recovery_model.get_damage_level(), 0.6 * 0.9,
                            abs_tol=1e-10) and recovery_model.recovery_activity.time_steps == list(range(10))

    def test_recover_fully_full_damage(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        damage_level = 1.0
        recovery_model.set_initial_damage_level(damage_level)
        for time_step in range(10):
            recovery_model.recover(time_step)
        assert math.isclose(recovery_model.get_damage_level(), 0,
                            abs_tol=1e-10) and recovery_model.recovery_activity.time_steps == list(range(10))

    def test_overrecover(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        damage_level = 0.6
        recovery_model.set_initial_damage_level(damage_level)
        for time_step in range(20):
            recovery_model.recover(time_step)
        assert math.isclose(recovery_model.get_damage_level(), 0,
                            abs_tol=1e-10) and recovery_model.recovery_activity.time_steps == list(range(10))

    def test_set_unmet_demand_for_recovery_activities(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_unmet_demand_for_recovery_activities('RepairCrew', 0.5)
        assert recovery_model.recovery_activity.demand_met == 0.5

    def test_set_wrong_unmet_demand_for_recovery_activities(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        with pytest.raises(ValueError):
            recovery_model.set_unmet_demand_for_recovery_activities('Inspectors', 0.5)


class TestMultipleRecoveryActivitiesComponentRecoveryModel:
    recovery_model_parameters = {"Type": "MultipleRecoveryActivities",
                                 "Parameters": {
                                     "RapidInspection": {
                                         "Duration": {"Lognormal": {"Median": 1, "Dispersion": 0.0}},
                                         "Demand": [{"Resource": "FirstResponderEngineer", "Amount": 0.1}],
                                         "PrecedingActivities": []
                                     },
                                     "ContractorMobilization": {
                                         "Duration": {"Lognormal": {"Median": 1, "Dispersion": 0.0}},
                                         "Demand": [{"Resource": "Contractor", "Amount": 1}],
                                         "PrecedingActivities": ["RapidInspection"]
                                     },
                                     "Repair": {
                                         "Duration": {"Lognormal": {"Median": 10, "Dispersion": 0.0}},
                                         "Demand": [{"Resource": "RepairCrew", "Amount": 10}],
                                         "PrecedingActivities": ["RapidInspection", "ContractorMobilization"]
                                     }
                                 },
                                 "DamageFunctionalityRelation": {
                                     "Type": "ReverseLinear"
                                 }
                                 }

    @pytest.fixture
    def recovery_model(self):
        target_recovery_model = getattr(ComponentRecoveryModel, self.recovery_model_parameters['Type'])
        return target_recovery_model()

    def test_set_init(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        assert recovery_model.recovery_activities == {}

    def test_set_parameters(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        bool_list = []
        for recovery_activity_name, recovery_activity_parameters in self.recovery_model_parameters[
            'Parameters'].items():
            bool_list.append(recovery_activity_name in recovery_model.recovery_activities)
            bool_list.append(
                type(recovery_model.recovery_activities[recovery_activity_name]).__name__ == 'ConcreteRecoveryActivity')
            bool_list.append(recovery_model.recovery_activities[recovery_activity_name].preceding_activities ==
                             recovery_activity_parameters['PrecedingActivities'])
            bool_list.append(recovery_model.recovery_activities[recovery_activity_name].level == 1)
            bool_list.append(math.isclose(recovery_model.recovery_activities[recovery_activity_name].duration,
                                          recovery_activity_parameters['Duration']['Lognormal']['Median']))
            bool_list.append(math.isclose(recovery_model.recovery_activities[recovery_activity_name].rate,
                                          1 / recovery_activity_parameters['Duration']['Lognormal']['Median']))
            bool_list.append(recovery_model.recovery_activities[recovery_activity_name].demand[
                                 recovery_activity_parameters['Demand'][0]['Resource']].initial_amount ==
                             recovery_activity_parameters['Demand'][0]['Amount'])

        assert all(bool_list)

    def test_set_initial_damage_level(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        damage_level = 1.0
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        recovery_model.set_initial_damage_level(damage_level)
        bool_list = []
        for recovery_activity_name, recovery_activity in recovery_model.recovery_activities.items():
            if recovery_activity_name == recovery_model.REPAIR_ACTIVITY_NAME:
                bool_list.append(recovery_activity.level == 1 - damage_level)
            else:
                bool_list.append(recovery_activity.level == 0.0)

    def test_set_wrong_initial_damage_level(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        with pytest.raises(ValueError):
            recovery_model.set_initial_damage_level(1.5)

    def test_set_damage_functionality(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_damage_functionality(self.recovery_model_parameters['DamageFunctionalityRelation'])
        damage_functionality_type = self.recovery_model_parameters['DamageFunctionalityRelation']['Type']
        assert isinstance(recovery_model.damage_to_functionality_relation, getattr(Relation, damage_functionality_type))

    def test_preceding_activities_finished(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        bool_list = []
        for recovery_activity in recovery_model.recovery_activities.values():
            bool_list.append(recovery_model.preceding_activities_finished(recovery_activity) == True)

        recovery_model.set_initial_damage_level(1.0)
        target_bools = [True, False, False]
        for target_bool, recovery_activity in zip(target_bools, recovery_model.recovery_activities.values()):
            bool_list.append(recovery_model.preceding_activities_finished(recovery_activity) == target_bool)

        recovery_model.recovery_activities['RapidInspection'].level = 1.0
        target_bools = [True, True, False]
        for target_bool, recovery_activity in zip(target_bools, recovery_model.recovery_activities.values()):
            bool_list.append(recovery_model.preceding_activities_finished(recovery_activity) == target_bool)

        assert all(bool_list)

    def test_check_preceding_activities(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        recovery_model.check_preceding_activities()
        bool_list = []
        target_bools = [True, True, True]
        for target_bool, recovery_activity in zip(target_bools, recovery_model.recovery_activities.values()):
            bool_list.append(recovery_activity.preceding_activities_finished == target_bool)

        recovery_model.set_initial_damage_level(0.5)
        recovery_model.check_preceding_activities()
        target_bools = [True, False, False]
        for target_bool, recovery_activity in zip(target_bools, recovery_model.recovery_activities.values()):
            bool_list.append(recovery_activity.preceding_activities_finished == target_bool)

        recovery_model.recovery_activities['RapidInspection'].level = 1.0
        recovery_model.check_preceding_activities()
        target_bools = [True, True, False]
        for target_bool, recovery_activity in zip(target_bools, recovery_model.recovery_activities.values()):
            bool_list.append(recovery_activity.preceding_activities_finished == target_bool)

        assert all(bool_list)

    def test_get_damage_level(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        bool_list = []
        bool_list.append(recovery_model.get_damage_level() == 0.0)
        recovery_model.set_initial_damage_level(1.0)
        bool_list.append(recovery_model.get_damage_level() == 1.0)
        recovery_model.set_initial_damage_level(0.6)
        bool_list.append(recovery_model.get_damage_level() == 0.6)
        assert all(bool_list)

    def test_get_functionality_level(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        recovery_model.set_damage_functionality(self.recovery_model_parameters['DamageFunctionalityRelation'])
        bool_list = []
        bool_list.append(recovery_model.get_functionality_level() == 1.0)
        recovery_model.set_initial_damage_level(1.0)
        bool_list.append(recovery_model.get_functionality_level() == 0.0)
        recovery_model.set_initial_damage_level(0.6)
        bool_list.append(recovery_model.get_functionality_level() == 0.4)
        assert all(bool_list)

    def test_get_demand(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        bool_list = []
        bool_list.append(recovery_model.get_demand() == {})

        recovery_model.set_initial_damage_level(0.1)
        current_demand = recovery_model.get_demand()
        bool_list.append(len(current_demand) == 1)
        bool_list.append(current_demand['FirstResponderEngineer'].initial_amount == 0.1)
        bool_list.append(current_demand['FirstResponderEngineer'].current_amount == 0.1)

        recovery_model.recovery_activities['RapidInspection'].level = 1.0
        current_demand = recovery_model.get_demand()
        bool_list.append(len(current_demand) == 1)
        bool_list.append(current_demand['Contractor'].initial_amount == 1)
        bool_list.append(current_demand['Contractor'].current_amount == 1)

        recovery_model.recovery_activities['ContractorMobilization'].level = 1.0
        current_demand = recovery_model.get_demand()
        bool_list.append(len(current_demand) == 1)
        bool_list.append(current_demand['RepairCrew'].initial_amount == 10)
        bool_list.append(current_demand['RepairCrew'].current_amount == 10)

        recovery_model.recovery_activities['Repair'].level = 1.0
        bool_list.append(recovery_model.get_demand() == {})

        assert all(bool_list)

    def test_set_activities_demand_to_met(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        bool_list = []
        bool_list.append(all([recovery_activity.demand_met == 1.0 for recovery_activity in
                              recovery_model.recovery_activities.values()]))
        recovery_model.recovery_activities['RapidInspection'].demand_met = 0.3
        recovery_model.set_activities_demand_to_met()
        bool_list.append(all([recovery_activity.demand_met == 1.0 for recovery_activity in
                              recovery_model.recovery_activities.values()]))
        assert all(bool_list)

    def test_set_unmet_demand_for_recovery_activities(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        bool_list = []
        bool_list.append(all([recovery_activity.demand_met == 1.0 for recovery_activity in
                              recovery_model.recovery_activities.values()]))
        recovery_model.set_unmet_demand_for_recovery_activities('FirstResponderEngineer', 0.5)
        bool_list.append(recovery_model.recovery_activities['RapidInspection'].demand_met == 0.5)
        bool_list.append(recovery_model.recovery_activities['ContractorMobilization'].demand_met == 1.0)
        bool_list.append(recovery_model.recovery_activities['Repair'].demand_met == 1.0)
        recovery_model.set_unmet_demand_for_recovery_activities('Contractor', 0.6)
        bool_list.append(recovery_model.recovery_activities['ContractorMobilization'].demand_met == 0.6)
        recovery_model.set_unmet_demand_for_recovery_activities('RepairCrew', 0.4)
        bool_list.append(recovery_model.recovery_activities['Repair'].demand_met == 0.4)
        assert all(bool_list)

    def test_find_recovery_activity_that_demands_the_resource(self,
                                                              recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        bool_list = []
        recovery_activity = recovery_model.find_recovery_activity_that_demands_the_resource('Contractor')
        bool_list.append(recovery_activity.name == 'ContractorMobilization')
        recovery_activity = recovery_model.find_recovery_activity_that_demands_the_resource('RepairCrew')
        bool_list.append(recovery_activity.name == 'Repair')
        assert all(bool_list)

    def test_recover_no_damage(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        recovery_model.set_damage_functionality(self.recovery_model_parameters['DamageFunctionalityRelation'])
        bool_list = []
        for time_step in range(10):
            recovery_model.recover(time_step)
        bool_list.append(recovery_model.recovery_activities['RapidInspection'].time_steps == [])
        bool_list.append(recovery_model.recovery_activities['ContractorMobilization'].time_steps == [])
        bool_list.append(recovery_model.recovery_activities['Repair'].time_steps == [])
        bool_list.append(recovery_model.recovery_activities['RapidInspection'].level == 1.0)
        bool_list.append(recovery_model.recovery_activities['ContractorMobilization'].level == 1.0)
        bool_list.append(recovery_model.recovery_activities['Repair'].level == 1.0)
        assert all(bool_list)

    def test_recover_once(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        recovery_model.set_damage_functionality(self.recovery_model_parameters['DamageFunctionalityRelation'])
        recovery_model.set_initial_damage_level(0.01)
        bool_list = []
        for time_step in range(1):
            recovery_model.recover(time_step)
        bool_list.append(recovery_model.recovery_activities['RapidInspection'].time_steps == [0])
        bool_list.append(recovery_model.recovery_activities['ContractorMobilization'].time_steps == [])
        bool_list.append(recovery_model.recovery_activities['Repair'].time_steps == [])
        bool_list.append(recovery_model.recovery_activities['RapidInspection'].level == 1.0)
        bool_list.append(recovery_model.recovery_activities['ContractorMobilization'].level == 0.0)
        bool_list.append(recovery_model.recovery_activities['Repair'].level == 0.99)
        assert all(bool_list)

    def test_recover_partially(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        recovery_model.set_damage_functionality(self.recovery_model_parameters['DamageFunctionalityRelation'])
        recovery_model.set_initial_damage_level(1.0)
        bool_list = []
        for time_step in range(5):
            recovery_model.recover(time_step)
        bool_list.append(recovery_model.recovery_activities['RapidInspection'].time_steps == [0])
        bool_list.append(recovery_model.recovery_activities['ContractorMobilization'].time_steps == [1])
        bool_list.append(recovery_model.recovery_activities['Repair'].time_steps == [2, 3, 4])
        bool_list.append(recovery_model.recovery_activities['RapidInspection'].level == 1.0)
        bool_list.append(recovery_model.recovery_activities['ContractorMobilization'].level == 1.0)
        bool_list.append(math.isclose(recovery_model.recovery_activities['Repair'].level, 0.3))
        assert all(bool_list)

    def test_recover_full(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        recovery_model.set_damage_functionality(self.recovery_model_parameters['DamageFunctionalityRelation'])
        recovery_model.set_initial_damage_level(1.0)
        bool_list = []
        for time_step in range(12):
            recovery_model.recover(time_step)
        bool_list.append(recovery_model.recovery_activities['RapidInspection'].time_steps == [0])
        bool_list.append(recovery_model.recovery_activities['ContractorMobilization'].time_steps == [1])
        bool_list.append(recovery_model.recovery_activities['Repair'].time_steps == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        bool_list.append(recovery_model.recovery_activities['RapidInspection'].level == 1.0)
        bool_list.append(recovery_model.recovery_activities['ContractorMobilization'].level == 1.0)
        bool_list.append(math.isclose(recovery_model.recovery_activities['Repair'].level, 1.0))
        assert all(bool_list)

    def test_recover_partial_demand_met(self, recovery_model: ComponentRecoveryModel.RecoveryModel):
        recovery_model.set_parameters(self.recovery_model_parameters['Parameters'])
        recovery_model.set_damage_functionality(self.recovery_model_parameters['DamageFunctionalityRelation'])
        recovery_model.set_initial_damage_level(1.0)
        recovery_model.recovery_activities['ContractorMobilization'].demand_met = 0.5
        bool_list = []
        for time_step in range(13):
            recovery_model.recover(time_step)
        bool_list.append(recovery_model.recovery_activities['RapidInspection'].time_steps == [0])
        bool_list.append(recovery_model.recovery_activities['ContractorMobilization'].time_steps == [1, 2])
        bool_list.append(recovery_model.recovery_activities['Repair'].time_steps == [3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        bool_list.append(recovery_model.recovery_activities['RapidInspection'].level == 1.0)
        bool_list.append(recovery_model.recovery_activities['ContractorMobilization'].level == 1.0)
        bool_list.append(math.isclose(recovery_model.recovery_activities['Repair'].level, 1.0))
        assert all(bool_list)
