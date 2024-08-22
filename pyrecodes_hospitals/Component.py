import math
from abc import ABC, abstractmethod
from enum import Enum
from pyrecodes_hospitals import ComponentRecoveryModel
from pyrecodes_hospitals import Resource
from pyrecodes_hospitals import Patient
import numpy as np
import json
import copy


class SupplyOrDemand(Enum):
    """
    Enum Class to specify the strings used for component's supply and demand parameters.
    """
    SUPPLY = 'supply'
    DEMAND = 'demand'

class Component(ABC):
    """
    Abstract Class to define the required methods and properties of a component.

    ...

    Attributes
    ----------
    name : str
        component's name
    functionality_level : float
        functionality level of a component at a time step of the recovery simulation
    functional : list([int])
        list contains time step of the recovery simulation at which a component is functional
    locality : list([int])
        locality id if the component is in a locality or a list of two locality id's if component is between the localities (i.e., link)
    supply : dict
        contains resources the component can supply to the system
    demand : dict
        contains resources the component demands from the system

    Methods
    -------
    form(component_name, component_parameters):
        forms the component by setting its name and parameters
    set_recovery_model()
        set component's recovery model
    set_initial_damage_level(damage_level):
        set component's initial damage level
    get_damage_level():
        get component's current damage level
    add_resources(supply_or_demand, resource_type, resource_parameters):
        add a resource to component's supply or demand
    update(time_step)
        update component's supply and demand values based on the current functionality level
    set_unmet_demand_for_recovery_activities(resource_name, percent_of_unmet_demand)
        set the percent of unmet demand for a resource required for a component's recovery activity as obtained from the resource distribution model
    recover()
        recover component as defined in its recovery model
    update_supply_based_on_unmet_demand(percent_of_met_demand)
        update component's supply of resources conditioned on how much of their resource demand is met at a time step of the recovery simulation
    set_locality(locality_id)
        set component's locality
    get_locality()
        get component's locality
    has_operation_demand()
        return True if a component has operation demand
    has_resource_supply(resource_name)
        return True if a component can supply a resource of resource_name    
    """
    name: str
    functionality_level: float 
    functional: list([int])  
    locality: list
    supply: dict
    demand: dict

    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def form(self, component_name: str, component_parameters: dict) -> None:
        pass

    @abstractmethod
    def set_recovery_model(self) -> None:
        pass

    @abstractmethod
    def set_initial_damage_level(self, damage_level: float) -> None:
        pass

    @abstractmethod
    def get_damage_level(self) -> float:
        pass

    @abstractmethod
    def add_resources(self, supply_or_demand: str, resource_type: str, resource_parameters: dict) -> None:
        pass

    @abstractmethod
    def update(self, time_step: int) -> None:
        pass

    # TODO: consider moving this to the recovery model
    @abstractmethod
    def set_unmet_demand_for_recovery_activities(self, resource_name: str, percent_of_met_demand: float) -> None:
        pass

    @abstractmethod
    def recover(self) -> None:
        pass

    @abstractmethod
    def update_supply_based_on_unmet_demand(self, resource_name: str, percent_of_met_demand: float) -> None:
        pass

    @abstractmethod
    def set_locality(self, locality_id: list) -> None:
        pass

    @abstractmethod
    def get_locality(self) -> int:
        pass

    @abstractmethod
    def has_operation_demand(self) -> bool:
        pass

    @abstractmethod
    def has_resource_supply(self, resource_name: str) -> bool:
        pass

