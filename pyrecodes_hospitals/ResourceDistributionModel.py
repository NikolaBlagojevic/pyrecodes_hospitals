
from abc import ABC, abstractmethod
import numpy as np
import math
import copy
import json
import itertools 
from pyrecodes_hospitals import Component
from pyrecodes_hospitals import DistributionPriority

class ResourceDistributionModel(ABC):

    @abstractmethod
    def distribute(self) -> None:
        pass

    @abstractmethod
    def get_total_supply(self, scope: str) -> float:
        pass

    @abstractmethod
    def get_total_demand(self, scope: str) -> float:
        pass

    @abstractmethod
    def get_total_consumption(self, scope: str) -> float:
        pass

class ResourceDistributionModelConstructor(ABC):

    @abstractmethod
    def set_components(self, components: list([Component.Component]), distribution_model: ResourceDistributionModel) -> None:
        pass

    @abstractmethod
    def set_resource_name(self, resource_name: str) -> None:
        pass

class ConcreteResourceDistributionModelConstructor(ResourceDistributionModelConstructor):

    def construct(self, resource_name: str, resource_parameters: dict, components: list([Component.Component]), distribution_model: ResourceDistributionModel):
        self.set_resource_name(resource_name, distribution_model)
        self.set_components(components, distribution_model)
     
    def set_components(self, components: list([Component.Component]), distribution_model: ResourceDistributionModel) -> None:
        distribution_model.components = components

    def set_resource_name(self, resource_name: str, distribution_model: ResourceDistributionModel) -> None:
        distribution_model.resource_name = resource_name   

class UtilityDistributionModelConstructor(ConcreteResourceDistributionModelConstructor):

    def construct(self, resource_name: str, resource_parameters: dict, components: list([Component.Component]), distribution_model: ResourceDistributionModel):
        self.set_resource_name(resource_name, distribution_model)
        self.set_components(components, distribution_model)
        self.set_priority_model(resource_name, resource_parameters['DistributionPriority'], components, distribution_model)
        self.set_system_matrix(components, resource_name, distribution_model)

    def set_priority_model(self, resource_name: str, distribution_priority: dict, components: list([Component.Component]), distribution_model: ResourceDistributionModel) -> None:
        target_priority_model = getattr(DistributionPriority, distribution_priority['Type'])
        priority_model = target_priority_model(resource_name, distribution_priority['Parameters'], components)
        distribution_model.priority = priority_model
    
    def set_system_matrix(self, components: list([Component.Component]), resource_name: str, distribution_model: ResourceDistributionModel) -> None:
        distribution_model.system_matrix = SingleResourceSystemMatrixCreator(components, resource_name)
    
    def set_transfer_service_distribution_model(self, transfer_service_distribution_model: ResourceDistributionModel, distribution_model: ResourceDistributionModel) -> None:
        pass 

