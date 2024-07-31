from abc import ABC, abstractmethod
import numpy as np
import math
import copy
from pyrecodes_hospitals import Component
from pyrecodes_hospitals import Patient

class ResilienceCalculator(ABC):

    @abstractmethod
    def calculate_resilience(self):
        pass

    @abstractmethod
    def update(self):
        pass

class FullRecoveryTimeResilienceCalculator(ResilienceCalculator):

    def calculate_resilience(self):
        return self.current_time_step

    def update(self, time_step: int) -> None:
        self.current_time_step = time_step

class ReCoDeSResilienceCalculator(ResilienceCalculator):
    
    def __init__(self, parameters: dict) -> None:   
        self.system_supply = {}
        self.system_demand = {}
        self.system_consumption = {}
        self.resources = parameters["Resources"]
        self.scope = parameters["Scope"]
        for resource_name in self.resources:
            self.system_supply[resource_name] = []
            self.system_demand[resource_name] = []
            self.system_consumption[resource_name] = []

    def calculate_resilience(self) -> dict:
        self.lack_of_resilience = dict()
        for resource_name in self.resources:
            self.lack_of_resilience[resource_name] = np.sum(
                np.asarray(self.system_demand[resource_name]) - np.asarray(self.system_consumption[resource_name]))
        return self.lack_of_resilience

    def update(self, resources: dict):
        for resource_name, resource_parameters in resources.items():
            if resource_name in self.resources:
                self.system_supply[resource_name].append(resource_parameters['DistributionModel'].get_total_supply(scope=self.scope))
                self.system_demand[resource_name].append(resource_parameters['DistributionModel'].get_total_demand(scope=self.scope))
                self.system_consumption[resource_name].append(
                    resource_parameters['DistributionModel'].get_total_consumption(scope=self.scope))

class NISTGoalsResilienceCalculator(ReCoDeSResilienceCalculator):

    def __init__(self, resilience_goals: list) -> None:
        self.set_resilience_goals(resilience_goals)

    def set_resilience_goals(self, resilience_goals: list):
        pass

    def update(self, resources: dict):
        # compare demand and consumption and check if the goal is met
        # if its met, save the time step in a bool list and then in the end in calculate resilience method get the first time step when the goal is met and maintained
        pass

    def calculate_resilience(self):
        pass

class PatientFlowCalculator(ReCoDeSResilienceCalculator):

    def component_in_scope(self, component: Component.Component) -> bool:
        if self.scope == ['All'] and component.name != 'EXIT':
            return True
        else:
            return component.name in self.scope

    def update(self, components: list) -> None:
        for patient_type in self.resources:
            self.system_consumption[patient_type].append(0)
            self.system_demand[patient_type].append(0)      
            self.system_supply[patient_type].append(0)
        for component in components:
            if self.component_in_scope(component):
                for patient in component.patients:  
                    if patient.name in self.resources:  
                        self.system_demand[patient.name][-1] += 1                  
                        if patient.treated:
                            self.system_consumption[patient.name][-1] += 1
                            self.system_supply[patient.name][-1] += 1 

class DeadPatientsCalculator(ResilienceCalculator):

    def __init__(self, parameters: dict) -> None:
        self.dead_patients = {}
        for patient_type in parameters['Resources']:
            self.dead_patients[patient_type] = []

    def update(self, components: list) -> None:
        for dead_patients in self.dead_patients.values():
            dead_patients.append(0)
        for component in components:
            for patient in component.patients:
                if patient.alive == False:
                    self.dead_patients[patient.name][-1] += 1
        
    def calculate_resilience(self):
        pass