class StandardiReCoDeSComponent(Component):
    """"
    Implementation of the Component abstract class to define standard functionality of a component in iRe-CoDeS.

    ...

    Attributes
    ----------
    ...as in abstract Component class

    Methods
    -------
    __init__()
        set functionality level of a component to 1 and initialize the "functional" time step list and supply and demand of a component as empty dicts
    __str__()
        define a string to describe a component in the print statement
    __eq__()
        define when two components are equal
    form(component_name, component_parameters)
        form a component by setting its recovery model, its resources and its name
    set_recovery_model(recovery_model_parameters)
        set component recovery model as defined in recovery_model_parameters
    set_resources(component_parameters)
        set component's supply and operation demand resources as defined in component_parameters
    set_initial_damage_level(damage_level)
        sets component's initial damage level
    get_initial_damage_level()
        get the component's current damage level from component's recovery model
    set_name(name)
        set component's name
    set_locality(locality_id)
        set component's locality 
    get_locality()
        get component's locality
    has_operation_demand()
        check whether component demands any resources to operate
    has_resource_supply(resource_name)
        check whether component has the resource resource_name in its supply attribute
    add_resources(supply_or_demand, type, resource_dict)
        add a resource to component's supply or demand as defined in the resource dict
    get_current_resource_amont(supply_or_demand, type, resource_name)
        get the current amount of a resource resource_name in component's supply or demand
        in case resource is not in component's supply or demand, returns 0
    update(time_step)
        update component's state by updating its functionality, supply and demand properties at a time step of the recovery simulation
    update_functionality()
        update component's functionality at a time step based on its current damage level and damage-to-functionality relation
    check_if_functional(time_step)
        check if a component is functional at time_step and add to the component's attribute "functional" list
        a component is considered functional if its functionality level is higher than 0
    update_resources_based_on_component_functionality(supply_or_demand, type)
        update component's resource supply or demand based on its current functionality level
    update_supply_based_on_component_functionality()
        update component's resource supply based on its current functionality level
    update_operation_demand()
        update component's resource operation demand based on its current functionality level
    update_recovery_demand()
        update component's resource recovery demand based on its currentyl active recovery activities
    set_recovery_model_activities_demand_to_met()
        set the demand of all component's recovery activities as met.
        this is done at each time step before distributing resources, since resource distribution assumes 
        that before the distribution is simulated all demand is met - BETTER EXPLANATION?
    update_supply_based_on_unmet_demand(percent_of_met_demand)
        update component's supply based on how much of its operation demand is met
        this is how component interdependencies are captured
        this method is called once the resource distribution is performed at a time step
    set_unmet_demand_for_recovery_activities(resource_name, percent_of_met_demand)
        update the component's percent of met demand for recovery activity taht requires the resource resource_name
        this is how recovery resource constraints are captured
        this method is called once the resource distribution is performed at a time step
    recover(time_step)
        recover the component by increasing the level of completion of its recovery activities conditioned on their met resource demand 
    
    """
    class SupplyTypes(Enum):
        """
        Enum Class to specify the strings used for component's supply types.
        Only one supply type is currently considered in pyrecodes.
        """
        SUPPLY = 'Supply'

    class DemandTypes(Enum):
        """
        Enum Class to specify the strings used for component's demand types.
        Two demand types are currently considered in pyrecodes: operation and recovery demand.
        """
        OPERATION_DEMAND = 'OperationDemand'
        RECOVERY_DEMAND = 'RecoveryDemand'

    def __init__(self) -> None:
        self.functionality_level = 1.0
        self.functional = []
        self.supply = {supply_type.value: dict() for supply_type in self.SupplyTypes}
        self.demand = {demand_type.value: dict() for demand_type in self.DemandTypes}

    def __str__(self) -> str:
        return f'{self.name} | Locality: {self.locality}'

    def __eq__(self, other) -> bool:
        check_list = []
        attributes_to_check = ['name', 'locality', 'functionality_level', 'supply', 'demand']
        for attribute_to_check in attributes_to_check:
            check_list.append(getattr(self, attribute_to_check) == getattr(other, attribute_to_check))
        return all(check_list)
    
    # TODO: consider moving this into a component constructor class!
    def form(self, component_name: str, component_parameters: dict) -> None:
        self.set_recovery_model(component_parameters['RecoveryModel'])
        self.set_resources(component_parameters)
        self.set_name(component_name)

    def set_recovery_model(self, recovery_model_parameters: dict) -> None:
        target_recovery_model = getattr(ComponentRecoveryModel, recovery_model_parameters['Type'])
        self.recovery_model = target_recovery_model()
        self.recovery_model.set_parameters(recovery_model_parameters['Parameters'])
        self.recovery_model.set_damage_functionality(recovery_model_parameters['DamageFunctionalityRelation'])
    
    def set_resources(self, component_parameters: dict) -> None:
        self.add_resources(SupplyOrDemand.SUPPLY.value,
                                self.SupplyTypes.SUPPLY.value,
                                component_parameters.get('Supply', {}))
                             
        self.add_resources(SupplyOrDemand.DEMAND.value,
                                self.DemandTypes.OPERATION_DEMAND.value,
                                component_parameters.get('OperationDemand', {}))                         

    def set_initial_damage_level(self, damage_level) -> None:
        self.recovery_model.set_initial_damage_level(damage_level)

    def get_damage_level(self) -> float:
        return self.recovery_model.get_damage_level()

    def set_name(self, name: str) -> None:
        self.name = name

    def set_locality(self, locality_id: list([int])) -> None:
        self.locality = locality_id

    def get_locality(self) -> list:
        return self.locality

    def has_operation_demand(self) -> bool:
        return len(self.demand[self.DemandTypes.OPERATION_DEMAND.value]) > 0

    def has_resource_supply(self, resource_name: str) -> bool:
        return resource_name in list(self.supply[self.SupplyTypes.SUPPLY.value].keys())

    def add_resources(self, supply_or_demand: str, type: str, resource_dict: dict) -> None:
        place_to_add = getattr(self, supply_or_demand)[type]
        for resource_name, resource_parameters in resource_dict.items():
            target_class = getattr(Resource, resource_parameters.get('ResourceClassName', 'ConcreteResource'))
            resource = target_class(resource_name, resource_parameters)
            place_to_add[resource_name] = resource
    
    def get_current_resource_amount(self, supply_or_demand: str, type: str, resource_name: str) -> float:
        resource = getattr(self, supply_or_demand)[type].get(resource_name, None)
        if not (resource is None):
            return resource.current_amount
        else:
            return 0.0

    def update(self, time_step: int) -> None:
        self.update_functionality()
        self.check_if_functional(time_step)
        self.update_supply_based_on_component_functionality()
        self.update_operation_demand()
        self.update_recovery_demand()

    def update_functionality(self) -> None:
        self.functionality_level = self.recovery_model.get_functionality_level()
        
    def check_if_functional(self, time_step: int) -> None:
        if self.functionality_level > 0:
            self.functional.append(time_step)

    def update_resources_based_on_component_functionality(self, supply_or_demand: str, type: str) -> None:
        resources_to_update = getattr(self, supply_or_demand)[type]
        for resource_object in resources_to_update.values():
            resource_object.update_based_on_component_functionality(self.functionality_level)

    def update_supply_based_on_component_functionality(self):
        self.update_resources_based_on_component_functionality(SupplyOrDemand.SUPPLY.value,
                                                               self.SupplyTypes.SUPPLY.value)

    def update_operation_demand(self):
        self.update_resources_based_on_component_functionality(SupplyOrDemand.DEMAND.value,
                                                               self.DemandTypes.OPERATION_DEMAND.value)

    def update_recovery_demand(self):
        self.set_recovery_model_activities_demand_to_met()
        self.demand[self.DemandTypes.RECOVERY_DEMAND.value] = self.recovery_model.get_demand()

    def set_recovery_model_activities_demand_to_met(self):
        self.recovery_model.set_activities_demand_to_met()

    def update_supply_based_on_unmet_demand(self, resource_name: str, percent_of_met_demand: float) -> None:
        resources_to_update = getattr(self, SupplyOrDemand.SUPPLY.value)[self.SupplyTypes.SUPPLY.value] 
        for resource_object in resources_to_update.values():
            resource_object.update_based_on_unmet_demand(resource_name, percent_of_met_demand)   
    
    def set_unmet_demand_for_recovery_activities(self, resource_name: str, percent_of_met_demand: float) -> None:
        self.recovery_model.set_unmet_demand_for_recovery_activities(resource_name,
                                                                     percent_of_met_demand)  # two recovery activities CANNOT ask for the same resource!

    def recover(self, time_step: int):
        self.recovery_model.recover(time_step)

