import pytest
import math
import copy
import pandas as pd
import numpy as np
import random
from pyrecodes_hospitals import SystemCreator
from pyrecodes_hospitals import ComponentLibraryCreator
from pyrecodes_hospitals import ComponentRecoveryModel
from pyrecodes_hospitals import Relation
from pyrecodes_hospitals import System
from pyrecodes_hospitals import Component
from pyrecodes_hospitals import Patient
from pyrecodes_hospitals import main

random.seed(1)

class TestHospitalComponent():

    RESOURCE_DYNAMICS = [{'Resource': 'Resource_1', 'SupplyOrDemand': 'supply', 'SupplyOrDemandType': 'Supply', 'AtTimeStep': [0, 2, 5, 10], 'Amount': [50, 30, 10, 20]},
                         {'Resource': 'Resource_2', 'SupplyOrDemand': 'demand', 'SupplyOrDemandType': 'OperationDemand', 'AtTimeStep': [0, 1, 2, 5], 'Amount': [10, 5, 15, 0]}]
    
    COMPONENT_PARAMETERS = {'ComponentClass': 'HospitalComponent',
                            'RecoveryModel': {'Type': 'NoRecoveryActivity',
                                              'Parameters': {},
                                              'DamageFunctionalityRelation': {'Type': 'Constant'}},
                            'Supply': {'Resource_1': {'Amount': 50, 'ResourceClassName': 'ConsumableResource', 'FunctionalityToAmountRelation': 'Constant', 'UnmetDemandToAmountRelation': {'Resource_1': 'Linear'}},},
                            'OperationDemand': {'Resource_1': {'Amount': 0, 'ResourceClassName': 'ConcreteResource', 'FunctionalityToAmountRelation': 'Constant'},
                                                'Resource_2': {'Amount': 10, 'ResourceClassName': 'ConcreteResource', 'FunctionalityToAmountRelation': 'Constant'},
                                                'Resource_3': {'Amount': 0, 'ResourceClassName': 'ConcreteResource', 'FunctionalityToAmountRelation': 'Constant'},
                                                'Resource_4': {'Amount': 0, 'ResourceClassName': 'ConcreteResource', 'FunctionalityToAmountRelation': 'Constant'},
                                                'Resource_5': {'Amount': 0, 'ResourceClassName': 'ConcreteResource', 'FunctionalityToAmountRelation': 'Constant'}}
    }

    PATIENT_PARAMETERS_SIMPLE = [{'Department_1': {'MaximalLengthOfStay': 10,
                                                   'BaselineLengthOfStay': 8, 
                                                   'BaselineMortalityRate': 0.01,
                                                   'ResourcesRequired': 
                                                       [{'ResourceName': 'Resource_1', 'ResourceAmount': 10, 'ConsequencesOfUnmetDemand': [{'MortalityRateIncrease': 1.2}]},
                                                       {'ResourceName': 'Resource_2', 'ResourceAmount': 5, 'ConsequencesOfUnmetDemand': [{'Death': ''}]},
                                                       {'ResourceName': 'Resource_3', 'ResourceAmount': 5, 'ConsequencesOfUnmetDemand': [{'LengthOfStayExtended': 1.5}]}]}},
                                {'Department_2': {'MaximalLengthOfStay': 5,
                                                   'BaselineLengthOfStay': 5, 
                                                   'BaselineMortalityRate': 0.0,
                                                   'ResourcesRequired': 
                                                       [{'ResourceName': 'Resource_4', 'ResourceAmount': 1, 'ConsequencesOfUnmetDemand': [{'MortalityRateIncrease': 1.1}]},
                                                       {'ResourceName': 'Resource_5', 'ResourceAmount': 5, 'ConsequencesOfUnmetDemand': [{'Death': ''}]}]}}]


    def test_init(self):
        component = Component.HospitalComponent()
        assert component.functionality_level == 1.0
        assert component.functional == []
        assert component.supply['Supply'] == {}
        assert component.demand['OperationDemand'] == {}
        assert component.demand['RecoveryDemand'] == {}
        assert component.patients == []
        assert component.predefined_resource_dynamics == []

    def test_set_predefined_resource_dynamics(self):
        component = Component.HospitalComponent()
        component.set_predefined_resource_dynamics(self.RESOURCE_DYNAMICS)  
        assert component.predefined_resource_dynamics == self.RESOURCE_DYNAMICS
    
    def test_update(self):
        component = Component.HospitalComponent()
        component.form('Department_1', self.COMPONENT_PARAMETERS)
        component.set_predefined_resource_dynamics(self.RESOURCE_DYNAMICS)
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient', self.PATIENT_PARAMETERS_SIMPLE)
        component.patients += [copy.deepcopy(patient) for _ in range(10)]
        system_consumption = {'Resource_1': [10]}
        component.update(0, system_consumption)
        assert component.supply['Supply']['Resource_1'].current_amount == 90
        assert component.demand['OperationDemand']['Resource_1'].current_amount == 100
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 70
        assert component.demand['OperationDemand']['Resource_3'].current_amount == 50

        for patient in component.patients[:5]:
            patient.move_to_next_department()
        
        component.update(1, system_consumption)
        assert component.supply['Supply']['Resource_1'].current_amount == 80
        assert component.demand['OperationDemand']['Resource_1'].current_amount == 50
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 50
        assert component.demand['OperationDemand']['Resource_3'].current_amount == 25
        assert component.demand['OperationDemand']['Resource_4'].current_amount == 5
        assert component.demand['OperationDemand']['Resource_5'].current_amount == 25

        system_consumption = {'Resource_1': [20]}
        component.update(2, system_consumption) 
        assert component.supply['Supply']['Resource_1'].current_amount == 90
        assert component.demand['OperationDemand']['Resource_1'].current_amount == 50
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 65
        assert component.demand['OperationDemand']['Resource_3'].current_amount == 25
        assert component.demand['OperationDemand']['Resource_4'].current_amount == 5
        assert component.demand['OperationDemand']['Resource_5'].current_amount == 25

        system_consumption = {'Resource_1': [5]}
        component.update(3, system_consumption) 
        assert component.supply['Supply']['Resource_1'].current_amount == 85
        assert component.demand['OperationDemand']['Resource_1'].current_amount == 50
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 65
        assert component.demand['OperationDemand']['Resource_3'].current_amount == 25
        assert component.demand['OperationDemand']['Resource_4'].current_amount == 5
        assert component.demand['OperationDemand']['Resource_5'].current_amount == 25

    def test_update_resources_based_on_predefined_resource_dynamics(self):
        component = Component.HospitalComponent()
        component.form('ExampleComponent', self.COMPONENT_PARAMETERS)
        component.set_predefined_resource_dynamics(self.RESOURCE_DYNAMICS)
        component.update_resources_based_on_predefined_resource_dynamics(0)
        assert component.supply['Supply']['Resource_1'].current_amount == 50 + 50
        assert component.supply['Supply']['Resource_1'].initial_amount == 50 + 50
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 10 + 10
        assert component.demand['OperationDemand']['Resource_2'].initial_amount == 10 + 10
        component.update_resources_based_on_predefined_resource_dynamics(1)
        assert component.supply['Supply']['Resource_1'].current_amount == 50 + 50
        assert component.supply['Supply']['Resource_1'].initial_amount == 50 + 50
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 5 + 20
        assert component.demand['OperationDemand']['Resource_2'].initial_amount == 5 + 20
        component.update_resources_based_on_predefined_resource_dynamics(2)
        assert component.supply['Supply']['Resource_1'].current_amount == 30 + 100
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 15 + 25
        component.update_resources_based_on_predefined_resource_dynamics(3)
        assert component.supply['Supply']['Resource_1'].current_amount == 30 + 100
        assert component.supply['Supply']['Resource_1'].initial_amount == 30 + 100
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 15 + 25
        assert component.demand['OperationDemand']['Resource_2'].initial_amount == 15 + 25
        component.update_resources_based_on_predefined_resource_dynamics(5)
        assert component.supply['Supply']['Resource_1'].current_amount == 10 + 130
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 0 + 40
        component.update_resources_based_on_predefined_resource_dynamics(10)
        assert component.supply['Supply']['Resource_1'].current_amount == 20 + 140
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 0 + 40
        component.update_resources_based_on_predefined_resource_dynamics(11)
        assert component.supply['Supply']['Resource_1'].current_amount == 20 + 140
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 0 + 40

    def test_get_resource_amount_based_on_time_step(self):
        component = Component.HospitalComponent()
        component.form('ExampleComponent', self.COMPONENT_PARAMETERS)
        component.set_predefined_resource_dynamics(self.RESOURCE_DYNAMICS)
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[0], 0) == 50 + 50
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[0], 1) == None
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[0], 2) == 30 + 50
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[0], 3) == None
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[0], 4) == None
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[0], 5) == 10 + 50
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[0], 6) == None
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[0], 7) == None
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[0], 8) == None
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[0], 9) == None
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[0], 10) == 20 + 50
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[0], 11) == None
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[0], 12) == None

        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[1], 0) == 10 + 10
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[1], 1) == 5 + 10
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[1], 2) == 15 + 10
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[1], 3) == None
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[1], 4) == None
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[1], 5) == 0 + 10
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[1], 6) == None
        assert component.get_resource_amount_based_on_time_step(self.RESOURCE_DYNAMICS[1], 7) == None
    
    def test_update_supply_based_on_consumption(self):
        component = Component.HospitalComponent()
        system_consumption = {'Resource_1': [10]}
        component.form('ExampleComponent', self.COMPONENT_PARAMETERS)
        assert component.supply['Supply']['Resource_1'].current_amount == 50
        component.update_supply_based_on_consumption(system_consumption)
        assert component.supply['Supply']['Resource_1'].current_amount == 40
        system_consumption = {'Resource_1': [10, 5]}
        component.update_supply_based_on_consumption(system_consumption)
        assert component.supply['Supply']['Resource_1'].current_amount == 35
        system_consumption = {'Resource_1': [10, 5, 20]}
        component.update_supply_based_on_consumption(system_consumption)
        assert component.supply['Supply']['Resource_1'].current_amount == 15

    def test_update_operation_demand_based_on_patients(self):
        component = Component.HospitalComponent()
        component.form('ExampleComponent', self.COMPONENT_PARAMETERS)
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient', self.PATIENT_PARAMETERS_SIMPLE)
        component.patients.append(copy.deepcopy(patient))
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 10
        component.update_operation_demand_based_on_patients()
        assert component.demand['OperationDemand']['Resource_1'].current_amount == 10
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 15
        assert component.demand['OperationDemand']['Resource_3'].current_amount == 5
        component.patients.append(copy.deepcopy(patient))
        component.update_operation_demand_based_on_patients()
        assert component.demand['OperationDemand']['Resource_1'].current_amount == 20
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 20
        assert component.demand['OperationDemand']['Resource_3'].current_amount == 10
        component.patients[0].move_to_next_department()
        component.update_operation_demand_based_on_patients()
        assert component.demand['OperationDemand']['Resource_1'].current_amount == 10
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 15
        assert component.demand['OperationDemand']['Resource_3'].current_amount == 5
        assert component.demand['OperationDemand']['Resource_4'].current_amount == 1
        assert component.demand['OperationDemand']['Resource_5'].current_amount == 5
    
    def test_set_current_operation_demand(self):
        component = Component.HospitalComponent()
        component.form('ExampleComponent', self.COMPONENT_PARAMETERS)
        operation_demand = {'Resource_1': 5}
        component.set_current_operation_demand(operation_demand)
        assert component.demand['OperationDemand']['Resource_1'].current_amount == 5
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 10
        assert len(component.demand['OperationDemand']) == 5

        operation_demand = {'Resource_1': 10, 'Resource_2': 5}
        component.set_current_operation_demand(operation_demand)
        assert component.demand['OperationDemand']['Resource_1'].current_amount == 10
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 15

        operation_demand = {'Resource_2': 5, 'Resource_3': 5}
        component.set_current_operation_demand(operation_demand)
        assert component.demand['OperationDemand']['Resource_1'].current_amount == 0
        assert component.demand['OperationDemand']['Resource_2'].current_amount == 15
        assert component.demand['OperationDemand']['Resource_3'].current_amount == 5
        assert component.demand['OperationDemand']['Resource_4'].current_amount == 0
        assert component.demand['OperationDemand']['Resource_5'].current_amount == 0

        operation_demand = {'Resource_6': 10}
        with pytest.raises(ValueError):
            component.set_current_operation_demand(operation_demand)

    def test_update_supply_based_on_unmet_demand(self):
        component = Component.HospitalComponent()
        component.form('ExampleComponent', self.COMPONENT_PARAMETERS)
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient', self.PATIENT_PARAMETERS_SIMPLE)
        component.patients += [copy.deepcopy(patient) for _ in range(10)]
        component.update_supply_based_on_unmet_demand('Resource_1', 0.0)
        assert component.supply['Supply']['Resource_1'].current_amount == 0.0
        for patient in component.patients:
            assert patient.demand_met[0]['Resource_1'] == 0.0
            assert patient.demand_met[0]['Resource_2'] == 1.0
            assert patient.demand_met[0]['Resource_3'] == 1.0
        
        component.supply['Supply']['Resource_1'].current_amount = 50
        component.update(0, {'Resource_1': [0]})
        for patient in component.patients:
            patient.set_all_demand_as_met()
        component.update_supply_based_on_unmet_demand('Resource_2', 0.0)
        assert component.supply['Supply']['Resource_1'].current_amount == 50.0
        for patient in component.patients:
            assert patient.demand_met[0]['Resource_1'] == 1.0
            assert patient.demand_met[0]['Resource_2'] == 0.0
            assert patient.demand_met[0]['Resource_3'] == 1.0

        for patient in component.patients:
            patient.set_all_demand_as_met()
        component.supply['Supply']['Resource_1'].current_amount = 50
        component.update(0, {'Resource_1': [0]})
        component.update_supply_based_on_unmet_demand('Resource_1', 0.5)
        assert component.supply['Supply']['Resource_1'].current_amount == 25.0
        for i, patient in enumerate(component.patients):
            if i < 5:
                assert patient.demand_met[0]['Resource_1'] == 1.0
            else:
                assert patient.demand_met[0]['Resource_1'] == 0.0
        
        component.supply['Supply']['Resource_1'].current_amount = 50
        component.update(0, {'Resource_1': [0]})
        for patient in component.patients:
            patient.set_all_demand_as_met()
        component.update_supply_based_on_unmet_demand('Resource_2', 0.8)
        assert component.supply['Supply']['Resource_1'].current_amount == 50
        for i, patient in enumerate(component.patients):
            if i < 8:
                assert patient.demand_met[0]['Resource_2'] == 1.0
            else:
                assert patient.demand_met[0]['Resource_2'] == 0.0
        
        component.supply['Supply']['Resource_1'].current_amount = 50
        component.update(0, {'Resource_1': [0]})
        for patient in component.patients:
            patient.set_all_demand_as_met()
        component.update_supply_based_on_unmet_demand('Resource_3', 1.0)
        assert component.supply['Supply']['Resource_1'].current_amount == 50
        for i, patient in enumerate(component.patients):
            assert patient.demand_met[0]['Resource_3'] == 1.0
        
        for patient in component.patients:
            patient.move_to_next_department()
        component.supply['Supply']['Resource_1'].current_amount = 50
        component.update(0, {'Resource_1': [0]})
        for patient in component.patients:
            patient.set_all_demand_as_met()
        component.update_supply_based_on_unmet_demand('Resource_4', 0.0)
        assert component.supply['Supply']['Resource_1'].current_amount == 50.0
        for patient in component.patients:
            assert patient.demand_met[1]['Resource_4'] == 0.0
            assert patient.demand_met[1]['Resource_5'] == 1.0
        
        component.supply['Supply']['Resource_1'].current_amount = 50
        component.update(0, {'Resource_1': [0]})
        for patient in component.patients:
            patient.set_all_demand_as_met()
        component.update_supply_based_on_unmet_demand('Resource_5', 0.4)
        assert component.supply['Supply']['Resource_1'].current_amount == 50.0
        for i, patient in enumerate(component.patients):
            if i < 4:
                assert patient.demand_met[1]['Resource_5'] == 1.0
            else:
                assert patient.demand_met[1]['Resource_5'] == 0.0
    
    def test_update_patients_based_on_unmet_demand(self):
        component = Component.HospitalComponent()
        component.form('ExampleComponent', self.COMPONENT_PARAMETERS)
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient', self.PATIENT_PARAMETERS_SIMPLE)
        component.patients += [copy.deepcopy(patient) for _ in range(10)]

        component.update_patients_based_on_unmet_demand('Resource_1', 1.0)
        for patient in component.patients:
            assert patient.demand_met[0]['Resource_1'] == 1.0

        component.update_patients_based_on_unmet_demand('Resource_1', 0.5)
        for i, patient in enumerate(component.patients):
            if i < 5:
                assert patient.demand_met[0]['Resource_1'] == 1.0
            else:
                assert patient.demand_met[0]['Resource_1'] == 0.0

        component.update_patients_based_on_unmet_demand('Resource_1', 0.0)
        for patient in component.patients:
            assert patient.demand_met[0]['Resource_1'] == 0.0

    def test_distribute_resource_among_patients_priority(self):
        component = Component.HospitalComponent()
        component.form('ExampleComponent', self.COMPONENT_PARAMETERS)
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient Red', self.PATIENT_PARAMETERS_SIMPLE)
        component.patients += [copy.deepcopy(patient) for _ in range(5)]
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient Yellow', self.PATIENT_PARAMETERS_SIMPLE)
        component.patients += [copy.deepcopy(patient) for _ in range(10)]
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient Green', self.PATIENT_PARAMETERS_SIMPLE)
        component.patients += [copy.deepcopy(patient) for _ in range(5)]
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient Inpatient', self.PATIENT_PARAMETERS_SIMPLE)
        component.patients += [copy.deepcopy(patient) for _ in range(5)]

        patients_with_demand = component.get_patients_with_demand('Resource_2')
        component.distribute_resource_among_patients_priority('Resource_2', 1.0, patients_with_demand)
        for patient in patients_with_demand:
            assert patient.demand_met[0]['Resource_2'] == 1.0
        
        component.distribute_resource_among_patients_priority('Resource_2', 0.5, patients_with_demand)
        yellow_count = 1
        for patient in patients_with_demand:
            if 'Red' in patient.name:
                assert patient.demand_met[0]['Resource_2'] == 1.0
            elif 'Yellow' in patient.name and yellow_count <= 7:
                assert patient.demand_met[0]['Resource_2'] == 1.0
                yellow_count += 1
            elif 'Green' in patient.name:
                assert patient.demand_met[0]['Resource_2'] == 0.0
            elif 'Inpatient' in patient.name:
                assert patient.demand_met[0]['Resource_2'] == 0.0

        component.distribute_resource_among_patients_priority('Resource_2', 0.2, patients_with_demand)
        yellow_count = 1
        for patient in patients_with_demand:
            if 'Red' in patient.name:
                assert patient.demand_met[0]['Resource_2'] == 1.0
            else:
                assert patient.demand_met[0]['Resource_2'] == 0.0
        
        component.distribute_resource_among_patients_priority('Resource_2', 0.0, patients_with_demand)
        for patient in patients_with_demand:
            assert patient.demand_met[0]['Resource_2'] == 0.0 

    def test_prioritize_patients(self):
        component = Component.HospitalComponent()
        component.form('ExampleComponent', self.COMPONENT_PARAMETERS)
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient Red', self.PATIENT_PARAMETERS_SIMPLE)
        component.patients += [copy.deepcopy(patient) for _ in range(5)]
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient Yellow', self.PATIENT_PARAMETERS_SIMPLE)
        component.patients += [copy.deepcopy(patient) for _ in range(10)]
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient Green', self.PATIENT_PARAMETERS_SIMPLE)
        component.patients += [copy.deepcopy(patient) for _ in range(5)]
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient Else', self.PATIENT_PARAMETERS_SIMPLE)
        component.patients += [copy.deepcopy(patient) for _ in range(5)]
        
        prioritized_patients = component.prioritize_patients(component.patients)
        assert all([patient.name == 'ExamplePatient Red' for patient in prioritized_patients[:5]])
        assert all([patient.name == 'ExamplePatient Yellow' for patient in prioritized_patients[5:15]])
        assert all([patient.name == 'ExamplePatient Green' for patient in prioritized_patients[15:20]])
        assert all([patient.name == 'ExamplePatient Else' for patient in prioritized_patients[20:25]])
        
        component.PRIORITIZED_PATIENTS_LIST = ['Else', 'Green', 'Rest']
        prioritized_patients = component.prioritize_patients(component.patients)
        assert all([patient.name == 'ExamplePatient Else' for patient in prioritized_patients[:5]])
        assert all([patient.name == 'ExamplePatient Green' for patient in prioritized_patients[5:10]])

    def test_distribute_resource_among_patients_evenly(self):
        component = Component.HospitalComponent()
        component.form('ExampleComponent', self.COMPONENT_PARAMETERS)
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient', self.PATIENT_PARAMETERS_SIMPLE)
        component.patients += [copy.deepcopy(patient) for _ in range(10)]
        patients_with_demand = component.get_patients_with_demand('Resource_2')
        component.distribute_resource_among_patients_evenly('Resource_2', 1.0, patients_with_demand)
        for patient in patients_with_demand:
            assert patient.demand_met[0]['Resource_2'] == 1.0
        
        component.distribute_resource_among_patients_evenly('Resource_2', 0.5, patients_with_demand)
        for patient in patients_with_demand:
            assert patient.demand_met[0]['Resource_2'] == 0.5
        
        component.distribute_resource_among_patients_evenly('Resource_2', 0.0, patients_with_demand)
        for patient in patients_with_demand:
            assert patient.demand_met[0]['Resource_2'] == 0.0     
    
    def test_get_patients_with_demand(self):
        component = Component.HospitalComponent()
        component.form('ExampleComponent', self.COMPONENT_PARAMETERS)
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient', self.PATIENT_PARAMETERS_SIMPLE)
        component.patients += [copy.deepcopy(patient) for _ in range(10)]
        patients_with_demand = component.get_patients_with_demand('Resource_2')
        assert len(patients_with_demand) == 10
        
        patients_with_demand = component.get_patients_with_demand('Resource_0')
        assert len(patients_with_demand) == 0
        
    def test_get_patients_that_move(self):
        component = Component.HospitalComponent()
        component.form('Department_1', self.COMPONENT_PARAMETERS)
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient', self.PATIENT_PARAMETERS_SIMPLE)
        component.patients += [copy.deepcopy(patient) for _ in range(10)]
        assert component.get_patients_that_move() == []
        component.patients[0].move_to_next_department()
        patients_that_move = component.get_patients_that_move()
        assert len(patients_that_move) == 1
        assert len(component.patients) == 9
        assert patients_that_move[0].get_current_department() == 'Department_2'

        component.patients[1].move_to_next_department()
        patients_that_move = component.get_patients_that_move()
        assert len(patients_that_move) == 1
        assert len(component.patients) == 8
        assert patients_that_move[0].get_current_department() == 'Department_2'
        
        for patient in component.patients:
            patient.move_to_next_department()
        patients_that_move = component.get_patients_that_move()
        assert len(patients_that_move) == 8
        assert len(component.patients) == 0
        for patient in patients_that_move:
            assert patient.get_current_department() == 'Department_2'
    
    def test_set_new_patients(self):
        department_1 = Component.HospitalComponent()
        department_1.form('Department_1', self.COMPONENT_PARAMETERS)

        department_2 = Component.HospitalComponent()
        department_2.form('Department_2', self.COMPONENT_PARAMETERS)

        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient', self.PATIENT_PARAMETERS_SIMPLE)
        department_1.patients += [copy.deepcopy(patient) for _ in range(10)]
        department_1.patients[0].move_to_next_department()
        patients_that_move = department_1.get_patients_that_move()
        department_2.set_new_patients(patients_that_move)
        assert len(department_1.patients) == 9
        assert len(department_2.patients) == 1
        assert department_2.patients[0].get_current_department() == 'Department_2'
    
    def test_patient_in_component(self):
        component = Component.HospitalComponent()
        component.form('Department_1', self.COMPONENT_PARAMETERS)
        patient = Patient.PatientType()
        patient.set_parameters('ExamplePatient', self.PATIENT_PARAMETERS_SIMPLE)
        assert component.patient_in_component(patient) == True
        patient.move_to_next_department()
        assert component.patient_in_component(patient) == False