class SingleResourceSystemMatrixCreator():
    components: list([Component.Component])
    matrix: np.ndarray
    NUM_COLUMN_SETS = 5  # start_locality/end_locality/supply/demand/demand_met
    ROWS_PER_COMPONENT = 2  # operation demand/recovery demand

    def __init__(self, components: list([Component.Component]), resource_name: str):
        self.components = components
        self.resource_name = resource_name
        self.RECOVERY_DEMAND_ROW_OFFSET = len(components)
        self.set_system_matrix_column_ids()
        self.initialize_system_matrix()

    def set_system_matrix_column_ids(self):
        self.START_LOCALITY_COL_ID = 0
        self.END_LOCALITY_COL_ID = 1
        self.SUPPLY_COL_ID = 2
        self.DEMAND_COL_ID = 3
        self.DEMAND_MET_COL_ID = 4

    def initialize_system_matrix(self):
        self.matrix = np.zeros((self.calculate_num_rows_in_system_matrix(),
                                self.calculate_num_columns_in_system_matrix()))

    def calculate_num_rows_in_system_matrix(self):
        return len(self.components) * self.ROWS_PER_COMPONENT

    def calculate_num_columns_in_system_matrix(self):
        return self.NUM_COLUMN_SETS

    def fill_system_matrix(self):
        for row, component in enumerate(self.components):
            self.fill_operation_demand_row(row, component)
            self.fill_recovery_demand_row(row, component)

    def fill_operation_demand_row(self, row: int, component: Component.Component):
        self.matrix[row, :] = np.asarray(self.get_component_properties(component, [
            [Component.SupplyOrDemand.SUPPLY.value, Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value],
            [Component.SupplyOrDemand.DEMAND.value,
             Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value]]))

    def fill_recovery_demand_row(self, row: int, component: Component.Component):
        self.matrix[row + self.RECOVERY_DEMAND_ROW_OFFSET, :] = np.asarray(self.get_component_properties(component, [
            [Component.SupplyOrDemand.DEMAND.value,
             Component.StandardiReCoDeSComponent.DemandTypes.RECOVERY_DEMAND.value]]))

    def get_component_properties(self, component: Component.Component, types: list):
        component_properties = np.zeros(self.NUM_COLUMN_SETS)
        for supply_or_demand, type in types:
            value = self.get_current_resource_amount(component, supply_or_demand, type)
            if supply_or_demand == Component.SupplyOrDemand.SUPPLY.value:
                component_properties[self.SUPPLY_COL_ID] = value
            elif supply_or_demand == Component.SupplyOrDemand.DEMAND.value:
                component_properties[self.DEMAND_COL_ID] = value
        component_properties[self.DEMAND_MET_COL_ID] = self.get_initial_demand_met_indicator()
        component_properties[self.START_LOCALITY_COL_ID] = component.get_locality()[0]
        component_properties[self.END_LOCALITY_COL_ID] = component.get_locality()[-1]
        return component_properties

    def get_current_resource_amount(self, component: Component.Component, supply_or_demand: str, type: str):
        return component.get_current_resource_amount(supply_or_demand, type, self.resource_name)      

    def get_initial_demand_met_indicator(self) -> float:
        return 1.0

    def set_demand_met_indicator(self, component_row_id: int, percent_of_met_demand: float):
        self.matrix[component_row_id, self.DEMAND_MET_COL_ID] = percent_of_met_demand

    def get_demand(self, component_row_id: int) -> None:
        return self.matrix[component_row_id, self.DEMAND_COL_ID]

    def update_components(self, components: list([Component.Component])) -> None:
        self.components = components