class HospitalMeasureOfServiceCalculator(ResilienceCalculator):

    ONE_DAY = 24 # define what is 24h considering the time step used in the simulation
    OPERATING_THEATER_NAME = 'OperatingTheater'

    def __init__(self, parameters: dict) -> None:
        self.scope = parameters['Scope']
        self.resources = parameters['Resources']
        self.measures_of_service = {}

    def update(self, components: list):
        # TODO: Improve this. Components do not need to be assigned at every time step.
        self.components = components

    def calculate_resilience(self):
        self.measures_of_service['MortalityRateBefore24H'] = self.calculate_mortality_rate(self.components, time_interval=[0, self.ONE_DAY])
        self.measures_of_service['MortalityRateAfter24H'] = self.calculate_mortality_rate(self.components, time_interval=[self.ONE_DAY, math.inf])
        self.measures_of_service['AverageLengthOfStay'] = self.calculate_average_length_of_stay(self.components)
        surgeries_performed, surgeries_cancelled = self.calculate_surgical_volume(self.components)
        self.measures_of_service['SurgeriesPerformed'] = surgeries_performed
        self.measures_of_service['SurgeriesCancelled'] = surgeries_cancelled
        return self.measures_of_service
    
    def calculate_mortality_rate(self, components: list, time_interval: list) -> dict:
        baseline_mortality_rate = self.calculate_baseline_mortality_rate(components)
        real_mortality_rate = self.calculate_mortality_rate_based_on_dead_patients(components, time_interval)
        return max(baseline_mortality_rate, real_mortality_rate)

    def calculate_mortality_rate_based_on_dead_patients(self, components: list, time_interval: list) -> float:
        all_patients = self.collect_all_patients(components, time_interval)
        dead_patients_count = 0
        for patient in all_patients:
            if patient.alive == False: # self.patient_died_within_time_interval(patient, time_interval):
                # make sure that if the scope is a single component, the patient died in that component and not in others
                if patient.flow[-2]['Department'] in self.scope or self.scope == ['All']: 
                    dead_patients_count += 1
        total_number_of_patients = len(self.collect_all_patients(components, time_interval=[0, math.inf]))
        if total_number_of_patients == 0:
            return 0
        else:
            return dead_patients_count/total_number_of_patients
        
    def calculate_baseline_mortality_rate(self, components: list, time_interval=[0, math.inf]) -> float:
        all_patients = self.collect_all_patients(components, time_interval)
        if len(all_patients) == 0:
            # in some cases patients do not have the time to get to a department in the MCI simulation, 
            # so the baseline mortality rate is not registered 
            # this should fix it
            if len(self.scope) == 1 and len(self.resources) == 1 and self.scope != ['All'] and self.resources != ['All']:
                patient_profile = self.resources[0]
                department_name = self.scope[0]
                patient_info = components[0].patient_library[patient_profile]
                for department in patient_info:
                    if list(department.keys())[0] == department_name:
                        mortality_rate_per_time_step = list(department.values())[0]['BaselineMortalityRate']
                        length_of_stay = list(department.values())[0]['BaselineLengthOfStay']
                        if mortality_rate_per_time_step > 0:
                            return self.get_mortality_rate_during_entire_length_of_stay([mortality_rate_per_time_step for _ in range(length_of_stay)])
                else:
                    return 0
            else: 
                return 0
        else:
            baseline_mortality_rates = []
            last_mortality_rates_per_time_step = []
            for patient in all_patients:
                mortality_rates_per_time_step = self.get_mortality_rates_per_time_step_during_entire_length_of_stay(patient)
                if len(baseline_mortality_rates) > 0 and mortality_rates_per_time_step == last_mortality_rates_per_time_step:
                    baseline_mortality_rates.append(baseline_mortality_rates[-1])
                else:
                    baseline_mortality_rates.append(self.get_mortality_rate_during_entire_length_of_stay(mortality_rates_per_time_step))
                    last_mortality_rates_per_time_step = mortality_rates_per_time_step
            return np.mean(baseline_mortality_rates)
        
    def get_mortality_rates_per_time_step_during_entire_length_of_stay(self, patient: Patient.PatientType) -> list:
        if self.scope == ['All']:
            mortality_rates_per_time_step = []
            for mortality_rate, length_of_stay in zip(patient.mortality_rates, patient.lengths_of_stay):
                if mortality_rate > 0:
                    mortality_rates_per_time_step += [mortality_rate for _ in range(length_of_stay)]
        else:
            mortality_rates_per_time_step = []
            for department in self.scope:
                department_id = patient.departments.index(department)
                if patient.mortality_rates[department_id] > 0:
                    mortality_rates_per_time_step += [patient.mortality_rates[department_id] for _ in range(patient.lengths_of_stay[department_id])]
        return mortality_rates_per_time_step
    
    def get_mortality_rate_during_entire_length_of_stay(self, mortality_rates_per_time_step: list) -> float:   
        # Calculated as probability of a single link failing in a serial system and other links not failing
        total_prob_of_dying = 0
        for i, prob_of_dying_at_time_step in enumerate(mortality_rates_per_time_step):
            mortality_rate_at_other_time_steps = mortality_rates_per_time_step[:i] + mortality_rates_per_time_step[i+1:]
            nonmortality_rate_at_other_time_steps = np.subtract(1, mortality_rate_at_other_time_steps)
            prob_of_not_dying_at_other_time_steps = np.prod(nonmortality_rate_at_other_time_steps)
            total_prob_of_dying += prob_of_dying_at_time_step * prob_of_not_dying_at_other_time_steps
        return total_prob_of_dying
    
    def patient_type_considered(self, patient: Patient.PatientType) -> bool:
        if self.resources == ['All']:
            return True
        else:
            return patient.name in self.resources
    
    # def patient_died_within_time_interval(self, patient: Patient.PatientType, time_interval: list) -> bool:
    #     if patient.alive == False:
    #         if patient.flow[-1]['Department'] == patient.EXIT and len(patient.flow[-1]['TimeStepAtDepartment']) > 0: 
    #             return patient.flow[-1]['TimeStepAtDepartment'][0] < time_interval[1]
    #         else:
    #             return patient.flow[-2]['TimeStepAtDepartment'][-1] < time_interval[1]
    #     else:
    #         return False
        
    def calculate_average_length_of_stay(self, components: list) -> float:
        all_patients = self.collect_all_patients(components)
        length_of_stay = []
        for patient in all_patients:
            length_of_stay.append(self.calculate_length_of_stay(patient))
        if len(length_of_stay) == 0:
            return 0
        else:
            return np.mean(length_of_stay)
    
    def calculate_surgical_volume(self, components: list):
        if self.OPERATING_THEATER_NAME in self.scope or self.scope == ['All']:
            original_scope = copy.deepcopy(self.scope) # change the scope to only consider the operating theater
            self.scope = [self.OPERATING_THEATER_NAME]
            all_patients = self.collect_all_patients(components)
            self.scope = original_scope
        else:
            all_patients = []
        surgeries_performed = 0
        surgeries_cancelled = 0
        for patient in all_patients:
            for department_info in patient.flow:
                if department_info['Department'] == self.OPERATING_THEATER_NAME:
                    if len(department_info['TimeStepTreated']) == patient.lengths_of_stay[patient.flow.index(department_info)]:
                        surgeries_performed += 1
                    elif self.patient_exits_hospital(patient):
                        surgeries_cancelled += 1
                    break
        return surgeries_performed, surgeries_cancelled
    
    def patient_exits_hospital(self, patient: Patient.PatientType) -> bool:
        if patient.flow[-1]['Department'] == patient.EXIT and len(patient.flow[-1]['TimeStepAtDepartment']) > 0:
            return True
        else:
            return False

    def collect_all_patients(self, components: list, time_interval: list = [0, math.inf]) -> list:
        # Collect patients that are admitted to the hospital and whose length of stay is within the time interval
        all_patients = []
        for component in components:
            for patient in component.patients:
                if self.patient_type_considered(patient):
                    if self.scope == ['All']:
                        # if time_interval[0] <= patient.flow[0]['TimeStepAtDepartment'][0] < time_interval[1]:
                        if time_interval[0] <= self.calculate_length_of_stay(patient, scope=['All']) < time_interval[1]:
                            all_patients.append(patient)
                    else:
                        for department_info in patient.flow:
                            if department_info['Department'] in self.scope:
                                if len(department_info['TimeStepAtDepartment']) > 0:
                                    # if time_interval[0] <= patient.flow[0]['TimeStepAtDepartment'][0] < time_interval[1]:
                                    if time_interval[0] <= self.calculate_length_of_stay(patient, scope=['All']) < time_interval[1]:
                                        all_patients.append(patient)
                                    break                        
                     
        return all_patients
    
    def calculate_length_of_stay(self, patient: Patient.PatientType, scope=None) -> int:
        if scope is None:
            scope = self.scope
        length_of_stay = 0
        for department_info in patient.flow:
            if (department_info['Department'] in scope or scope == ['All']) and not(department_info['Department'] == patient.EXIT):
                length_of_stay += len(department_info['TimeStepAtDepartment'])
        return length_of_stay
    