class TestPatientSource():

    RESOURCE_DYNAMICS = [{'Resource': 'Resource_1', 'SupplyOrDemand': 'supply', 'SupplyOrDemandType': 'Supply', 'AtTimeStep': [0, 2, 5, 10], 'Amount': [50, 30, 10, 20]},
                         {'Resource': 'Resource_2', 'SupplyOrDemand': 'demand', 'SupplyOrDemandType': 'OperationDemand', 'AtTimeStep': [0, 1, 2, 5], 'Amount': [10, 5, 15, 0]}]
    
    PATIENT_ARRIVAL_DYNAMICS = [{"Resource": "Red", "SupplyOrDemand": "demand", "SupplyOrDemandType": "OperationDemand", 
                                "AtTimeStep": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                                "Amount": [0, 0, 10, 10, 10, 15, 15, 15, 15, 15]},
                                {"Resource": "Yellow", "SupplyOrDemand": "demand", "SupplyOrDemandType": "OperationDemand", 
                                "AtTimeStep": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                                "Amount": [0, 0, 20, 20, 0, 0, 0, 10, 10, 0]}]
    
    COMPONENT_PARAMETERS = {
        "ComponentClass": "PatientSource",
        "PatientLibrary": "./tests/test_inputs/test_inputs_Hospital_PatientTypeLibrary.json",
        "RecoveryModel": {
            "Type": "NoRecoveryActivity",
            "Parameters": {},
            "DamageFunctionalityRelation": {
                "Type": "Constant"
            }
        },
        "OperationDemand": {
            "Green": {
                "Amount": 0,
                "ResourceClassName": "ConcreteResource",
                "FunctionalityToAmountRelation": "Constant"
            },
            "Red": {
                "Amount": 0,
                "ResourceClassName": "ConcreteResource",
                "FunctionalityToAmountRelation": "Constant"
            }
        }
    }

    STRESS_SCENARIO = [{"Resource": "Red", "SupplyOrDemand": "demand", "SupplyOrDemandType": "OperationDemand", "AtTimeStep": [0, 1, 2, 3, 4, 5, 6], "Amount": [0, 0, 10, 10, 10, 15, 15]},
                       {"Resource": "Green", "SupplyOrDemand": "demand", "SupplyOrDemandType": "OperationDemand", "AtTimeStep": [0, 1, 2, 3, 4, 5, 6], "Amount": [0, 100, 100, 100, 50, 50, 50]}]
    
    MAIN_FILE = './tests/test_inputs/test_inputs_Hospital_Main.json'
    EXCEL_INPUT_2 = './tests/test_inputs/test_inputs_Hospital_ExcelInput2.xlsx'
    ADDITIONAL_DATA_LOCATION = './tests/test_inputs/'

    def read_excel_input(self, input_filename: str):
        sheet_names = ['ResourceSupply', 'StressScenario', 'PatientProfiles']
        input_data = pd.read_excel(input_filename, sheet_name=sheet_names, header=None, na_filter=False)
        for sheet_name in sheet_names:
            input_data[sheet_name].replace('', np.nan, inplace=True)
        return input_data
    
    def test_set_patient_library(self):
        component = Component.PatientSource()
        excel_input = self.read_excel_input(self.EXCEL_INPUT_2)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        component_library_dict = main.read_file(input_dict['ComponentLibrary']['ComponentLibraryFile'])
        main.format_patient_library_file_location(component_library_dict, self.ADDITIONAL_DATA_LOCATION, default_patient_library_file='test_inputs_Hospital_PatientTypeLibrary.json')
        main.format_patient_library_file(excel_input, input_dict, self.ADDITIONAL_DATA_LOCATION)
        component.set_patient_library('./tests/test_inputs/test_inputs_Hospital_PatientTypeLibrary.json')
        assert len(component.patient_library) == 4
        assert list(component.patient_library.keys())[0] == 'Red'
    
    def test_form(self):
        component = Component.PatientSource()
        component.form('ExampleComponent', self.COMPONENT_PARAMETERS)
        assert component.functionality_level == 1.0
        assert component.functional == []
        assert isinstance(component.patient_library, dict)
        assert component.name == 'ExampleComponent'
        assert component.demand['OperationDemand']['Green'].current_amount == 0
        assert component.demand['OperationDemand']['Red'].current_amount == 0

    def test_get_resource_amount_based_on_time_step(self):
        component = Component.PatientSource()
        component.form('PatientSource', self.COMPONENT_PARAMETERS)
        assert component.get_resource_amount_based_on_time_step(self.PATIENT_ARRIVAL_DYNAMICS[0], 0) == 0
        assert component.get_resource_amount_based_on_time_step(self.PATIENT_ARRIVAL_DYNAMICS[0], 2) == 10
        assert component.get_resource_amount_based_on_time_step(self.PATIENT_ARRIVAL_DYNAMICS[0], 5) == 15
    
    def test_create_patients(self):
        component = Component.PatientSource()
        component.form('PatientSource', self.COMPONENT_PARAMETERS)
        component.set_predefined_resource_dynamics(self.STRESS_SCENARIO)
        component.create_patients(0)
        assert len(component.patients) == 0
        component.create_patients(1)
        assert len(component.patients) == 100
        component.create_patients(2)
        assert len(component.patients) == 100 + 110
        component.create_patients(3)
        assert len(component.patients) == 100 + 110 + 110
        component.create_patients(4)
        assert len(component.patients) == 100 + 110 + 110 + 60
        component.create_patients(5)
        assert len(component.patients) == 100 + 110 + 110 + 60 + 65
        component.create_patients(6)
        assert len(component.patients) == 100 + 110 + 110 + 60 + 65 + 65
   
