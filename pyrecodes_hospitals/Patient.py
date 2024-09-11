import random

class PatientType():
    """
    Class to represent a patient type that goes through the hospital and consumes resources.
    """

    EXIT = 'EXIT'
    STRETCHER_NAME = 'Stretcher'
    ONE_TIME_CONSUMABLES = ['Stretcher', 'MCI_Kit_NonWalking_EmergencyDepartment', 
                            'MCI_Kit_NonWalking_OperatingTheater', 'MCI_Kit_NonWalking_HighDependencyUnit',
                            'MCI_Kit_NonWalking_Medical/SurgicalDepartment', 'MCI_Kit_NonWalking_RestOfHospital',
                            'MCI_Kit_Walking_RestOfHospital', 'Blood']

    def set_parameters(self, patient_type_name, patient_type_parameters: list) -> None:
        self.name = patient_type_name
        self.set_demand(patient_type_parameters)
        self.set_departments(patient_type_parameters)
        self.set_mortality_rates(patient_type_parameters)
        self.set_lengths_of_stay(patient_type_parameters)
        self.flow = []        
        self.treated = False
        self.alive = True
        self.unmet_demand_info = {}
        self.mortality_rate_record = []
        self.set_initial_department()     
    
    def set_initial_department(self) -> None:
        self.flow.append({'Department': self.departments[0],
                         'TimeStepAtDepartment': [],
                         'TimeStepTreated': []})
        
    def set_demand(self, parameters: list) -> None:
        self.demand = []
        self.demand_met = []
        self.consequences_of_unmet_demand = []
        for department_dict in parameters:
            department_parameters = list(department_dict.values())[0]
            current_department_demand = {}
            current_department_demand_met = {}
            current_department_consequences = {}
            for resource_dict in department_parameters['ResourcesRequired']: 
                current_department_demand[resource_dict['ResourceName']] = resource_dict['ResourceAmount']
                current_department_demand_met[resource_dict['ResourceName']] = 1.0
                current_department_consequences[resource_dict['ResourceName']] = resource_dict['ConsequencesOfUnmetDemand']
            self.demand.append(current_department_demand)
            self.demand_met.append(current_department_demand_met)
            self.consequences_of_unmet_demand.append(current_department_consequences)

    def set_departments(self, parameters: list):
        self.departments = [list(department_dict.keys())[0] for department_dict in parameters]
    
    def set_mortality_rates(self, parameters: list):
        self.mortality_rates = [list(department_dict.values())[0]['BaselineMortalityRate'] for department_dict in parameters]

    def set_lengths_of_stay(self, parameters: list):
        self.lengths_of_stay = [list(department_dict.values())[0]['BaselineLengthOfStay'] for department_dict in parameters]
    
    def get_resource_demand(self) -> dict:
        if not(self.out_of_hospital()):
            self.update_consumable_demand()
            return self.demand[self.get_current_department_id()]
        else:
            return {}
    
    def update_consumable_demand(self) -> None:
        # Stretchers are only needed in the first time step of the patient's stay at the department.
        # Other consumables (MCI kits, blood) are also only consumed once.
        # If the patient is already at the department, then the patient has already been transferred to a bed and does not a stretcher.        
        if self.get_current_length_of_stay() > 0:
            for resource_name in self.demand[self.get_current_department_id()].keys():
                if resource_name in self.ONE_TIME_CONSUMABLES:
                    self.demand[self.get_current_department_id()][resource_name] = 0.0
    
    def get_current_department(self) -> str:
        return self.flow[-1]['Department']
    
    def get_current_department_id(self) -> int:
        return len(self.flow)-1
    
    def get_current_length_of_treatment(self) -> int:
        return len(self.flow[-1]['TimeStepTreated'])
    
    def update(self, time_step: int) -> None:
        self.flow[-1]['TimeStepAtDepartment'].append(time_step)
        self.treated = True
        self.flow[-1]['TimeStepTreated'].append(time_step)
        if not(self.out_of_hospital()):
            self.set_current_baseline_mortality_rate()   
            self.set_current_baseline_length_of_stay()     
            if not(self.resource_demand_met()):                            
                self.check_consequences_of_unmet_demand(time_step)
                # set all demand to met so that during resource distribution only unmet demand is set, as it is implemented now
                self.set_all_demand_as_met()
            self.check_if_alive()
            self.record_mortality_rate()
            if self.stay_finished():
                self.move_to_next_department()
         
    def set_current_baseline_mortality_rate(self) -> None:
        self.mortality_rate = self.mortality_rates[self.get_current_department_id()]
    
    def set_current_baseline_length_of_stay(self) -> None:
        self.length_of_stay = self.lengths_of_stay[self.get_current_department_id()]
    
    def check_consequences_of_unmet_demand(self, time_step: int) -> None:
        for resource_name, demand_met in self.demand_met[self.get_current_department_id()].items():
            if demand_met < 1.0:
                self.update_unmet_demand_dict(resource_name, time_step)
                self.update_patient_status_when_demand_not_met(resource_name, demand_met)
    
    def update_patient_status_when_demand_not_met(self, resource_name: str, demand_met: float) -> None:
        consequences = self.consequences_of_unmet_demand[self.get_current_department_id()][resource_name]
        for consequence in consequences:
            consequence_name, consequence_value = list(consequence.items())[0]
            if consequence_name == 'Mortality Rate Increase [per missing nurse]':
                updated_mortality_rate = self.update_patient_when_nurses_missing(resource_name, consequence_value, demand_met, self.mortality_rates[self.get_current_department_id()])
                self.mortality_rate = max(updated_mortality_rate, self.mortality_rate)
            elif consequence_name == 'Length Of Stay Extended [per missing nurse]':
                updated_length_of_stay = self.update_patient_when_nurses_missing(resource_name, consequence_value, demand_met, self.lengths_of_stay[self.get_current_department_id()])
                self.length_of_stay = max(self.length_of_stay, updated_length_of_stay)
            elif consequence_name == 'Mortality Rate Increase':
                updated_mortality_rate = consequence_value * self.mortality_rates[self.get_current_department_id()]
                self.mortality_rate = max(updated_mortality_rate, self.mortality_rate)
                self.patient_not_treated()
            elif consequence_name == 'Length Of Stay Extended':
                updated_length_of_stay = consequence_value * self.lengths_of_stay[self.get_current_department_id()]
                self.length_of_stay = max(self.length_of_stay, updated_length_of_stay)
                self.patient_not_treated()
            elif consequence_name == 'Death In [hours]':
                self.patient_not_treated()
                if self.demand_unmet_too_long(resource_name, consequence_value):
                    self.mortality_rate = 1.0
            elif consequence_name == 'None':
                pass
            else:
                raise ValueError(f'Consequence {consequence_name} is not implemented in the patient class.')
            
    def demand_unmet_too_long(self, resource_name: str, consequence_value: int) -> bool:
        unmet_demand_time_steps = self.unmet_demand_info.get(resource_name, [])
        if len(unmet_demand_time_steps) == 0:
            return False
        else:
            return self.length_of_last_n_elements_with_difference_one(unmet_demand_time_steps) >= consequence_value

    def length_of_last_n_elements_with_difference_one(self, list: list) -> int:
        if len(list) < 2:
            return 0
        
        count = 1
        for i in range(len(list) - 1, 0, -1):
            if abs(list[i] - list[i - 1]) == 1:
                count += 1
            else:
                break
        return count
    
    def update_patient_when_nurses_missing(self, resource_name: str, consequence_value: float, demand_met: float, parameter_to_update: float) -> None:
        # self.patient_not_treated() # too conservative to assume that if a single nurse is missing, the patient is not treated, the patient is treated but with increased mortality rate/length of stay
        nurse_demand = self.demand[self.get_current_department_id()][resource_name]
        if nurse_demand > 1:
            number_of_missing_nurses = nurse_demand * (1-demand_met)           
        else:            
            nurse_patient_ratio = 1/nurse_demand
            number_of_missing_nurses = nurse_patient_ratio * (1-demand_met)
        return parameter_to_update * max(consequence_value ** (number_of_missing_nurses), 1.0)
    
    def patient_not_treated(self) -> None:
        self.treated = False
        if len(self.flow[-1]['TimeStepTreated']) > 0:
            self.flow[-1]['TimeStepTreated'].pop()
    
    def update_unmet_demand_dict(self, resource_name: str, time_step: int) -> None:
        if resource_name in self.unmet_demand_info.keys():
            self.unmet_demand_info[resource_name].append(time_step)
        else:
            self.unmet_demand_info[resource_name] = [time_step]        

    def check_if_alive(self) -> None:
        random.seed(1)
        # check if patient is alive at each time step
        # by sampling from a uniform distribution and comparing to the mortality rate
        if random.random() < self.mortality_rate:
            self.alive = False
            self.flow.append({'Department': self.EXIT,
                        'TimeStepAtDepartment': [],
                        'TimeStepTreated': []})
            
    def record_mortality_rate(self) -> None:
        self.mortality_rate_record.append(self.mortality_rate)
            
    def get_current_length_of_stay(self):
        return len(self.flow[-1]['TimeStepAtDepartment'])
    
    def patient_untreated_for_too_long(self):
        return self.get_current_length_of_stay() >= self.length_of_stay
    
    def resource_demand_met(self) -> bool: 
        return all([demand_met == 1.0 for demand_met in self.demand_met[self.get_current_department_id()].values()])
    
    def update_resource_demand_met(self, resource_name: str, demand_met: float) -> None:
        if resource_name in self.demand_met[self.get_current_department_id()].keys():
            self.demand_met[self.get_current_department_id()][resource_name] = demand_met

    def set_all_demand_as_met(self) -> None:
        for resource_name in self.demand_met[self.get_current_department_id()].keys():
            self.demand_met[self.get_current_department_id()][resource_name] = 1.0

    def stay_finished(self) -> bool:
        return self.get_current_length_of_treatment() >= self.length_of_stay
    
    def move_to_next_department(self) -> None:
        next_department_id = self.get_current_department_id() + 1
        if next_department_id >= len(self.departments):
            next_department = self.EXIT
        else:
            next_department = self.departments[next_department_id]
        self.flow.append({'Department': next_department,
                          'TimeStepAtDepartment': [],
                          'TimeStepTreated': []})
    
    def out_of_hospital(self):
        return self.flow[-1]['Department'] == self.EXIT

    def has_demand(self, resource_name: str) -> bool:
        return self.get_resource_demand().get(resource_name, 0) > 0
            