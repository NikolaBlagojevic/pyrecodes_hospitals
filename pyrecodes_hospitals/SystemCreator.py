from abc import ABC, abstractmethod
from pyrecodes_hospitals import Component
from pyrecodes_hospitals import ComponentLibraryCreator
from pyrecodes_hospitals import ResourceDistributionModel
from pyrecodes_hospitals import ResilienceCalculator
import json
import copy
import math

class SystemCreator(ABC):
    """
    Abstract class for creating a System from a file
    """

    @abstractmethod
    def setup(self, component_library: ComponentLibraryCreator.ComponentLibraryCreator, file_name: str) -> None:
        pass

    @abstractmethod
    def read_file(self, file_name: str) -> None:
        pass

    @abstractmethod
    def set_component_library(self, component_library: dict) -> None:
        pass

    @abstractmethod
    def create_components(self) -> list([Component.Component]):
        pass

    @abstractmethod
    def get_damage_input_type(self) -> str:
        pass

    @abstractmethod
    def get_damage_input_parameters(self) -> dict:
        pass

    @abstractmethod
    def get_resource_distribution_parameters(self) -> dict:
        pass

    @abstractmethod
    def get_resilience_calculators(self) -> list([dict]):
        pass

class ConcreteSystemCreator(SystemCreator):
    """
    Class that implements methods common to all SystemCreator subclasses.
    """

    def setup(self, component_library: dict, file_name: str) -> None:
        self.set_component_library(component_library)
        self.read_file(file_name)
        self.set_constants()
    
    def set_component_library(self, component_library: dict) -> None:
        self.component_library = component_library

    def read_file(self, file_name: str) -> None:
        with open(file_name, 'r') as file:
            self.system_configuration_file = json.load(file)
    
    def set_constants(self) -> None:
        for constant_label, constant_value in self.system_configuration_file['Constants'].items():
            setattr(self, constant_label, constant_value)
    
    def get_damage_input_type(self) -> str:
        return self.system_configuration_file['DamageInput']['Type']

    def get_damage_input_parameters(self) -> dict:
        return self.system_configuration_file['DamageInput']['Parameters']

    def get_resource_distribution_parameters(self) -> dict:
        return self.system_configuration_file['Resources']
    
    def get_resource_parameters(self, components) -> dict:
        all_resources_parameters = self.get_resource_distribution_parameters()
        transfer_services = self.get_transfer_services(components, all_resources_parameters)
        non_transfer_services = self.get_non_transfer_services(components, all_resources_parameters, transfer_services)
        return {**transfer_services, **non_transfer_services}
    
    def get_transfer_services(self, components, all_resources_parameters) -> dict:
        resources = dict()
        for resource_name, resource_parameters in all_resources_parameters.items():
            if resource_parameters['Group'] == 'TransferService':
                resources[resource_name] = dict()        
                target_distribution_model = getattr(ResourceDistributionModel, resource_parameters['DistributionModel']['Type'])
                resources[resource_name]['Group'] = resource_parameters['Group']
                resources[resource_name]['DistributionModel'] = target_distribution_model(resource_name, 
                                                                                        resource_parameters['DistributionModel']['Parameters'],
                                                                                        components)
        return resources
    
    def get_non_transfer_services(self, components, all_resources_parameters, transfer_services: dict) -> dict:
        resources = {}
        for resource_name, resource_parameters in all_resources_parameters.items():
            if resource_parameters['Group'] != 'TransferService':
                resources[resource_name] = dict()        
                target_distribution_model = getattr(ResourceDistributionModel, resource_parameters['DistributionModel']['Type'])
                resources[resource_name]['Group'] = resource_parameters['Group']
                resources[resource_name]['DistributionModel'] = target_distribution_model(resource_name, 
                                                                                        resource_parameters['DistributionModel']['Parameters'],
                                                                                        components)
                required_transfer_service = resource_parameters['DistributionModel']['Parameters']['TransferService']
                if len(required_transfer_service) > 0: 
                    resources[resource_name]['DistributionModel'].transfer_service_distribution_model = transfer_services[required_transfer_service]['DistributionModel']
        return resources
    
    def get_resilience_calculators(self) -> list([ResilienceCalculator.ResilienceCalculator]):
        resilience_calculators = []
        for resilience_calculator_parameters in self.system_configuration_file['ResilienceCalculator']:
            target_resilience_calculator = getattr(ResilienceCalculator, resilience_calculator_parameters['Type'])
            resilience_calculators.append(target_resilience_calculator(resilience_calculator_parameters['Parameters']))
        return resilience_calculators
    
    def create_components(self) -> list([Component.Component]):
        self.components = []
        for locality, content in self.system_configuration_file["Content"].items():
            self.create_components_in_localities(locality, content.get('ComponentsInLocality', {}))
            self.create_components_between_localities(locality, content.get('LinkTo', ()))
        return self.components
    
    def create_components_in_localities(self, locality: str, content: dict) -> None:
        """
        Implemented by subclasses.
        """
        pass

    def create_components_between_localities(self, locality: str, content: dict) -> None:
        """
        Implemented by subclasses.
        """
        pass

    def get_component_object(self, component_type: str) -> Component.Component:
        return copy.deepcopy(self.component_library[component_type])

    def add_component(self, component_object: Component.Component) -> None:
        self.components.append(copy.deepcopy(component_object))
    
    @staticmethod
    def format_locality_id(locality_string) -> int:
        return int(locality_string.split(' ')[-1])   