class UtilityDistributionModel(ResourceDistributionModel):
    components: list([Component.Component])
    resource_name: str
    transfer_service_distribution_model: ResourceDistributionModel
    system_matrix: SingleResourceSystemMatrixCreator

    def __init__(self, resource_name: str, resource_parameters: dict, components: list([Component.Component])):
        self.constructor = UtilityDistributionModelConstructor()
        self.constructor.construct(resource_name, resource_parameters, components, self)
        self.transfer_service_distribution_model = None #consider moving this into the constructor or finding a better solution-the point is to have an initial value for this property

    def distribute(self):
        self.fill_system_matrix()

        component_priorities_by_row, component_demand_types = self.get_component_priorities()    

        suppliers = []
        for component_row_id, component_demand_type in zip(component_priorities_by_row, component_demand_types):
            suppliers, component_is_supplier = self.add_supplier(component_row_id, suppliers)
            suppliers = self.meet_component_demand(suppliers, component_row_id, component_demand_type)

            if component_is_supplier:
                self.reset_supplier_order(suppliers)

    def fill_system_matrix(self):
        self.system_matrix.update_components(self.components)
        self.system_matrix.fill_system_matrix()

    def get_component_priorities(self):
        component_priorities_id, component_demand_types = self.priority.get_component_priorities()
        component_row_in_system_matrix = self.set_component_row_based_on_demand_type(component_priorities_id,
                                                                                     component_demand_types)
        return component_row_in_system_matrix, component_demand_types

    def set_component_row_based_on_demand_type(self, component_priorities_id: list([int]),
                                               component_demand_types: list([str])):
        component_row_ids = []
        for component_priority_id, component_demand_type in zip(component_priorities_id, component_demand_types):
            if component_demand_type == Component.StandardiReCoDeSComponent.DemandTypes.RECOVERY_DEMAND.value:
                component_row_ids.append(component_priority_id + self.system_matrix.RECOVERY_DEMAND_ROW_OFFSET)
            elif component_demand_type == Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value:
                component_row_ids.append(component_priority_id)
        return component_row_ids

    def add_supplier(self, component_row_id: int, suppliers: list) -> 'tuple[list, bool]':
        current_supply = self.system_matrix.matrix[component_row_id, self.system_matrix.SUPPLY_COL_ID]
        start_locality = self.system_matrix.matrix[component_row_id, self.system_matrix.START_LOCALITY_COL_ID]
        end_locality = self.system_matrix.matrix[component_row_id, self.system_matrix.END_LOCALITY_COL_ID]
        component_is_supplier = False
        if current_supply > 0:
            suppliers.append([start_locality, end_locality, current_supply])
            self.put_current_supplier_on_top(suppliers)
            component_is_supplier = True
        return suppliers, component_is_supplier

    def put_current_supplier_on_top(self, suppliers):
        suppliers[0], suppliers[1:] = suppliers[-1], suppliers[0:-1]
        return suppliers

    def meet_component_demand(self, suppliers, component_row_id, component_demand_type):
        component_demand = self.get_demand(component_row_id)  
        component_localities = [self.system_matrix.matrix[component_row_id, self.system_matrix.START_LOCALITY_COL_ID],
                                self.system_matrix.matrix[component_row_id, self.system_matrix.END_LOCALITY_COL_ID]]
        if component_demand > 0.0:
            transfer_service_demand = self.get_transfer_service_demand(component_row_id, component_demand_type)
            component_demand_after_distribution, suppliers = self.suppliers_meet_component_demand(suppliers,
                                                                                                  component_demand,  
                                                                                                  component_localities,                                                                                      
                                                                                                  transfer_service_demand)

            if component_demand_after_distribution > 0.0:
                percent_of_met_demand = 1 - (component_demand_after_distribution / component_demand)
                self.set_demand_met_indicator(component_row_id, percent_of_met_demand)
                if component_demand_type == Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value:
                    self.reduce_component_supply(component_row_id, percent_of_met_demand)
                elif component_demand_type == Component.StandardiReCoDeSComponent.DemandTypes.RECOVERY_DEMAND.value:
                    self.set_unmet_demand_for_recovery_activities(component_row_id, percent_of_met_demand)     

        return suppliers

    def suppliers_meet_component_demand(self, suppliers, component_demand, component_localities, transfer_service_demand):
        for supplier in suppliers:
            supplier_start_locality, supplier_end_locality, current_supply = supplier
            supply_needed, path_functionality = self.modify_demand_to_account_for_resource_transfer(supplier_start_locality,
                                                                                   supplier_end_locality,
                                                                                   component_demand,
                                                                                   component_localities,                                                                                   
                                                                                   transfer_service_demand)
            # REFACTOR THIS, CAN BE DONE BETTER - PATH FUNCTIONALITY INTRODUCED TO AVOID SUPPLY_NEEDED = IN SCENARIOS WHEN THERE IS NO PATH BETWEEN TWO LOCALITIES
            if supply_needed < current_supply:
                current_supply -= supply_needed
                component_demand = 0
                supplier = self.update_supplier_resource_amount(supplier, current_supply)
                break
            elif path_functionality > 0:
                component_demand -= current_supply * path_functionality
                current_supply = 0
                supplier = self.update_supplier_resource_amount(supplier, current_supply)

        return component_demand, suppliers

    def update_supplier_resource_amount(self, supplier, current_supply):
        supplier[2] = current_supply
        return supplier

    def set_demand_met_indicator(self, component_row_id: int, percent_of_met_demand: float):
        self.system_matrix.set_demand_met_indicator(component_row_id, percent_of_met_demand)

    def reduce_component_supply(self, component_row_id: int, percent_of_met_demand: float):
        self.components[component_row_id].update_supply_based_on_unmet_demand(self.resource_name, percent_of_met_demand)

    def set_unmet_demand_for_recovery_activities(self, component_row_id: int, percent_of_met_demand: float):
        self.components[
            component_row_id - self.system_matrix.RECOVERY_DEMAND_ROW_OFFSET].set_unmet_demand_for_recovery_activities(
            self.resource_name, percent_of_met_demand)

    def reset_supplier_order(self, suppliers: list) -> list:
        suppliers[-1], suppliers[:-1] = suppliers[0], suppliers[1:]
        return suppliers

    def reset_suppliers(self, initial_suppliers: list) -> list:
        return copy.deepcopy(initial_suppliers)

    def get_demand(self, component_row_id: int) -> float:
        return self.system_matrix.get_demand(component_row_id)

    def get_transfer_service_demand(self, component_row_id: int, demand_type: str) -> float:
        """Method assumes that the transfer service demand is the same as the demand for the utility resource."""
        resource_name = self.resource_name
        # consider moving if statement to a separate method
        if demand_type == Component.StandardiReCoDeSComponent.DemandTypes.RECOVERY_DEMAND.value:
            component_row_id -= self.system_matrix.RECOVERY_DEMAND_ROW_OFFSET
        return self.components[component_row_id].get_current_resource_amount(
                                                                            Component.SupplyOrDemand.DEMAND.value, 
                                                                            demand_type, resource_name)       

    def modify_demand_to_account_for_resource_transfer(self, supplier_start_locality: int, supplier_end_locality: int,
                                                       component_demand: float, component_localities: list([int]),
                                                       transfer_service_demand: float) -> float:
        locality_pairs = self.get_locality_pairs(supplier_start_locality, supplier_end_locality, component_localities)
        
        best_path_functionality = self.get_best_path_functionality(locality_pairs, transfer_service_demand)        

        if best_path_functionality > 0:
            return component_demand / best_path_functionality, best_path_functionality
        else:
            return math.inf, best_path_functionality

    def get_locality_pairs(self, supplier_start_locality: int, supplier_end_locality: int, component_localities: list) -> list:
        """Finds non-duplicate locality pairs between supplier and component."""
        locality_pairs = [[supplier_start_locality, component_localities[0]], [supplier_start_locality, component_localities[1]], 
                            [supplier_end_locality, component_localities[0]], [supplier_end_locality, component_localities[1]]]
        locality_pairs.sort()
        return list(i for i,_ in itertools.groupby(locality_pairs))
               
    def get_best_path_functionality(self, locality_pairs: list, transfer_service_demand: float) -> float:
        best_path_functionality = 0.0
        for start_locality, end_locality in locality_pairs:
            current_path_functionality = self.get_path_functionality(start_locality, end_locality, transfer_service_demand)
            if current_path_functionality > best_path_functionality:
                best_path_functionality = current_path_functionality 
        return best_path_functionality
    
    def get_path_functionality(self, start_locality, end_locality, transfer_service_demand):
        """Method calculates path functionality by comparing the transfer service supply
            of the optimal path with the demand."""   
        if start_locality == end_locality:            
            return 1.0
        else:
            optimal_transfer_supply, optimal_path = self.get_optimal_path(start_locality, end_locality)
            return [1.0 if optimal_transfer_supply > transfer_service_demand else 0.0][0]

    def get_optimal_path(self, start_locality: int, end_locality: int) -> float:
        if self.transfer_service_distribution_model:
            return self.transfer_service_distribution_model.get_optimal_path(start_locality, end_locality)
        else:
            return math.inf, None
    
    def get_scope(self, scope=['All']) -> list:
        if scope == ['All']:
            return list(range(self.system_matrix.matrix.shape[0]))
        elif "Locality" in scope:
            locality_id = int(scope[-1])
            component_rows_in_locality = np.where(np.logical_or(self.system_matrix.matrix[:, self.system_matrix.START_LOCALITY_COL_ID] == locality_id, 
                                                  self.system_matrix.matrix[:, self.system_matrix.END_LOCALITY_COL_ID] == locality_id))
            return component_rows_in_locality
        # TODO: Fix this, it's vague. Anything can be in a list. Use a dict instead.
        elif isinstance(scope, list):
            # TODO: This assumes that the order of components in the system matrix is the same as the order of components in the self.components.
            return [i for i, component in enumerate(self.components) if component.name in scope]
        else:
            raise ValueError('Scope of the Re-CoDeS Resilience Calculator not well defined: All or Locality X or List of Departments.')

    def get_total_supply(self, scope: str) -> float:
        components_to_include = self.get_scope(scope)
        if len(components_to_include) == 0:
            return 0.0
        else:
            return np.sum(self.system_matrix.matrix[components_to_include, self.system_matrix.SUPPLY_COL_ID])

    def get_total_demand(self, scope: str) -> float:
        components_to_include = self.get_scope(scope)
        if len(components_to_include) == 0:
            return 0.0
        else:
            return np.sum(self.system_matrix.matrix[components_to_include, self.system_matrix.DEMAND_COL_ID])

    def get_total_consumption(self, scope: str) -> float:
        components_to_include = self.get_scope(scope)
        if len(components_to_include) == 0:
            return 0.0
        else:
            return np.sum(np.multiply(self.system_matrix.matrix[components_to_include, self.system_matrix.DEMAND_COL_ID],
                                  self.system_matrix.matrix[components_to_include, self.system_matrix.DEMAND_MET_COL_ID]))