class CauseOfDeathCalculator(HospitalMeasureOfServiceCalculator):

    """
    Calculate how many patients died due to a specific unmet resource demand.

    NOTE: List all patient types that are considered in the resources parameter in the system configuration file.
    """

    def calculate_resilience(self):
        if self.resources == ['All']:
            patient_types = list(self.components[0].patient_library.keys())
        else:
            patient_types = self.resources
            
        dead_patient_types_unmet_demand = {patient_type: [] for patient_type in patient_types}
        all_patients = self.collect_all_patients(self.components)
        for patient in all_patients:
            if patient.alive == False:
                dead_patient_types_unmet_demand[patient.name] += list(patient.unmet_demand_info.keys())
            
        self.unmet_demands_of_dead_patients = {patient_type: {} for patient_type in patient_types}
        
        for patient_type, unmet_demand_resources in dead_patient_types_unmet_demand.items():
            for unmet_demand_resource in unmet_demand_resources:
                if unmet_demand_resource in self.unmet_demands_of_dead_patients[patient_type]:
                    self.unmet_demands_of_dead_patients[patient_type][unmet_demand_resource] += 1
                else:
                    self.unmet_demands_of_dead_patients[patient_type][unmet_demand_resource] = 1
                    
        return self.unmet_demands_of_dead_patients
    



    