class JSONSystemCreator(ConcreteSystemCreator):
    """
    Create a System from a JSON file.
    """

    components: list([Component])

    def __init__(self) -> None:
        self.components = []

    def create_components_in_localities(self, locality: str, content: dict) -> None:
        for component_type, amount in content.items():
            component_object = self.get_component_object(component_type)
            component_object.set_locality([self.format_locality_id(locality)])
            for _ in range(amount):
                self.add_component(component_object)

    def create_components_between_localities(self, locality: str, content: dict) -> None:
        for link_to, link_type_list in content.items():
            for link_type in link_type_list:
                component_object = self.get_component_object(link_type)
                component_object.set_locality([self.format_locality_id(locality), self.format_locality_id(link_to)])
                self.add_component(component_object)
    
class ComponentParametersSetter:
    """
    Class that sets component parameters unique to each component and defined during system creation.
    """

    def set_component_supply(self, component: Component.Component, resource_name: str, 
                             resource_supply_amount: float, 
                             resource_supply_type=Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value) -> None:        
        component_supply = getattr(component, Component.SupplyOrDemand.SUPPLY.value)[resource_supply_type]
        component_supply[resource_name].set_initial_amount(resource_supply_amount)

    def set_component_operation_demand(self, component: Component.Component, resource_name: str, 
                             resource_demand_amount: float) -> None: 
        component_demand = getattr(component, Component.SupplyOrDemand.DEMAND.value)[
                            Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value]
        component_demand[resource_name].set_initial_amount(resource_demand_amount)
    
    def set_component_recovery_demand(self, component: Component.Component, recovery_activity_name: str, 
                                      resource_name: str, resource_amount: float):
        if recovery_activity_name in component.recovery_model.recovery_activities.keys():
            component.recovery_model.recovery_activities[recovery_activity_name].demand[resource_name].set_initial_amount(
                resource_amount)