class BuildingStockUnitWithEmergencyCalls(StandardiReCoDeSComponent):
    """
    Subclass of the StandardiReCoDeSComponent class that simulates the performance of building stock units 
    with increased post-disaster demand for communication services due to emergency calls.

    ...

    Attributes
    ----------
    (only subclass specific)

    COMMUNICATION_RESOURCE_NAME : str
        define the name of the communication resource in the system class 
        the demand for this resource will increase after a disaster
    COMMUNICATION_DEMAND_MULTIPLIER : float
        defines by how much the pre-disaster demand for the communication resource 
        is increased after a disaster
    COMMUNICATION_DEMAND_INCREASE_TIME_STEP : int
        define at which time step of the recovery simulation will the demand for communication resource increase
        note: this time step should be after the DISASTER_TIME_STEP defined in the system configuration file
    COMMUNICATION_DEMAND_EXP_DECREASE_COEFF : float
        define the parameter of the exponential function that simulates the post-disaster decrease of the
        demand for communication resource following the initial demand surge   
    

    Methods
    -------
    (only subclass specific)

    update(time_step)
        | *extend parent method*
        | update the demand for communication services conditioned on the current time step
    update_communication_demand(time_step)
        | calculate the communication resource demand at the current time step
        | and update in component's operation demand
    modify_emergency_calls_demand(initial_communication_demand, time_step)
        | based on the current time step, the exponential function parameters and initial communication demand
        | calculate the current demand for communication resource which cannot be smaller than
        | the initial, pre-disaster, demand
    add_resources(supply_or_demand, type, resource_dict)
        | *override parent method*
        | while adding resources check if a resource is a communication resource
        | if yes, set the COMMUNICATION_RESOURCE_NAME attribute  
    check_if_demand_increase_considered(resource_name, resource_parameters)
        | check if the resource demand should be increased following the disaster as specified for the communication resource,
        | a communication resource parameters dict in ComponentLibrary should have the 'PostDisasterIncreaseDueToEmergencyCalls' key with a 'True' value
    """

    COMMUNICATION_DEMAND_MULTIPLIER = 10.0
    COMMUNICATION_DEMAND_INCREASE_TIME_STEP = 1
    COMMUNICATION_DEMAND_EXP_DECREASE_COEFF = -0.3

    def update(self, time_step: int):
        super().update(time_step)
        self.update_communication_demand(time_step)

    def update_communication_demand(self, time_step: int):
        communication_resource_object = \
            getattr(self, SupplyOrDemand.DEMAND.value)[self.DemandTypes.OPERATION_DEMAND.value][
                self.COMMUNICATION_RESOURCE_NAME]
        current_communication_demand = communication_resource_object.current_amount
        initial_communication_demand = communication_resource_object.initial_amount
        if time_step >= self.COMMUNICATION_DEMAND_INCREASE_TIME_STEP:
            current_communication_demand = self.modify_emergency_calls_demand(initial_communication_demand, time_step)
        communication_resource_object.set_current_amount(current_communication_demand)

    def modify_emergency_calls_demand(self, initial_communication_demand: float, time_step: int) -> float:
        modified_communication_demand = (
                                                initial_communication_demand * self.COMMUNICATION_DEMAND_MULTIPLIER) * math.exp(
            self.COMMUNICATION_DEMAND_EXP_DECREASE_COEFF) ** (time_step - self.COMMUNICATION_DEMAND_INCREASE_TIME_STEP)
        if modified_communication_demand < initial_communication_demand:
            return initial_communication_demand
        else:
            return modified_communication_demand
    
    def add_resources(self, supply_or_demand: str, type: str, resource_dict: dict):
        place_to_add = getattr(self, supply_or_demand)[type]
        for resource_name, resource_parameters in resource_dict.items():
            self.check_if_demand_increase_considered(resource_name, resource_parameters)
            resource = Resource.ConcreteResource(resource_name, resource_parameters)
            place_to_add[resource_name] = resource
    
    def check_if_demand_increase_considered(self, resource_name: str, resource_parameters: dict) -> None:
        if resource_parameters.get('PostDisasterIncreaseDueToEmergencyCalls', None) == "True":
            self.COMMUNICATION_RESOURCE_NAME = resource_name

