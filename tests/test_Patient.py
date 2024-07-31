import random
from pyrecodes_hospitals import Patient

random.seed(1)

class TestPatientType():

    PATIENT_NAME = 'ExamplePatient'
    PATIENT_PARAMETERS_SIMPLE = [{'Department_1': {'BaselineLengthOfStay': 8, 
                                                   'BaselineMortalityRate': 0.01,
                                                   'ResourcesRequired': 
                                                       [{'ResourceName': 'Resource_1', 'ResourceAmount': 10, 'ConsequencesOfUnmetDemand': [{'Mortality Rate Increase [per missing nurse]': 1.2}]},
                                                       {'ResourceName': 'Stretcher', 'ResourceAmount': 1, 'ConsequencesOfUnmetDemand': [{'Death In [hours]': 0}]},
                                                       {'ResourceName': 'Resource_2', 'ResourceAmount': 5, 'ConsequencesOfUnmetDemand': [{'Death In [hours]': 0}]},
                                                       {'ResourceName': 'Resource_3', 'ResourceAmount': 5, 'ConsequencesOfUnmetDemand': [{'Length Of Stay Extended': 1.5}]}]}},
                                {'Department_2': {'BaselineLengthOfStay': 5, 
                                                   'BaselineMortalityRate': 0.0,
                                                   'ResourcesRequired': 
                                                       [{'ResourceName': 'Stretcher', 'ResourceAmount': 1, 'ConsequencesOfUnmetDemand': [{'Death In [hours]': 0}]},
                                                        {'ResourceName': 'Resource_4', 'ResourceAmount': 1, 'ConsequencesOfUnmetDemand': [{'Mortality Rate Increase': 1.1}]},
                                                       {'ResourceName': 'Resource_5', 'ResourceAmount': 5, 'ConsequencesOfUnmetDemand': [{'Death In [hours]': 2}]},
                                                       {'ResourceName': 'Resource_6', 'ResourceAmount': 5, 'ConsequencesOfUnmetDemand': [{'Length Of Stay Extended [per missing nurse]': 1.2}]}]}},                                
                                {'EXIT': {'BaselineLengthOfStay': 1000, 
                                            'BaselineMortalityRate': 0.0,
                                            'ResourcesRequired':[]}}
                                ]

    def test_set_parameters(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        assert patient.name == self.PATIENT_NAME
        assert patient.demand == [{'Resource_1': 10, 'Stretcher': 1, 'Resource_2': 5, 'Resource_3': 5}, {'Stretcher': 1, 'Resource_4': 1, 'Resource_5': 5, 'Resource_6': 5}, {}]
        assert patient.departments == ['Department_1', 'Department_2', 'EXIT']
        assert patient.mortality_rates == [0.01, 0.0, 0.0]
        assert patient.lengths_of_stay == [8, 5, 1000]
        assert patient.flow == [{'Department': 'Department_1', 'TimeStepAtDepartment': [], 'TimeStepTreated': []}]
        assert patient.treated == False
        assert patient.alive == True
    
    def test_get_resource_demand(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        resource_demand = patient.get_resource_demand()
        assert resource_demand == {'Resource_1': 10, 'Stretcher': 1, 'Resource_2': 5, 'Resource_3': 5}
        patient.flow[0]['TimeStepAtDepartment'] = [1]
        resource_demand = patient.get_resource_demand()
        assert resource_demand == {'Resource_1': 10, 'Stretcher': 0, 'Resource_2': 5, 'Resource_3': 5}
        patient.flow.append({'Department': 'Department_2', 'TimeStepAtDepartment': [], 'TimeStepTreated': []})
        resource_demand = patient.get_resource_demand()
        assert resource_demand == {'Stretcher': 1, 'Resource_4': 1, 'Resource_5': 5, 'Resource_6': 5}
        patient.flow.append({'Department': patient.EXIT, 'TimeStepAtDepartment': [], 'TimeStepTreated': []})
        resource_demand = patient.get_resource_demand()
        assert resource_demand == {}

    def test_update_stretcher_demand(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.update_stretcher_demand()
        assert patient.demand[0]['Stretcher'] == 1
        patient.flow[0]['TimeStepAtDepartment'] = [1]
        patient.update_stretcher_demand()
        assert patient.demand[0]['Stretcher'] == 0
        patient.flow.append({'Department': 'Department_2', 'TimeStepAtDepartment': [], 'TimeStepTreated': []})
        patient.update_stretcher_demand()
        assert patient.demand[1]['Stretcher'] == 1
        patient.flow[1]['TimeStepAtDepartment'] = [1]
        patient.update_stretcher_demand()
        assert patient.demand[1]['Stretcher'] == 0

    def test_get_current_department(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        current_department = patient.get_current_department()
        assert current_department == 'Department_1'
        patient.flow.append({'Department': 'Department_2', 'TimeStepAtDepartment': [], 'TimeStepTreated': []})
        current_department = patient.get_current_department()
        assert current_department == 'Department_2'
    
    def test_get_current_department_id(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        current_department_id = patient.get_current_department_id()
        assert current_department_id == 0
        patient.flow.append({'Department': 'Department_2', 'TimeStepAtDepartment': [], 'TimeStepTreated': []})
        current_department_id = patient.get_current_department_id()
        assert current_department_id == 1
    
    def test_get_current_length_of_treatment(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        current_length_of_treatment = patient.get_current_length_of_treatment()
        assert current_length_of_treatment == 0
        patient.flow[0]['TimeStepTreated'] = [0, 1, 2]
        current_length_of_treatment = patient.get_current_length_of_treatment()
        assert current_length_of_treatment == 3
        patient.flow.append({'Department': 'Department_2', 'TimeStepAtDepartment': [], 'TimeStepTreated': [0, 1, 2, 3]})
        current_length_of_treatment = patient.get_current_length_of_treatment()
        assert current_length_of_treatment == 4
    
    def test_update_once_met_demand(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.update(0)
        assert patient.flow[0]['TimeStepAtDepartment'] == [0]
        assert patient.flow[0]['TimeStepTreated'] == [0]
        assert patient.treated == True
        assert patient.alive == True
    
    def test_update_multiple_met_demand(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        for time_step in range(0, 5):
            patient.update(time_step)
        assert patient.flow[0]['TimeStepAtDepartment'] == list(range(0, 5))
        assert patient.flow[0]['TimeStepTreated'] == list(range(0, 5))
        assert patient.treated == True
        assert patient.alive == True
    
    def test_update_once_unmet_demand(self):
        random.seed(0)
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.demand_met[0]['Resource_1'] = 0.0
        patient.update(0)
        assert patient.flow[0]['TimeStepAtDepartment'] == [0]
        assert patient.flow[0]['TimeStepTreated'] == []
        assert patient.treated == False
        assert patient.mortality_rate == 1.2**10 * 0.01

        patient.demand_met[0]['Resource_3'] = 0.0
        patient.update(1)
        assert patient.flow[0]['TimeStepAtDepartment'] == [0, 1]
        assert patient.flow[0]['TimeStepTreated'] == []
        assert patient.length_of_stay == 8 * 1.5
        assert patient.treated == False
        assert patient.mortality_rate == 0.01

        patient.demand_met[0]['Resource_2'] = 0.0
        patient.update(2)
        assert patient.flow[0]['TimeStepAtDepartment'] == [0, 1, 2]
        assert patient.flow[0]['TimeStepTreated'] == []
        assert patient.treated == False
        assert patient.alive == False
        assert patient.mortality_rate == 1.0

    def test_update_once_unmet_demand_death_in_multiple_hours(self):
        random.seed(0)
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        for time_step in range(0, 8):
            patient.update(time_step)
        assert patient.get_current_department() == 'Department_2'
        patient.demand_met[1]['Resource_5'] = 0.0
        patient.update(8)
        assert patient.flow[1]['TimeStepAtDepartment'] == [8]
        assert patient.flow[1]['TimeStepTreated'] == []
        assert patient.treated == False
        assert patient.alive == True
        assert patient.mortality_rate == 0.0

        patient.demand_met[1]['Resource_5'] = 1.0
        patient.update(9)
        assert patient.flow[1]['TimeStepAtDepartment'] == [8, 9]
        assert patient.flow[1]['TimeStepTreated'] == [9]
        assert patient.treated == True
        assert patient.alive == True
        assert patient.mortality_rate == 0.0

        patient.demand_met[1]['Resource_5'] = 0.0
        patient.update(10)
        assert patient.flow[1]['TimeStepAtDepartment'] == [8, 9, 10]
        assert patient.flow[1]['TimeStepTreated'] == [9]
        assert patient.treated == False
        assert patient.alive == True
        assert patient.mortality_rate == 0.0

        patient.demand_met[1]['Resource_5'] = 0.0
        patient.update(11)
        assert patient.flow[1]['TimeStepAtDepartment'] == [8, 9, 10, 11]
        assert patient.flow[1]['TimeStepTreated'] == [9]
        assert patient.treated == False
        assert patient.alive == False
        assert patient.mortality_rate == 1.0
    
    def test_update_multiple_change_departments(self):
        random.seed(0)
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        for time_step in range(0, 15):
            patient.update(time_step)
        assert patient.flow[0]['TimeStepAtDepartment'] == list(range(0, 8))
        assert patient.flow[0]['TimeStepTreated'] == list(range(0, 8))
        assert patient.flow[1]['TimeStepAtDepartment'] == list(range(8, 13))
        assert patient.flow[1]['TimeStepTreated'] == list(range(8, 13))
        assert patient.get_current_department() == patient.EXIT 
        assert patient.flow[2]['TimeStepAtDepartment'] == list(range(13, 15))
        assert patient.flow[2]['TimeStepTreated'] == [13, 14]        
    
    # def test_update_multiple_single_department_too_long_untreated(self):
    #     patient = Patient.PatientType()
    #     patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)    
    #     for time_step in range(0, 11):
    #         patient.demand_met[0]['Resource_1'] = False  
    #         patient.update(time_step)
    #     assert patient.flow[0]['TimeStepAtDepartment'] == list(range(0, 10))
    #     assert patient.flow[0]['TimeStepTreated'] == []
    #     assert patient.get_current_department() == patient.EXIT 
    #     assert patient.treated == False
    #     assert patient.alive == False
    #     assert patient.mortality_rate == 1.0

    def test_update_multiple_time_steps_multiple_departments_single_unmet_demand(self):
        random.seed(0)
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        for time_step in range(0, 5):
            patient.demand_met[0]['Resource_1'] = 0.0
            patient.update(time_step)
        patient.demand_met[0]['Resource_1'] = 1.0
        for time_step in range(5, 20):
            patient.update(time_step)
        assert patient.flow[0]['TimeStepAtDepartment'] == list(range(0, 13))
        assert patient.flow[0]['TimeStepTreated'] == list(range(5, 13))
        assert patient.flow[1]['TimeStepAtDepartment'] == list(range(13, 18))
        assert patient.flow[1]['TimeStepTreated'] == list(range(13, 18))
        assert patient.out_of_hospital() == True
        assert patient.alive == True

    def test_update_once_multiple_unmet_demand(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.demand_met[0]['Resource_1'] = 0.0
        patient.demand_met[0]['Resource_2'] = 0.0
        patient.demand_met[0]['Resource_3'] = 0.0
        patient.update(0)
        assert patient.flow[0]['TimeStepAtDepartment'] == [0]
        assert patient.flow[0]['TimeStepTreated'] == []
        assert patient.treated == False
        assert patient.mortality_rate == 1.0
        assert patient.length_of_stay == 8 * 1.5        

    def test_update_exit(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.flow.append({'Department': patient.EXIT, 'TimeStepAtDepartment': [], 'TimeStepTreated': []})
        patient.update(0)
        assert patient.flow[0]['TimeStepAtDepartment'] == []
        assert patient.flow[0]['TimeStepTreated'] == []
        assert patient.treated == True
        assert patient.alive == True
    
    def test_set_current_baseline_mortality_rate(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.set_current_baseline_mortality_rate()
        assert patient.mortality_rate == 0.01
        patient.flow.append({'Department': 'Department_2', 'TimeStepAtDepartment': [], 'TimeStepTreated': []})
        patient.set_current_baseline_mortality_rate()
        assert patient.mortality_rate == 0.0
        patient.flow.append({'Department': patient.EXIT, 'TimeStepAtDepartment': [], 'TimeStepTreated': []})
        patient.set_current_baseline_mortality_rate()
        assert patient.mortality_rate == 0.0
    
    def test_check_consequences_of_unmet_demand(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.set_current_baseline_mortality_rate()
        patient.demand_met[0]['Resource_1'] = 0.9 # 90% of demand met so that only 1 "nurse" is missing
        patient.check_consequences_of_unmet_demand(time_step=0)
        assert patient.unmet_demand_info['Resource_1'] == [0]
        assert patient.mortality_rate == 0.01 * 1.2
        patient.mortality_rate = 0.01
        patient.demand_met[0]['Resource_1'] = 0.1 # 10% of demand met so that 9 "nurses" are missing
        patient.check_consequences_of_unmet_demand(time_step=0)
        assert patient.unmet_demand_info['Resource_1'] == [0, 0]
        assert patient.mortality_rate == 0.01 * (1.2**9)
        patient.demand_met[0]['Resource_2'] = 0.99 # random value below 1
        patient.check_consequences_of_unmet_demand(time_step=0)
        assert patient.unmet_demand_info['Resource_2'] == [0]
        assert patient.mortality_rate == 1.0
        patient.demand_met[0]['Resource_3'] = 0.8 # random value below 1
        patient.check_consequences_of_unmet_demand(time_step=0)
        assert patient.unmet_demand_info['Resource_3'] == [0]
        assert patient.length_of_stay == 8 * 1.5        
        patient.flow.append({'Department': 'Department_2', 'TimeStepAtDepartment': [], 'TimeStepTreated': []})
        patient.set_current_baseline_mortality_rate()
        patient.demand_met[1]['Resource_4'] = 0.5 # random value below 1
        patient.check_consequences_of_unmet_demand(time_step=0)
        assert patient.unmet_demand_info['Resource_4'] == [0]
        assert patient.mortality_rate == 0.0
        patient.demand_met[1]['Resource_5'] = 0.0 # random value below 1
        patient.check_consequences_of_unmet_demand(time_step=0)
        assert patient.mortality_rate == 0.0
        patient.check_consequences_of_unmet_demand(time_step=1)
        assert patient.mortality_rate == 1.0
        patient.check_consequences_of_unmet_demand(time_step=2)
        assert patient.mortality_rate == 1.0
        patient.demand_met[1]['Resource_6'] = 0.8 # random value below 1
        patient.check_consequences_of_unmet_demand(time_step=0)
        assert patient.length_of_stay == 5 * 1.2  
        patient.lengths_of_stay[1] = 5
        patient.demand_met[1]['Resource_6'] = 0.2 # random value below 1
        patient.check_consequences_of_unmet_demand(time_step=0)        
        assert patient.length_of_stay == 5 * 1.2**4

    def test_update_patient_status_when_demand_not_met(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.set_current_baseline_mortality_rate()
        patient.update_patient_status_when_demand_not_met('Resource_1', 0.5)
        assert patient.mortality_rate == 0.01 * (1.2**5)
        patient.mortality_rate = 0.01
        patient.update_patient_status_when_demand_not_met('Resource_2', 0.5)
        assert patient.mortality_rate == 0.01
        patient.unmet_demand_info['Resource_2'] = [0]
        patient.update_patient_status_when_demand_not_met('Resource_2', 0.5)
        assert patient.mortality_rate == 1.0
        patient.mortality_rate = 0.01
        patient.update_patient_status_when_demand_not_met('Resource_3', 0.5)
        assert patient.length_of_stay == 8 * 1.5
        patient.flow.append({'Department': 'Department_2', 'TimeStepAtDepartment': [], 'TimeStepTreated': []})
        patient.set_current_baseline_mortality_rate()
        patient.update_patient_status_when_demand_not_met('Resource_4', 0.5)
        assert patient.mortality_rate == 0.0
        patient.update_patient_status_when_demand_not_met('Resource_5', 0.5)
        assert patient.mortality_rate == 0.0
        patient.unmet_demand_info['Resource_5'] = [0]
        patient.update_patient_status_when_demand_not_met('Resource_5', 0.5)
        assert patient.mortality_rate == 0.0
        patient.unmet_demand_info['Resource_5'] = [0, 1]
        patient.update_patient_status_when_demand_not_met('Resource_5', 0.5)
        assert patient.mortality_rate == 1.0
        patient.unmet_demand_info['Resource_5'] = [0, 1, 2]
        patient.update_patient_status_when_demand_not_met('Resource_5', 0.5)
        assert patient.mortality_rate == 1.0
        patient.update_patient_status_when_demand_not_met('Resource_6', 0.5)
        assert patient.length_of_stay == 5 * 1.2**2.5

    def test_demand_unmet_too_long(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.unmet_demand_info['Resource_1'] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        assert patient.demand_unmet_too_long('Resource_1', 5) == True
        assert patient.demand_unmet_too_long('Resource_1', 11) == False
        patient.unmet_demand_info['Resource_2'] = [0, 2, 3, 4, 5, 6, 7, 8, 9]
        assert patient.demand_unmet_too_long('Resource_2', 8) == True
        assert patient.demand_unmet_too_long('Resource_2', 9) == False
    
    def test_update_patient_when_nurses_missing(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.set_current_baseline_mortality_rate()
        output = patient.update_patient_when_nurses_missing('Resource_1', 1.0, 0.5, patient.mortality_rate)
        assert output == 0.01
        output = patient.update_patient_when_nurses_missing('Resource_1', 1.2, 0.5, patient.mortality_rate)
        assert output == 0.01 * 1.2**5
        patient.mortality_rate = 0.01
        output = patient.update_patient_when_nurses_missing('Resource_1', 1.2, 1.0, patient.mortality_rate)
        assert output == 0.01
        output = patient.update_patient_when_nurses_missing('Resource_1', 0.9, 1.0, patient.mortality_rate)
        assert output == 0.01
    
    def test_patient_not_treated(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.patient_not_treated()
        assert patient.flow[0]['TimeStepAtDepartment'] == []
        assert patient.flow[0]['TimeStepTreated'] == []
        assert patient.treated == False
        patient.flow[0]['TimeStepAtDepartment'] = [0, 1, 2]
        patient.flow[0]['TimeStepTreated'] = [0, 1, 2]
        patient.patient_not_treated()
        assert patient.flow[0]['TimeStepAtDepartment'] == [0, 1, 2]
        assert patient.flow[0]['TimeStepTreated'] == [0, 1]
        assert patient.treated == False
    
    def test_update_unmet_demand_dict(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.update_unmet_demand_dict('Resource_1', 0)
        assert patient.unmet_demand_info['Resource_1'] == [0]
        patient.update_unmet_demand_dict('Resource_1', 5)
        assert patient.unmet_demand_info['Resource_1'] == [0, 5]

    def test_check_if_alive(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.mortality_rate = 0.0
        patient.check_if_alive()
        assert patient.alive == True
        patient.mortality_rate = 1.0
        patient.check_if_alive()
        assert patient.alive == False  

    def test_get_current_length_of_stay(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.flow[0]['TimeStepAtDepartment'] = [0, 1, 2]
        assert patient.get_current_length_of_stay() == 3
        patient.flow[0]['TimeStepAtDepartment'] = [0, 1, 2, 3, 4, 5]
        assert patient.get_current_length_of_stay() == 6
        patient.flow.append({'Department': 'Department_2', 'TimeStepAtDepartment': [3, 4], 'TimeStepTreated': [3]})
        assert patient.get_current_length_of_stay() == 2
        patient.flow.append({'Department': patient.EXIT, 'TimeStepAtDepartment': [5], 'TimeStepTreated': []})
        assert patient.get_current_length_of_stay() == 1

    # def test_patient_untreated_for_too_long(self):
    #     patient = Patient.PatientType()
    #     patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
    #     patient.flow[0]['TimeStepAtDepartment'] = [0, 1, 2, 3, 4, 5]
    #     patient.flow[0]['TimeStepTreated'] = [0, 1, 2, 3, 4, 5]
    #     assert patient.patient_untreated_for_too_long() == False      

    #     patient.flow[0]['TimeStepAtDepartment'] = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    #     patient.flow[0]['TimeStepTreated'] = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    #     assert patient.patient_untreated_for_too_long() == False  

    #     patient.flow[0]['TimeStepAtDepartment'] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    #     patient.flow[0]['TimeStepTreated'] = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    #     assert patient.patient_untreated_for_too_long() == True

    #     patient.flow[0]['TimeStepAtDepartment'] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    #     patient.flow[0]['TimeStepTreated'] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    #     assert patient.patient_untreated_for_too_long() == True

    #     patient.flow[0]['TimeStepAtDepartment'] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    #     patient.flow[0]['TimeStepTreated'] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    #     assert patient.patient_untreated_for_too_long() == True

    def test_resource_demand_met(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        assert patient.resource_demand_met() == True
        patient.demand_met[0]['Resource_1'] = False
        assert patient.resource_demand_met() == False
        patient.demand_met[0]['Resource_1'] = True
        assert patient.resource_demand_met() == True

    def test_update_resource_demand_met(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.update_resource_demand_met('Resource_1', 0.3)
        assert patient.demand_met[0]['Resource_1'] == 0.3
        assert patient.demand_met[0]['Resource_2'] == 1.0
        assert patient.demand_met[0]['Resource_3'] == 1.0
        patient.update_resource_demand_met('Resource_1', 0.7)
        assert patient.demand_met[0]['Resource_1'] == 0.7
        assert patient.demand_met[0]['Resource_2'] == 1.0
        assert patient.demand_met[0]['Resource_3'] == 1.0

        patient.flow.append({'Department': 'Department_2', 'TimeStepAtDepartment': [], 'TimeStepTreated': []})
        patient.update_resource_demand_met('Resource_4', 0.0)
        assert patient.demand_met[1]['Resource_4'] == 0.0
        assert patient.demand_met[1]['Resource_5'] == 1.0
        patient.update_resource_demand_met('Resource_4', 1.0)
        assert patient.demand_met[1]['Resource_4'] == 1.0
        assert patient.demand_met[1]['Resource_5'] == 1.0
    
    def test_set_all_demand_as_met(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.update_resource_demand_met('Resource_1', 0.5)
        patient.set_all_demand_as_met()
        assert patient.resource_demand_met() == 1.0

    def test_stay_finished(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        patient.flow[0]['TimeStepAtDepartment'] = [0, 1, 2, 3, 4, 5, 6, 7]
        patient.flow[0]['TimeStepTreated'] = [0, 1, 2, 3, 4, 5, 6, 7]
        patient.set_current_baseline_length_of_stay() 
        assert patient.stay_finished() == True
        patient.flow[0]['TimeStepAtDepartment'] = [0, 1, 2, 3, 4, 5, 6, 7]
        patient.flow[0]['TimeStepTreated'] = [0, 1, 2, 3, 4]
        patient.set_current_baseline_length_of_stay() 
        assert patient.stay_finished() == False
        patient.flow[0]['TimeStepAtDepartment'] = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        patient.flow[0]['TimeStepTreated'] = [0, 1, 2, 3, 4, 5]
        patient.flow.append({'Department': 'Department_2', 'TimeStepAtDepartment': [0, 1, 2, 3, 4, 5], 'TimeStepTreated': [0, 1, 2, 3, 4, 5]})
        patient.set_current_baseline_length_of_stay() 
        assert patient.stay_finished() == True
    
    def test_move_to_next_department(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        assert patient.get_current_department() == 'Department_1'
        patient.move_to_next_department()
        assert patient.get_current_department() == 'Department_2'
        assert patient.flow[-1]['TimeStepAtDepartment'] == []
        assert patient.flow[-1]['TimeStepTreated'] == []
        patient.move_to_next_department()
        assert patient.get_current_department() == patient.EXIT
        patient.move_to_next_department()
        assert patient.get_current_department() == patient.EXIT

    def test_out_of_hospital(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        assert patient.out_of_hospital() == False
        patient.move_to_next_department()
        assert patient.out_of_hospital() == False
        patient.move_to_next_department()
        assert patient.out_of_hospital() == True
    
    def test_has_demand(self):
        patient = Patient.PatientType()
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        assert patient.has_demand('Resource_1') == True
        assert patient.has_demand('Resource_9') == False
        self.PATIENT_PARAMETERS_SIMPLE[0]['Department_1']['ResourcesRequired'][0]['ResourceAmount'] = 0
        patient.set_parameters(self.PATIENT_NAME, self.PATIENT_PARAMETERS_SIMPLE)
        assert patient.has_demand('Resource_1') == False