class R2DResidentialBuildingParametersSetter(ComponentParametersSetter):
    """
    Class that sets parameters of residential building components as provided in the R2DTool output files
    """

    SYSTEM_LEVEL_DATA_REQUIRED_FOR_BUILDINGS = ['DS4_REPAIR_DURATION', 'MAX_REPAIR_CREW_DEMAND_PER_BUILDING',
                                                'MAX_RESIDENTS_PER_BUILDING', 'REPAIR_CREW_DEMAND_PER_SQFT',
                                                'DEFAULT_REPAIR_DURATION_DICT', 'DEMAND_PER_PERSON', 
                                                'building_area_per_person', 'scenario_id']
    
    def __init__(self, system_level_data: dict):
        self.system_level_data = system_level_data

    def set_parameters(self, component: Component.Component, locality: str, building_data: dict, building_DS: int):  
        self.set_building_geometry(component, building_data)      
        self.set_housing_parameters(component, locality, building_data['HousingResources'])
        self.set_operation_demand_parameters(component, locality, building_data.get('OperationDemandResources', []))
        self.set_repair_parameters(component, building_data, building_DS)       
        component.set_locality([R2DSystemCreator.format_locality_id(locality)])
        return component

    def set_building_geometry(self, component, building_data: dict):
        self.set_building_area(component, building_data)
        self.set_building_footprint(component, building_data)
        self.set_building_num_stories(component, building_data)
    
    def set_building_area(self, component: Component.Component, building_data: dict) -> None:
        component.area = self.get_total_building_area(building_data)

    def set_building_footprint(self, component: Component.Component, building_data: dict) -> None:
        component.footprint = json.loads(building_data['Information']['GeneralInformation']['Footprint'])

    def set_building_num_stories(self, component: Component.Component, building_data: dict) -> None:
        component.num_stories = building_data['Information']['GeneralInformation']['NumberOfStories']

    def get_total_building_area(self, building_data: dict) -> float:
        return building_data['Information']['GeneralInformation']['PlanArea'] * \
            building_data['Information']['GeneralInformation']['NumberOfStories']
    
    def set_housing_parameters(self, component: Component.Component, locality: str, housing_resource_names=['Shelter']):
        building_housing_capacity = self.get_building_housing_capacity(component.area, locality)
        for housing_resource_name in housing_resource_names:
            self.set_component_supply(component, housing_resource_name, building_housing_capacity)
            self.set_component_operation_demand(component, housing_resource_name, building_housing_capacity)

    def get_building_housing_capacity(self, building_area: float, locality: str) -> int:        
        building_housing_capacity = min(int(building_area / self.system_level_data['building_area_per_person'][locality]), self.system_level_data['MAX_RESIDENTS_PER_BUILDING'])
        return building_housing_capacity  
    
    def set_operation_demand_parameters(self, component: Component.Component, locality: str, operation_demand_resources: list):
        building_housing_capacity = self.get_building_housing_capacity(component.area, locality)
        for operation_demand_resource in operation_demand_resources:
            self.set_component_operation_demand(component, operation_demand_resource, 
                                                building_housing_capacity*self.system_level_data['DEMAND_PER_PERSON'][operation_demand_resource])
     
    def set_repair_parameters(self, component: Component.Component, building_data: dict, building_DS: int):
        self.set_repair_demand(component, building_data, building_DS)
        self.set_repair_duration(component, building_data)
        self.set_building_repair_cost(component, building_data)

    def set_repair_demand(self, component: Component.Component, building_data: dict, building_DS: int) -> None:
        if 'Repair' in component.recovery_model.recovery_activities.keys():
            repair_demand = self.get_repair_crew_demand(building_DS, component.area)
            self.set_component_recovery_demand(component, 'Repair', 'RepairCrew', repair_demand)

    def get_repair_crew_demand(self, building_DS: int, building_area: float) -> int:
        repair_crew_demand = math.ceil(building_area / self.system_level_data['REPAIR_CREW_DEMAND_PER_SQFT'][f'DS{building_DS}'])
        return min(self.system_level_data['MAX_REPAIR_CREW_DEMAND_PER_BUILDING'], repair_crew_demand)

    def set_repair_duration(self, component: Component.Component, building_data: dict) -> None:
        if 'Repair' in component.recovery_model.recovery_activities.keys():
            median_repair_duration = self.get_median_repair_duration(building_data)
            repair_duration_dict = copy.deepcopy(self.system_level_data['DEFAULT_REPAIR_DURATION_DICT'])
            repair_duration_dict['Lognormal']['Median'] = median_repair_duration
            component.recovery_model.recovery_activities['Repair'].set_duration(repair_duration_dict)

    def get_median_repair_duration(self, building_data: dict) -> int:
        """
        Get median repair duration from the R2D .csv building file. 
        Note that if the building collapsed, a dummy repair duration of 1 is assigned in R2D.
        In that case, set the repair duration to DS4 duration.
        """
        median_repair_duration = building_data['Damage']['reconstruction/time'][self.system_level_data['scenario_id']]
        if median_repair_duration == 1 and building_data['Damage']['collapses/collapsed'][self.system_level_data['scenario_id']] == 1:
            return self.system_level_data['DS4_REPAIR_DURATION']
        else:
            return median_repair_duration
  
    def set_building_repair_cost(self, component: Component.Component, building_data: dict) -> None:
        repair_cost = building_data['Damage']['reconstruction/cost'][self.system_level_data['scenario_id']]
        self.set_component_recovery_demand(component, 'Financing', 'Money', repair_cost)


    