class InfrastructureInterface(StandardiReCoDeSComponent):
    """
    Subclass of the StandardiReCoDeSComponent class used to interface third-party infrastructure simulators into an iRe-CoDeS system-of-systems model.
    Infrastructure simulator outputs are defined in the system configuration file.
    
    ...
 

    Methods
    -------
    (only subclass specific)

    update(time_step)
        | *extend parent method*
        | update the demand for communication services conditioned on the current time step
    update_communication_demand(time_step)
        | calculate the communication resource demand at the current time step
        | and update in component's operation demand
    modify_emergency_calls_demand(initial_communication_demand, time_step)
        | based on the current time step, the exponential function parameters and initial communication demand
        | calculate the current demand for communication resource which cannot be smaller than
        | the initial, pre-disaster, demand
    add_resources(supply_or_demand, type, resource_dict)
        | *override parent method*
        | while adding resources check if a resource is a communication resource
        | if yes, set the COMMUNICATION_RESOURCE_NAME attribute  
    check_if_communication_resource(resource_name, resource_parameters)
        | check if a resource is a communication resource, as specified in the system configuration file
        | a communication resource parameters dict should have the 'IsCommunicationResource' key with a 'True' value
    """

    def set_recovery_model(self, recovery_model_parameters: dict) -> None:
        target_recovery_model = getattr(ComponentRecoveryModel, 
                                        recovery_model_parameters['Type'])
        self.recovery_model = target_recovery_model()
        self.recovery_model.set_damage_functionality()
    
    def set_supply_dynamics(self, supply_dynamics: dict) -> None:   
        restoration_times = [list(current_dict.values())[-1]['Value'] for current_dict in supply_dynamics['RestoredIn']]     
        step_limits = list(np.divide(restoration_times, restoration_times[-1]))
        step_values = list(np.divide(supply_dynamics['Amount'], max(supply_dynamics['Amount'])))   
        if step_limits[0] != 0.0:
            step_values = [0] + step_values
        else:
            step_values = [step_values[0]] + step_values

        self.recovery_model.set_parameters({'RestoredIn': supply_dynamics['RestoredIn'],
                                            'StepLimits': step_limits,
                                            'StepValues': step_values})
        self.supply['Supply'][supply_dynamics['Resource']].set_initial_amount(max(supply_dynamics['Amount']))