class TestStandardiReCoDeSComponent_SingleRecoveryActivity():
    component_library_file = "./tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_ComponentLibrary.json"
    system_configuration_file = './tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_SystemConfiguration.json'
    resource_dict = {"ElectricPower": {"Amount": 5, "FunctionalityToAmountRelation": "Linear",
                                       "UnmetDemandToAmountRelation": {"ElectricPower": "Binary"},
                                       "ResourceClassName": "ConcreteResource"}}
    recovery_model_parameters = {"Type": "SingleRecoveryActivity",
                                 "Parameters": {"Repair": {"Duration": {"Deterministic": {"Value": 10}},
                                                           "Demand": [{"Resource": "Workers", "Amount": 10}]}},
                                 "DamageFunctionalityRelation": {"Type": "ReverseLinear"}}

    @pytest.fixture()
    def json_system_creator(self) -> SystemCreator.SystemCreator:
        return SystemCreator.JSONSystemCreator()

    @pytest.fixture()
    def component_library(self) -> ComponentLibraryCreator.ComponentLibraryCreator:
        return ComponentLibraryCreator.JSONComponentLibraryCreator(self.component_library_file).form_library()

    def create_system_to_test(self, json_system_creator, component_library) -> System.System:
        system = System.BuiltEnvironmentSystem(self.system_configuration_file, component_library, json_system_creator)
        self.system = system

    def create_component_with_simple_recovery_model(self) -> Component.Component:
        component = Component.StandardiReCoDeSComponent()
        component.set_recovery_model(self.recovery_model_parameters)
        return component

    def test_init(self):
        component = Component.StandardiReCoDeSComponent()
        assert all([component.functionality_level == 1.0,
                    component.functional == [],
                    component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value] == {},
                    component.demand[Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value] == {},
                    component.demand[Component.StandardiReCoDeSComponent.DemandTypes.RECOVERY_DEMAND.value] == {}])

    def test_set_recovery_model(self):
        component = self.create_component_with_simple_recovery_model()
        assert all([isinstance(component.recovery_model, ComponentRecoveryModel.SingleRecoveryActivity),
                    component.recovery_model.recovery_activity.rate == 0.1,
                    isinstance(component.recovery_model.damage_to_functionality_relation, Relation.ReverseLinear)])

    def test_set_get_damage_level(self):
        component = self.create_component_with_simple_recovery_model()
        damage_level = 0.4
        component.set_initial_damage_level(damage_level)
        assert component.get_damage_level() == damage_level
    
    def test_set_wrong_damage_level(self):
        component = self.create_component_with_simple_recovery_model()
        damage_level = -0.4
        with pytest.raises(ValueError):
            component.set_initial_damage_level(damage_level)
        
    def test_set_name(self):
        component = self.create_component_with_simple_recovery_model()
        component_name = 'Component_Name'
        component.set_name(component_name)
        assert component_name == component.name

    def test_set_single_locality(self):
        component = self.create_component_with_simple_recovery_model()
        component.set_locality([0])
        assert component.get_locality() == [0]

    def test_set_two_localities(self):
        component = self.create_component_with_simple_recovery_model()
        component.set_locality([0, 1])
        assert component.get_locality() == [0, 1]
    
    def test_has_operation_demand(self, json_system_creator, component_library):
        self.create_system_to_test(json_system_creator, component_library)
        bool_list = []
        target_bools = [True, True, False, False, True, False, False, True, True, False, False]
        for target_bool, component in zip(target_bools, self.system.components):
            bool_list.append(component.has_operation_demand() == target_bool)
        assert all(bool_list)

    def test_has_resource_supply(self, json_system_creator, component_library):
        self.create_system_to_test(json_system_creator, component_library)
        bool_list = []
        bool_list.append(self.system.components[0].has_resource_supply('Communication') == True)
        bool_list.append(self.system.components[0].has_resource_supply('CoolingWater') == False)
        bool_list.append(self.system.components[1].has_resource_supply('CoolingWater') == False)
        bool_list.append(self.system.components[1].has_resource_supply('ElectricPower') == True)
        bool_list.append(self.system.components[2].has_resource_supply('ElectricPower') == False)
        assert all(bool_list)

    def test_add_one_resource(self):
        component = Component.StandardiReCoDeSComponent()
        component.add_resources(Component.SupplyOrDemand.SUPPLY.value,
                                Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value, 
                                self.resource_dict)
        assert all([component.demand[Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value] == {},
                    component.demand[Component.StandardiReCoDeSComponent.DemandTypes.RECOVERY_DEMAND.value] == {},
                    len(component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value]) == 1,
                    component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                        'ElectricPower'].name == 'ElectricPower',
                    component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                        'ElectricPower'].initial_amount == 5,
                    component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                        'ElectricPower'].current_amount == 5])

    def test_add_one_resource_wrong_supply_key_string(self):
        component = Component.StandardiReCoDeSComponent()
        with pytest.raises(KeyError):
            component.add_resources(Component.SupplyOrDemand.SUPPLY.value, 'supply', self.resource_dict)

    def test_add_one_resource_wrong_demand_key_string(self):
        component = Component.StandardiReCoDeSComponent()
        with pytest.raises(KeyError):
            component.add_resources(Component.SupplyOrDemand.DEMAND.value, 'operation_demand', self.resource_dict)

    def test_add_multiple_resources(self):
        component = Component.StandardiReCoDeSComponent()
        for _ in range(5):
            component.add_resources(Component.SupplyOrDemand.SUPPLY.value,
                                    Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value, self.resource_dict)
        boolean_list = []
        for resource in component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value].values():
            boolean_list.append(resource.name == 'ElectricPower')
            boolean_list.append(resource.initial_amount == 5)
            boolean_list.append(resource.current_amount == 5)

        assert all([component.demand[Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value] == {},
                    component.demand[Component.StandardiReCoDeSComponent.DemandTypes.RECOVERY_DEMAND.value] == {},
                    len(component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value]) == 1,
                    all(boolean_list)])
    
    def test_get_current_resource_amount_no_damage(self):
        component = self.create_component_with_simple_recovery_model()
        component.add_resources(Component.SupplyOrDemand.SUPPLY.value,
                                Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value, self.resource_dict)
        component.update(0)
        power_amount = component.get_current_resource_amount(Component.SupplyOrDemand.SUPPLY.value,
                                                            Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value,
                                                            'ElectricPower')
        assert power_amount == self.resource_dict['ElectricPower']['Amount']
    
    def test_get_current_resource_amount_with_damage(self):
        component = self.create_component_with_simple_recovery_model()
        component.add_resources(Component.SupplyOrDemand.SUPPLY.value,
                                Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value, self.resource_dict)
        damage_level = 0.5
        component.set_initial_damage_level(damage_level)  
        component.update(1)
        power_amount = component.get_current_resource_amount(Component.SupplyOrDemand.SUPPLY.value,
                                                            Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value,
                                                            'ElectricPower')
        assert power_amount == self.resource_dict['ElectricPower']['Amount'] * 0.5

    def test_update_functionality_once(self):
        component = self.create_component_with_simple_recovery_model()
        damage_level = 0.23
        functionality_level = 0.77
        component.set_initial_damage_level(damage_level)
        component.update_functionality()
        assert math.isclose(component.functionality_level, functionality_level) 

    def test_update_functionality_twice(self):
        component = self.create_component_with_simple_recovery_model()
        damage_level = 0.23
        component.set_initial_damage_level(damage_level)
        component.update_functionality()
        damage_level = 0.56
        component.set_initial_damage_level(damage_level)
        component.update_functionality()
        functionality_level = 0.44
        assert math.isclose(component.functionality_level, functionality_level) 
    
    def test_check_if_functional(self):
        component = self.create_component_with_simple_recovery_model()
        damage_level = 0.23
        component.set_initial_damage_level(damage_level)
        component.update_functionality()
        component.check_if_functional(time_step=1)
        assert component.functional == [1]
    
    def test_check_if_functional_full_damage(self):
        component = self.create_component_with_simple_recovery_model()
        damage_level = 1.0
        component.set_initial_damage_level(damage_level)
        component.update_functionality()
        component.check_if_functional(time_step=5)   
        assert component.functional == []
    
    def test_check_if_functional_during_recovery(self):
        component = self.create_component_with_simple_recovery_model()
        damage_level = 1.0
        component.set_initial_damage_level(damage_level)                
        for time_step in range(0, 10):
            component.update_functionality()
            component.check_if_functional(time_step)            
            component.recover(time_step)            
        assert component.functional == list(range(1, 10))    

    def test_update_resources_based_on_component_functionality(self):
        component = self.create_component_with_simple_recovery_model()
        component.add_resources(Component.SupplyOrDemand.SUPPLY.value,
                                Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value, self.resource_dict)
        damage_level = 0.23
        target_functionality_level = 0.77
        component.set_initial_damage_level(damage_level)
        component.update_functionality()
        component.update_resources_based_on_component_functionality(Component.SupplyOrDemand.SUPPLY.value,
                                                                    Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value)
        assert math.isclose(component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                                'ElectricPower'].current_amount,
                            component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                                'ElectricPower'].initial_amount * target_functionality_level)
    
    def test_update_supply_based_on_component_functionality(self):
        component = self.create_component_with_simple_recovery_model()
        component.add_resources(Component.SupplyOrDemand.SUPPLY.value,
                                Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value, self.resource_dict)
        damage_levels_to_check = [0.0, 0.8, 0.2]
        for damage_level in damage_levels_to_check:
            target_supply = 5.0 * (1-damage_level)
            component.set_initial_damage_level(damage_level)
            component.update_functionality()
            bool_list = []
            target_supply = 5.0 * (1-damage_level)
            component.update_supply_based_on_component_functionality()
            current_supply = component.get_current_resource_amount(Component.SupplyOrDemand.SUPPLY.value, 
                                                                Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value, 
                                                                'ElectricPower')
            bool_list.append(math.isclose(target_supply, current_supply))        
        assert all(bool_list)

    def test_update_operation_demand(self):
        component = self.create_component_with_simple_recovery_model()
        component.add_resources(Component.SupplyOrDemand.DEMAND.value,
                                Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value, self.resource_dict)
        damage_levels_to_check = [0.0, 0.8, 0.2]
        for damage_level in damage_levels_to_check:
            target_supply = 5.0 * (1-damage_level)
            component.set_initial_damage_level(damage_level)
            component.update_functionality()
            bool_list = []
            target_supply = 5.0 * (1-damage_level)
            component.update_operation_demand()
            current_supply = component.get_current_resource_amount(Component.SupplyOrDemand.DEMAND.value, 
                                                                Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value, 
                                                                'ElectricPower')
            bool_list.append(math.isclose(target_supply, current_supply))        
        assert all(bool_list)

    def test_update_recovery_demand(self):
        component = self.create_component_with_simple_recovery_model()
        component.update_functionality()
        component.update_recovery_demand()
        bool_list = []
        bool_list.append(len(component.demand['RecoveryDemand']) == 0)  
        component.set_initial_damage_level(0.5)
        component.update_functionality()
        component.update_recovery_demand()
        bool_list.append(component.get_current_resource_amount(Component.SupplyOrDemand.DEMAND.value, 
                                                                Component.StandardiReCoDeSComponent.DemandTypes.RECOVERY_DEMAND.value, 
                                                                'Workers') == 10)
        component.set_initial_damage_level(0.0)
        component.update_functionality()
        component.update_recovery_demand()
        bool_list.append(len(component.demand['RecoveryDemand']) == 0)
        assert all(bool_list)

    def test_update_supply_based_on_unmet_demand(self):
        bool_list = []
        component = self.create_component_with_simple_recovery_model()
        component.add_resources(Component.SupplyOrDemand.SUPPLY.value,
                                Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value, self.resource_dict)
        percent_of_met_demand = 1.0
        component.update_supply_based_on_unmet_demand('ElectricPower', percent_of_met_demand)        
        bool_list.append(math.isclose(component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                             'ElectricPower'].current_amount, 5.0))
        component.add_resources(Component.SupplyOrDemand.SUPPLY.value,
                                Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value, 
                                self.resource_dict)        
        percent_of_met_demand = 0.5
        component.update_supply_based_on_unmet_demand('ElectricPower', percent_of_met_demand)
        bool_list.append(component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                             'ElectricPower'].current_amount == 0.0)  
        percent_of_met_demand = 0.0
        component.update_supply_based_on_unmet_demand('ElectricPower', percent_of_met_demand)
        bool_list.append(component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                         'ElectricPower'].current_amount == 0.0)     
        assert all(bool_list)

    def test_update_once(self):
        time_step = 5
        component = self.create_component_with_simple_recovery_model()
        component.add_resources(Component.SupplyOrDemand.SUPPLY.value,
                                Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value, self.resource_dict)
        component.add_resources(Component.SupplyOrDemand.DEMAND.value,
                                Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value,
                                self.resource_dict)
        damage_level = 0.4
        component.set_initial_damage_level(damage_level)
        component.update(time_step)
        functionality_level = 0.6
        assert all([component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                        'ElectricPower'].initial_amount == 5,
                    component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                        'ElectricPower'].current_amount == 5 * functionality_level,
                    component.demand[Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value][
                        'ElectricPower'].initial_amount == 5,
                    component.demand[Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value][
                        'ElectricPower'].current_amount == 5 * functionality_level])

    def test_update_twice(self):
        time_step = 10
        component = self.create_component_with_simple_recovery_model()
        component.add_resources(Component.SupplyOrDemand.SUPPLY.value,
                                Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value, self.resource_dict)
        component.add_resources(Component.SupplyOrDemand.DEMAND.value,
                                Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value,
                                self.resource_dict)
        damage_level = 0.4
        component.set_initial_damage_level(damage_level)
        component.update(time_step)
        damage_level = 0.1
        component.set_initial_damage_level(damage_level)
        component.update(time_step)
        functionality_level = 0.9
        assert all([component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                        'ElectricPower'].initial_amount == 5,
                    component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                        'ElectricPower'].current_amount == 5 * functionality_level,
                    component.demand[Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value][
                        'ElectricPower'].initial_amount == 5,
                    component.demand[Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value][
                        'ElectricPower'].current_amount == 5 * functionality_level])

    def test_update_multiple_resources_once(self):
        time_step = 5
        component = self.create_component_with_simple_recovery_model()
        for _ in range(5):
            component.add_resources(Component.SupplyOrDemand.SUPPLY.value,
                                    Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value, self.resource_dict)
        damage_level = 0.4
        component.set_initial_damage_level(damage_level)
        component.update(time_step)
        functionality_level = 0.6
        boolean_list = []
        boolean_list.append(component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                                'ElectricPower'].initial_amount == 5)
        boolean_list.append(component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                                'ElectricPower'].current_amount == 5 * functionality_level)
        assert all([component.demand[Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value] == {},
                    component.demand[Component.StandardiReCoDeSComponent.DemandTypes.RECOVERY_DEMAND.value][
                        'Workers'].initial_amount == 10,
                    component.demand[Component.StandardiReCoDeSComponent.DemandTypes.RECOVERY_DEMAND.value][
                        'Workers'].current_amount == 10,
                    all(boolean_list)])

    def test_update_multiple_resources_twice(self):
        component = self.create_component_with_simple_recovery_model()
        time_step = 0
        for _ in range(5):
            component.add_resources(Component.SupplyOrDemand.SUPPLY.value,
                                    Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value, self.resource_dict)
        damage_level = 0.4
        component.set_initial_damage_level(damage_level)
        component.update(time_step)
        damage_level = 0.9
        component.set_initial_damage_level(damage_level)
        component.update(time_step)
        functionality_level = 0.1
        boolean_list = []
        boolean_list.append(component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                                'ElectricPower'].initial_amount == 5)
        boolean_list.append(math.isclose(component.supply[Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value][
                                             'ElectricPower'].current_amount, 5 * functionality_level))
        assert all([component.demand[Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value] == {},
                    component.demand[Component.StandardiReCoDeSComponent.DemandTypes.RECOVERY_DEMAND.value][
                        'Workers'].initial_amount == 10,
                    component.demand[Component.StandardiReCoDeSComponent.DemandTypes.RECOVERY_DEMAND.value][
                        'Workers'].current_amount == 10,
                    all(boolean_list)])
    
    def test_set_recovery_model_activities_demand_to_met(self):
        component = self.create_component_with_simple_recovery_model()
        damage_level = 0.5
        component.set_initial_damage_level(damage_level)
        component.set_unmet_demand_for_recovery_activities('Workers', 0.0)
        bool_list = [component.recovery_model.recovery_activity.demand_met == 0.0]
        component.set_recovery_model_activities_demand_to_met()
        bool_list.append(component.recovery_model.recovery_activity.demand_met == 1.0)
        assert all(bool_list)

    def test_recover_once(self):
        time_step = 5
        component = self.create_component_with_simple_recovery_model()
        damage_level = 0.4
        component.set_initial_damage_level(damage_level)
        repair_rate = component.recovery_model.recovery_activity.rate
        component.recover(time_step)
        assert math.isclose(component.get_damage_level(), damage_level - repair_rate)

    def test_recover_full(self):
        component = self.create_component_with_simple_recovery_model()
        damage_level = 0.4
        component.set_initial_damage_level(damage_level)
        time_step = 0
        while not (math.isclose(component.get_damage_level(), 0, abs_tol=1e-10)):
            component.recover(time_step)
            time_step += 1
        assert time_step == 10

    def test_recover_full_two_damage_levels(self, json_system_creator, component_library):
        self.create_system_to_test(json_system_creator, component_library)
        component = self.create_component_with_simple_recovery_model()
        damage_levels = [0.4, 1.0]
        time_steps = []
        for damage_level in damage_levels:
            component.set_initial_damage_level(damage_level)
            time_step = 0
            while not (math.isclose(component.get_damage_level(), 0, abs_tol=1e-10)):
                component.recover(time_step)
                time_step += 1
            time_steps.append(time_step)
        assert time_steps == [10, 10]    

    def test_set_unmet_demand_for_recovery_activities(self):
        component = self.create_component_with_simple_recovery_model()
        bool_list = []
        time_step = 1
        damage_level = 0.5
        repair_duration = self.recovery_model_parameters['Parameters']['Repair']['Duration']['Deterministic']['Value']
        component.set_initial_damage_level(damage_level)
        component.set_unmet_demand_for_recovery_activities('Workers', 0.0)
        component.recover(time_step)
        bool_list.append(component.get_damage_level() == damage_level)
        component.set_unmet_demand_for_recovery_activities('Workers', 1.0)
        component.recover(time_step)
        bool_list.append(math.isclose(component.get_damage_level(), damage_level - damage_level / repair_duration))
        component.set_unmet_demand_for_recovery_activities('Workers', 0.5)
        component.recover(time_step)
        bool_list.append(math.isclose(component.get_damage_level(),
                                      damage_level - damage_level / repair_duration - 0.5 * damage_level / repair_duration))
        assert all(bool_list)