class TimeStepsOfAutonomyDistributionModel(ResourceDistributionModel):
    """
    Resource distribution model that meets the demand of all components for a certain number of time steps.

    Supply/Demand are 1/0: 1 if there is supply, 0 if there is no supply
    """

    def __init__(self, resource_name: str, resource_parameters: dict, components: list([Component.Component])):
        self.constructor = ConcreteResourceDistributionModelConstructor()
        self.constructor.construct(resource_name, resource_parameters, components, self)
        self.transfer_service_distribution_model = None
        self.find_suppliers()
    
    def find_suppliers(self):
        self.suppliers = [component for component in self.components if component.has_resource_supply(self.resource_name)]

    def find_users(self):
        self.users = [component for component in self.components if component.get_current_resource_amount('demand', 'OperationDemand', self.resource_name) > 0]

    def distribute(self) -> None:
        supply_exists = self.check_if_supply_exists()
        self.update_user_operation_demand(supply_exists)
        
    def check_if_supply_exists(self):
        supply_exists = False
        for component in self.suppliers:
            if component.supply['Supply'][self.resource_name].current_amount > 0:
                supply_exists = True
                break
        return supply_exists

    def update_user_operation_demand(self, supply_exists: bool) -> None:
        self.find_users()
        if not(supply_exists):
            for component in self.users:
                component.update_supply_based_on_unmet_demand(self.resource_name, percent_of_met_demand=0)

    def get_scope(self, scope=['All']) -> list:
        if scope == ['All']:
            return self.components
        elif isinstance(scope, list):
            return [component for component in self.components if component.name in scope]
        
    def get_total_supply(self, scope: str) -> float:
        if self.check_if_supply_exists():
            return 1.0
        else:
            return 0.0

    def get_total_demand(self, scope: str) -> float:
        components_to_include = self.get_scope(scope)
        patients_needing_drugs = np.sum([component.get_current_resource_amount(Component.SupplyOrDemand.DEMAND.value,
                                                            Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value,
                                                            self.resource_name) for component in components_to_include])
        if patients_needing_drugs > 0:
            return 1.0
        else:
            return 0.0

    def get_total_consumption(self, scope: str) -> float:
        return min(self.get_total_supply(scope), self.get_total_demand(scope))