class HospitalComponent(StandardiReCoDeSComponent):
    """
    Class to implement components of a hospital system.

    Attributes
    ----------
    ...only subclass specific

    predefined_resource_dynamics

    Methods
    -------
    ...only subclass specific

    set_predefined_resource_dynamics

    update_resources_based_on_predefined_resource_dynamics

    get_resource_amount_based_on_time_step

    update_supply_based_on_consumption
    """

    PRIORITIZED_PATIENTS_LIST = ['Red', 'Yellow', 'Green', 'Rest'] # last element is for patients that do not have a triage category and must be in the list to avoid errors

    def __init__(self) -> None:
        super().__init__()
        self.predefined_resource_dynamics = []
        self.patients = []
    
    def set_predefined_resource_dynamics(self, resource_dynamics: list): 
        self.predefined_resource_dynamics = resource_dynamics    

    def update(self, time_step: int, system_consumption: dict) -> None:
        super().update(time_step)
        self.update_resources_based_on_predefined_resource_dynamics(time_step)   
        self.update_supply_based_on_consumption(system_consumption)   
        self.update_operation_demand_based_on_patients()  
        
    def update_resources_based_on_predefined_resource_dynamics(self, time_step: int) -> None:
        """
        Note that the predefined resoruce dynamics changes the intial resource amount.
        """
        for resource_dynamic in self.predefined_resource_dynamics:
            new_amount = self.get_resource_amount_based_on_time_step(resource_dynamic, time_step)
            if new_amount is not None:
                resource_to_change = getattr(self, resource_dynamic['SupplyOrDemand'])[resource_dynamic['SupplyOrDemandType']][resource_dynamic['Resource']]
                resource_to_change.set_initial_amount(new_amount)
    
    def get_resource_amount_based_on_time_step(self, resource_dynamic: dict, time_step: int) -> None:   
        # this method is used for supply increase (consider renaming it to reflect that!)
        # take current supply and increase the amount based on resource dynamics  
        # different for patient source component   
        if time_step in resource_dynamic['AtTimeStep']:
            amount_id = [i for i, value in enumerate(resource_dynamic['AtTimeStep']) if value == time_step]
            current_amount = getattr(self, resource_dynamic['SupplyOrDemand'])[resource_dynamic['SupplyOrDemandType']][resource_dynamic['Resource']].current_amount
            return resource_dynamic['Amount'][amount_id[0]] + current_amount
        else:
            return None
    
    def update_supply_based_on_consumption(self, system_consumption: dict) -> None:
        """
        Decrease supply of consumable resources based on the consumption. 
        Takes the last value of the system_consumption dict as the current consumption.
        """
        for resource_name, resource in self.supply['Supply'].items():
            if isinstance(resource, Resource.ConsumableResource) and len(system_consumption[resource_name]) > 0:
                resource.update_supply_based_on_consumption(system_consumption[resource_name][-1])
    
    def update_operation_demand_based_on_patients(self):
        operation_demand = {}
        for patient in self.patients:
            patient_resource_demand = patient.get_resource_demand()
            for key, value in patient_resource_demand.items():
                if key in operation_demand:
                    operation_demand[key] += value
                else:
                    operation_demand[key] = value
        self.set_current_operation_demand(operation_demand)
    
    def set_current_operation_demand(self, operation_demand: dict) -> None:
        """
        Current operation demand is the sum of patient demands and the base demand of the component.
        """
        for resource_name, resource_object in self.demand[self.DemandTypes.OPERATION_DEMAND.value].items():
            base_demand = resource_object.initial_amount
            current_amount = operation_demand.get(resource_name, 0)
            resource_object.set_current_amount(current_amount + base_demand)
            if resource_name in operation_demand:
                operation_demand.pop(resource_name)
        if len(operation_demand) > 0:
            raise ValueError(f'Not all resources needed for a patient are considered in component {self.name}. Please add the following in the component library dict: {list(operation_demand.keys())}')
    
    def update_supply_based_on_unmet_demand(self, resource_name: str, percent_of_met_demand: float) -> None:
        super().update_supply_based_on_unmet_demand(resource_name, percent_of_met_demand)
        self.update_patients_based_on_unmet_demand(resource_name, percent_of_met_demand)
    
    def update_patients_based_on_unmet_demand(self, resource_name: str, percent_of_met_demand: float) -> None:
        """
        Define the number of patients with met demand - prioritization on first-come first-served basis.
        """
        patients_with_demand = self.get_patients_with_demand(resource_name)
        if resource_name == 'Nurse':
            self.distribute_resource_among_patients_evenly(resource_name, percent_of_met_demand, patients_with_demand)
        else:
            self.distribute_resource_among_patients_priority(resource_name, percent_of_met_demand, patients_with_demand)
    
    def distribute_resource_among_patients_priority(self, resource_name: str, percent_of_met_demand: float, patients_with_demand: list) -> None:
        number_of_patients_with_met_demand = int(len(patients_with_demand) * percent_of_met_demand)
        patients_with_demand = self.prioritize_patients(patients_with_demand)
        for i, patient in enumerate(patients_with_demand):
            if i >= number_of_patients_with_met_demand:
                patient.update_resource_demand_met(resource_name, 0.0) 
    
    def prioritize_patients(self, patients_with_demand: list) -> list:
        # Prioritization of patients based on the patient triage category
        # The order of the categories is defined in the PRIORITIZED_PATIENTS_LIST
        
        categorized_patients = {category: [] for category in self.PRIORITIZED_PATIENTS_LIST}
        for patient in patients_with_demand:
            for category in self.PRIORITIZED_PATIENTS_LIST:
                if category in patient.name:
                    categorized_patients[category].append(patient)
                    break
            else:
                categorized_patients[category].append(patient)
        
        prioritized_patients = []
        for category in self.PRIORITIZED_PATIENTS_LIST:
            prioritized_patients += categorized_patients[category]
        return prioritized_patients
    
    def distribute_resource_among_patients_evenly(self, resource_name: str, percent_of_met_demand: float, patients_with_demand: list) -> None:
        for patient in patients_with_demand:
            patient.update_resource_demand_met(resource_name, percent_of_met_demand)

    def get_patients_with_demand(self, resource_name: str) -> list:
        patients_with_demand = []
        for patient in self.patients:
            if patient.has_demand(resource_name):
                patients_with_demand.append(patient)
        return patients_with_demand      

    def update_patient_status(self, time_step: int) -> None:
        for patient in self.patients:
            patient.update(time_step)

    def get_patients_that_move(self) -> list:
        patients_that_move = []
        for patient in self.patients:
            if not(self.patient_in_component(patient)):
                patients_that_move.append(patient)
        self.patients = [patient for patient in self.patients if patient not in patients_that_move]
        return patients_that_move

    def set_new_patients(self, patients_that_move: list):
        for patient in patients_that_move:
            if self.patient_in_component(patient):
                self.patients.append(patient)

    def patient_in_component(self, patient: Patient.PatientType) -> bool:
        return patient.get_current_department() == self.name