class TestStandardiReCoDeSComponent_MultipleRecoveryActivities():
    recovery_model_parameters = {
        "Type": "MultipleRecoveryActivities",
        "Parameters": {
            "RapidInspection": {
                "Duration": {"Lognormal": {"Median": 1, "Dispersion": 0.0}},
                "Demand": [{"Resource": "FirstResponderEngineer", "Amount": 0.1}],
                "PrecedingActivities": []
            },
            "DetailedInspection": {
                "Duration": {"Deterministic": {"Value": 3}},
                "Demand": [{"Resource": "SeniorEngineer", "Amount": 2}],
                "PrecedingActivities": ["RapidInspection"]
            },
            "CleanUp": {
                "Duration": {"Deterministic": {"Value": 5}},
                "Demand": [{"Resource": "CleanUpCrew", "Amount": 1}],
                "PrecedingActivities": ["RapidInspection"]
            },
            "Financing": {
                "Duration": {"Deterministic": {"Value": 5}},
                "Demand": [{"Resource": "Money", "Amount": 0}],
                "PrecedingActivities": ["RapidInspection", "DetailedInspection"]
            },
            "ArchAndEngDesign": {
                "Duration": {"Deterministic": {"Value": 15}},
                "Demand": [{"Resource": "EngineeringDesignTeam", "Amount": 1}],
                "PrecedingActivities": ["RapidInspection", "DetailedInspection"]
            },
            "ContractorMobilization": {
                "Duration": {"Deterministic": {"Value": 10}},
                "Demand": [{"Resource": "Contractor", "Amount": 1}],
                "PrecedingActivities": ["RapidInspection", "DetailedInspection", "ArchAndEngDesign"]
            },
            "Permitting": {
                "Duration": {"Deterministic": {"Value": 15}},
                "Demand": [{"Resource": "PlanCheckEngineeringTeam", "Amount": 1}],
                "PrecedingActivities": ["RapidInspection", "DetailedInspection", "ArchAndEngDesign"]
            },
            "Repair": {
                "Duration": {"Deterministic": {"Value": 30}},
                "Demand": [{"Resource": "RepairCrew", "Amount": 10}],
                "PrecedingActivities": ["RapidInspection", "DetailedInspection", "CleanUp", "Financing",
                                        "ArchAndEngDesign", "ContractorMobilization", "Permitting"]
            }
        },
        "DamageFunctionalityRelation": {"Type": "ReverseBinary"}
    }

    @pytest.fixture()
    def json_system_creator(self) -> SystemCreator.SystemCreator:
        return SystemCreator.JSONSystemCreator()

    @pytest.fixture()
    def component_library(self) -> ComponentLibraryCreator.ComponentLibraryCreator:
        return ComponentLibraryCreator.JSONComponentLibraryCreator(self.component_library_file).form_library()

    def create_system_to_test(self, json_system_creator, component_library) -> System.System:
        system = System.BuiltEnvironmentSystem(self.system_configuration_file, component_library, json_system_creator)
        self.system = system

    def create_component_with_recovery_model(self) -> Component.Component:
        component = Component.StandardiReCoDeSComponent()
        component.set_recovery_model(self.recovery_model_parameters)
        return component

    def test_update_recovery_demand_no_damage(self):
        component = self.create_component_with_recovery_model()
        component.update_recovery_demand()
        assert component.demand['RecoveryDemand'] == {}

    def test_update_recovery_demand_inspection(self):
        component = self.create_component_with_recovery_model()
        component.set_initial_damage_level(0.2)
        component.update_recovery_demand()
        assert all([component.demand['RecoveryDemand']['FirstResponderEngineer'].initial_amount == 0.1,
                    component.demand['RecoveryDemand']['FirstResponderEngineer'].current_amount == 0.1,
                    len(component.demand['RecoveryDemand']) == 1])

    def test_update_recovery_demand_inspection_finished(self):
        component = self.create_component_with_recovery_model()
        component.set_initial_damage_level(0.2)
        component.update_recovery_demand()
        component.recover(time_step=1)
        component.update_recovery_demand()
        assert all([component.demand['RecoveryDemand']['SeniorEngineer'].initial_amount == 2,
                    component.demand['RecoveryDemand']['SeniorEngineer'].current_amount == 2,
                    component.demand['RecoveryDemand']['CleanUpCrew'].initial_amount == 1,
                    component.demand['RecoveryDemand']['CleanUpCrew'].current_amount == 1,
                    len(component.demand['RecoveryDemand']) == 2])

    def test_update_recovery_demand_some_activities_finished(self):
        component = self.create_component_with_recovery_model()
        component.set_initial_damage_level(0.2)
        component.update_recovery_demand()
        for time_step in range(5):
            component.recover(time_step=time_step)
        component.update_recovery_demand()
        assert all([component.demand['RecoveryDemand']['CleanUpCrew'].initial_amount == 1,
                    component.demand['RecoveryDemand']['CleanUpCrew'].current_amount == 1,
                    component.demand['RecoveryDemand']['Money'].initial_amount == 0,
                    component.demand['RecoveryDemand']['Money'].current_amount == 0,
                    component.demand['RecoveryDemand']['EngineeringDesignTeam'].initial_amount == 1,
                    component.demand['RecoveryDemand']['EngineeringDesignTeam'].current_amount == 1,
                    len(component.demand['RecoveryDemand']) == 3])

    def test_update_recovery_demand_impeding_factors_finished(self):
        component = self.create_component_with_recovery_model()
        component.set_initial_damage_level(0.2)
        component.update_recovery_demand()
        for time_step in range(35):
            component.recover(time_step=time_step)
        component.update_recovery_demand()
        assert all([component.demand['RecoveryDemand']['RepairCrew'].initial_amount == 10,
                    component.demand['RecoveryDemand']['RepairCrew'].current_amount == 10,
                    len(component.demand['RecoveryDemand']) == 1])

    def test_update_recovery_demand_repair_finished(self):
        component = self.create_component_with_recovery_model()
        component.set_initial_damage_level(0.2)
        component.update_recovery_demand()
        for time_step in range(66):
            component.recover(time_step=time_step)
        component.update_recovery_demand()
        assert component.demand['RecoveryDemand'] == {}

    def test_recover_once(self):
        component = self.create_component_with_recovery_model()
        component.set_initial_damage_level(0.2)
        component.update_recovery_demand()
        component.recover(0)
        assert component.recovery_model.recovery_activities['RapidInspection'].time_steps == [0]

    def test_recover_fully(self):
        component = self.create_component_with_recovery_model()
        component.set_initial_damage_level(0.2)
        component.update_recovery_demand()
        for time_step in range(66):
            component.recover(time_step=time_step)
        assert all([component.recovery_model.recovery_activities['RapidInspection'].time_steps == [0],
                    component.recovery_model.recovery_activities['DetailedInspection'].time_steps == [1, 2, 3],
                    component.recovery_model.recovery_activities['CleanUp'].time_steps == [1, 2, 3, 4, 5],
                    component.recovery_model.recovery_activities['Financing'].time_steps == [4, 5, 6, 7, 8],
                    component.recovery_model.recovery_activities['ArchAndEngDesign'].time_steps == list(range(4, 19)),
                    component.recovery_model.recovery_activities['ContractorMobilization'].time_steps == list(
                        range(19, 29)),
                    component.recovery_model.recovery_activities['Permitting'].time_steps == list(range(19, 34)),
                    component.recovery_model.recovery_activities['Repair'].time_steps == list(range(34, 64))])

    def test_recover_partial_demand_met(self):
        component = self.create_component_with_recovery_model()
        component.set_initial_damage_level(0.2)
        component.update_recovery_demand()
        component.recovery_model.recovery_activities['Repair'].demand_met = 0.5
        component.recovery_model.recovery_activities['Financing'].demand_met = 0.5
        component.recovery_model.recovery_activities['ContractorMobilization'].demand_met = 0.5
        for time_step in range(100):
            component.recover(time_step=time_step)
        assert all([component.recovery_model.recovery_activities['Permitting'].time_steps == list(range(19, 34)),
                    component.recovery_model.recovery_activities['Repair'].time_steps == list(range(39, 99)),
                    component.recovery_model.recovery_activities['ContractorMobilization'].time_steps == list(
                        range(19, 39)),
                    component.recovery_model.recovery_activities['RapidInspection'].time_steps == [0],
                    component.recovery_model.recovery_activities['DetailedInspection'].time_steps == [1, 2, 3],
                    component.recovery_model.recovery_activities['CleanUp'].time_steps == [1, 2, 3, 4, 5],
                    component.recovery_model.recovery_activities['Financing'].time_steps == [4, 5, 6, 7, 8, 9, 10, 11,
                                                                                             12, 13],
                    component.recovery_model.recovery_activities['ArchAndEngDesign'].time_steps == list(range(4, 19))
                    ])  
    
    def test_get_current_resource_amount_inspection(self):
        component = self.create_component_with_recovery_model()
        component.set_initial_damage_level(0.2)
        component.update_recovery_demand()
        inspection_demand = component.get_current_resource_amount(Component.SupplyOrDemand.DEMAND.value,
                                                                  Component.StandardiReCoDeSComponent.DemandTypes.RECOVERY_DEMAND.value,
                                                                  'FirstResponderEngineer')
        assert inspection_demand == self.recovery_model_parameters['Parameters']['RapidInspection']['Demand'][0]['Amount']