class TransferServiceDistributionModelPotentialPathSets(ResourceDistributionModel): 
    components: list([Component.Component])
    resource_name: str
    potential_paths: dict

    def __init__(self, resource_name: str, resource_parameters: dict, components: list([Component.Component])) -> None:
        self.constructor = ConcreteResourceDistributionModelConstructor()
        self.constructor.construct(resource_name, resource_parameters, components, self)
        self.set_potential_paths(resource_parameters["PathSetsFile"])
        self.create_potential_paths() 

    def set_potential_paths(self, filename: str):
        with open(filename, 'r') as file:
            self.potential_paths_list = json.load(file)
    
    def create_potential_paths(self) -> None:
        """ The method finds the links that are used in potential paths. 
        It creates a list of links that is latter queried to find the 
        optimal path from the list of potential paths."""     
        self.potential_paths = {} 
        for path_string, localities_list in self.potential_paths_list.items():       
            self.potential_paths[path_string] = [] 
            start_locality, end_locality = self.get_start_end_locality_from_path_string(path_string)                                  
            for localities in localities_list:
                current_start = start_locality                
                self.initiate_new_link_list(path_string)
                
                for locality in localities[1:]:                
                    self.find_connecting_link(path_string, current_start, locality)

                    if locality == end_locality:                    
                        break
                    else:                    
                        current_start = locality  

    def get_start_end_locality_from_path_string(self, path_string: str) -> tuple:
        return [int(locality) for locality in (path_string.split('from ')[1].split(' to '))]  
    
    def initiate_new_link_list(self, path_string) -> None:
        self.potential_paths[path_string].append([])
    
    def find_connecting_link(self, path_string: str, start_locality: int, next_locality: int):
        for component in self.components:
            if component.locality[0] == start_locality and \
                component.locality[-1] == next_locality and \
                component.has_resource_supply(self.resource_name):
                self.potential_paths[path_string][-1].append(component)
                break

    def distribute(self):
        """Distribute method updates the potential paths between all locality pairs.
        This is done implicitly when using the potential path sets,
        as components' transfer service supply is updated in the system class. """
        pass                                                                                    
                        
    def get_optimal_path(self, start_locality: int, end_locality: int) -> tuple:
        """Method finds the optimal path, from all potential paths between two localities.
            Optimality is defined as maximizing the transfer service supply.
            Transfer service supply of a path is the minimal supply among its constitutive links."""   
        potential_path_links = self.potential_paths.get(f'from {int(start_locality)} to {int(end_locality)}', None)
      
        if potential_path_links is None:
            optimal_transfer_supply = 0.0
            optimal_path = None
            return optimal_transfer_supply, optimal_path
        else:
            optimal_path = None
            optimal_transfer_supply = -math.inf
            
            for i, path in enumerate(potential_path_links):        
                path_supply = self.get_path_supply(path)
          
                if path_supply > optimal_transfer_supply:
                    optimal_transfer_supply = path_supply                
                    optimal_path = i
            
            return optimal_transfer_supply, optimal_path      

    def get_path_supply(self, path: list([Component.Component])) -> float:
        """Get the supply capacity of a path as the minimum of links supply."""    
        return min([link.get_current_resource_amount(Component.SupplyOrDemand.SUPPLY.value, 
                                                    Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value, 
                                                    self.resource_name) for link in path])       

    def get_total_supply(self, scope: str) -> float:
        print(f'System supply for transfer service {self.resource_name} not defined yet.')
        return None

    def get_total_demand(self, scope: str) -> float:
        print(f'System demand for transfer service {self.resource_name} not defined yet.')
        return None

    def get_total_consumption(self, scope: str) -> float:
        print(f'System consumption for transfer service {self.resource_name} not defined yet.')   
        return None

class BridgeServiceDistributionModel(ResourceDistributionModel):       
    
    def distribute(self) -> None:
        pass
    
    def get_total_supply(self) -> float:
        pass
    
    def get_total_demand(self) -> float:
        pass
    
    def get_total_consumption(self) -> float:
        pass