class PatientSource(HospitalComponent):
    """
    Class to create patients.
    """

    def form(self, component_name: str, component_parameters: dict) -> None:
        super().form(component_name, component_parameters)
        self.set_patient_library(component_parameters['PatientLibrary'])

    def set_patient_library(self, patient_library_file: str) -> None:
        with open(patient_library_file, 'r') as file:
            self.patient_library = json.load(file)
    
    def update(self, time_step: int, system_consumption: float) -> None:
        pass

    def get_resource_amount_based_on_time_step(self, resource_dynamic: dict, time_step: int) -> None:  
        # This method is different for patient source, as setting patients based on resource dynamics works different than setting resource supply 
        amount_id = [i for i, value in enumerate(resource_dynamic['AtTimeStep']) if value == time_step]
        if len(amount_id) == 0:
            return 0
        else:
            return resource_dynamic['Amount'][amount_id[0]]  
    
    def create_patients(self, time_step: int) -> None:
        self.update_resources_based_on_predefined_resource_dynamics(time_step)
        for patient_type_name, patient_group_parameters in self.demand['OperationDemand'].items():
            patient = Patient.PatientType()
            number_of_patients = patient_group_parameters.initial_amount
            patient.set_parameters(patient_type_name, self.patient_library[patient_type_name])
            self.patients += [copy.deepcopy(patient) for _ in range(number_of_patients)]
