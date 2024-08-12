import math
import numpy as np
import pytest
from pyrecodes_hospitals import Component
from pyrecodes_hospitals import ComponentLibraryCreator
from pyrecodes_hospitals import DistributionPriority
from pyrecodes_hospitals import System
from pyrecodes_hospitals import SystemCreator
from pyrecodes_hospitals import main

def set_bsu_communication_resource_name(components):
    for component in components:
        if component.name == 'BuildingStockUnit':
            component.COMMUNICATION_RESOURCE_NAME = 'Communication'

class TestSingleResourceSystemMatrixCreator():

    COMPONENT_LIBRARY_FILE = "./tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_ComponentLibrary.json"
    SYSTEM_CONFIGURATION_FILE = './tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_SystemConfiguration.json'

    @pytest.fixture
    def system_creator(self):
        return SystemCreator.JSONSystemCreator()

    @pytest.fixture
    def component_library(self):
        return ComponentLibraryCreator.JSONComponentLibraryCreator(self.COMPONENT_LIBRARY_FILE).form_library()

    @pytest.fixture
    def system(self, system_creator, component_library):
        system = System.BuiltEnvironmentSystem(self.SYSTEM_CONFIGURATION_FILE, component_library, system_creator)
        system.time_step = 0
        # set_bsu_communication_resource_name(system.components)
        return system

    @pytest.fixture
    def distribution_models(self, system_creator, component_library):
        system_creator.setup(component_library, self.SYSTEM_CONFIGURATION_FILE)
        components = system_creator.create_components()
        # set_bsu_communication_resource_name(components)
        resources = system_creator.get_resource_parameters(components)
        distribution_models = {resource_name: resource_parameters['DistributionModel'] for
                               resource_name, resource_parameters in resources.items()}
        return distribution_models    

    def test_initialize_system_matrix(self, distribution_models: dict, system: System.System):
        bool_list = []
        for distribution_model in distribution_models.values():
            bool_list.append(np.all(distribution_model.system_matrix.matrix == np.zeros(
                (2 * len(system.components), distribution_models['ElectricPower'].system_matrix.NUM_COLUMN_SETS))))
        assert all(bool_list)

    def test_calculate_num_rows_in_system_matrix(self, distribution_models: dict, system: System.System):
        assert distribution_models['ElectricPower'].system_matrix.calculate_num_rows_in_system_matrix() == len(
            system.components) * distribution_models['ElectricPower'].system_matrix.ROWS_PER_COMPONENT

    def test_calculate_num_columns_in_system_matrix(self, distribution_models: dict):
        assert distribution_models['ElectricPower'].system_matrix.calculate_num_columns_in_system_matrix() == \
               distribution_models['ElectricPower'].system_matrix.NUM_COLUMN_SETS

    def test_fill_operation_demand_row(self, distribution_models: dict):
        bool_list = []
        for resource_name, distribution_model in distribution_models.items():
            for i, component in enumerate(distribution_model.components):
                supply = distribution_model.system_matrix.get_current_resource_amount(component, 'supply',
                                                                                      Component.StandardiReCoDeSComponent.SupplyTypes.SUPPLY.value)
                demand = distribution_model.system_matrix.get_current_resource_amount(component, 'demand',
                                                                                      Component.StandardiReCoDeSComponent.DemandTypes.OPERATION_DEMAND.value)
                target_row = [component.get_locality()[0], component.get_locality()[-1], supply, demand, 1.0]
                distribution_model.system_matrix.fill_operation_demand_row(i, component)
                bool_list.append(np.all(target_row == distribution_model.system_matrix.matrix[i, :]))
        assert all(bool_list)

    def test_fill_recovery_demand_row(self, distribution_models: dict):
        bool_list = []
        for resource_name, distribution_model in distribution_models.items():
            for i, component in enumerate(distribution_model.components):
                recovery_demand = distribution_model.system_matrix.get_current_resource_amount(component, 'demand',
                                                                                               Component.StandardiReCoDeSComponent.DemandTypes.RECOVERY_DEMAND.value)
                target_row = [component.get_locality()[0], component.get_locality()[-1], 0.0, recovery_demand, 1.0]
                distribution_model.system_matrix.fill_recovery_demand_row(i, component)
                bool_list.append(np.all(target_row == distribution_model.system_matrix.matrix[
                                                      i + distribution_model.system_matrix.RECOVERY_DEMAND_ROW_OFFSET,
                                                      :]))
        assert all(bool_list)

    def test_fill_system_matrix_no_damage(self, distribution_models: dict):
        for distribution_model in distribution_models.values():
            distribution_model.system_matrix.fill_system_matrix()
        bool_list = []
        locality_matrix = []
        for component in distribution_model.components:
            locality_matrix.append([component.get_locality()[0], component.get_locality()[-1]])

        recovery_demand_matrix_part = np.concatenate(
            (locality_matrix, np.asarray([[0.0, 0.0, 1.0] for _ in distribution_models['ElectricPower'].components])),
            axis=1)
        target_power_matrix = np.concatenate(
            (np.asarray([[1, 1, 0.0, 1.0, 1.0], [1, 1, 5.0, 0.0, 1.0], [1, 2, 0.0, 0.0, 1.0], [1, 3, 0.0, 0.0, 1.0],
                         [2, 2, 0.0, 1.0, 1.0], [2, 1, 0.0, 0.0, 1.0], [2, 3, 0.0, 0.0, 1.0], [3, 3, 0.0, 1.0, 1.0],
                         [3, 3, 0.0, 1.0, 1.0], [3, 1, 0.0, 0.0, 1.0], [3, 2, 0.0, 0.0, 1.0]]),
             recovery_demand_matrix_part), axis=0)

        bool_list.append(np.all(target_power_matrix == distribution_models['ElectricPower'].system_matrix.matrix))
        target_communication_matrix = np.concatenate(
            (np.asarray([[1, 1, 1.0, 0.0, 1.0], [1, 1, 0.0, 1.0, 1.0], [1, 2, 0.0, 0.0, 1.0], [1, 3, 0.0, 0.0, 1.0],
                         [2, 2, 0.0, 1.0, 1.0], [2, 1, 0.0, 0.0, 1.0], [2, 3, 0.0, 0.0, 1.0], [3, 3, 0.0, 1.0, 1.0],
                         [3, 3, 2.0, 0.0, 1.0], [3, 1, 0.0, 0.0, 1.0], [3, 2, 0.0, 0.0, 1.0]]),
             recovery_demand_matrix_part), axis=0)
        bool_list.append(
            np.all(target_communication_matrix == distribution_models['Communication'].system_matrix.matrix))

        target_cooling_water_matrix = np.concatenate(
            (np.asarray([[1, 1, 0.0, 0.0, 1.0], [1, 1, 0.0, 1.0, 1.0], [1, 2, 0.0, 0.0, 1.0], [1, 3, 0.0, 0.0, 1.0],
                         [2, 2, 3.0, 0.0, 1.0], [2, 1, 0.0, 0.0, 1.0], [2, 3, 0.0, 0.0, 1.0], [3, 3, 0.0, 0.0, 1.0],
                         [3, 3, 0.0, 0.0, 1.0], [3, 1, 0.0, 0.0, 1.0], [3, 2, 0.0, 0.0, 1.0]]),
             recovery_demand_matrix_part), axis=0)
        bool_list.append(
            np.all(target_cooling_water_matrix == distribution_models['CoolingWater'].system_matrix.matrix))
        assert all(bool_list)

    def test_fill_system_matrix_with_damage(self, distribution_models: dict, system: System.System):
        system.set_initial_damage()
        system.update()
        for distribution_model in distribution_models.values():
            distribution_model.components = system.components
            distribution_model.fill_system_matrix()
        bool_list = []
        locality_matrix = []
        for component in distribution_model.components:
            locality_matrix.append([component.get_locality()[0], component.get_locality()[-1]])

        recovery_demand_matrix_part = np.concatenate(
            (locality_matrix, np.asarray([[0.0, 0.0, 1.0] for _ in distribution_models['ElectricPower'].components])),
            axis=1)
        target_power_matrix = np.concatenate(
            (np.asarray([[1, 1, 0.0, 1.0, 1.0], [1, 1, 3.0, 0.0, 1.0], [1, 2, 0.0, 0.0, 1.0], [1, 3, 0.0, 0.0, 1.0],
                         [2, 2, 0.0, 1.0, 1.0], [2, 1, 0.0, 0.0, 1.0], [2, 3, 0.0, 0.0, 1.0], [3, 3, 0.0, 0.6, 1.0],
                         [3, 3, 0.0, 0.0, 1.0], [3, 1, 0.0, 0.0, 1.0], [3, 2, 0.0, 0.0, 1.0]]),
             recovery_demand_matrix_part), axis=0)
        bool_list.append(
            np.all(np.isclose(target_power_matrix, distribution_models['ElectricPower'].system_matrix.matrix)))

        target_communication_matrix = np.concatenate(
            (np.asarray([[1, 1, 1.0, 0.0, 1.0], [1, 1, 0.0, 1.0, 1.0], [1, 2, 0.0, 0.0, 1.0], [1, 3, 0.0, 0.0, 1.0],
                         [2, 2, 0.0, 1.0, 1.0], [2, 1, 0.0, 0.0, 1.0], [2, 3, 0.0, 0.0, 1.0], [3, 3, 0.0, 1.0, 1.0],
                         [3, 3, 0.0, 0.0, 1.0], [3, 1, 0.0, 0.0, 1.0], [3, 2, 0.0, 0.0, 1.0]]),
             recovery_demand_matrix_part), axis=0)
        bool_list.append(
            np.all(np.isclose(target_communication_matrix, distribution_models['Communication'].system_matrix.matrix)))

        target_cooling_water_matrix = np.concatenate(
            (np.asarray([[1, 1, 0.0, 0.0, 1.0], [1, 1, 0.0, 1.0, 1.0], [1, 2, 0.0, 0.0, 1.0], [1, 3, 0.0, 0.0, 1.0],
                         [2, 2, 1.8, 0.0, 1.0], [2, 1, 0.0, 0.0, 1.0], [2, 3, 0.0, 0.0, 1.0], [3, 3, 0.0, 0.0, 1.0],
                         [3, 3, 0.0, 0.0, 1.0], [3, 1, 0.0, 0.0, 1.0], [3, 2, 0.0, 0.0, 1.0]]),
             recovery_demand_matrix_part), axis=0)
        bool_list.append(
            np.all(np.isclose(target_cooling_water_matrix, distribution_models['CoolingWater'].system_matrix.matrix)))
        assert all(bool_list)

    def test_get_component_properties(self, distribution_models: dict):
        bool_list = []
        electric_power_plant = distribution_models['ElectricPower'].components[1]
        component_properties = distribution_models['ElectricPower'].system_matrix.get_component_properties(
            electric_power_plant, [['supply', 'Supply'], ['demand', 'OperationDemand']])
        bool_list.append(all(component_properties == [1, 1, 5, 0, 1]))
        component_properties = distribution_models['ElectricPower'].system_matrix.get_component_properties(
            electric_power_plant, [['supply', 'Supply'], ['demand', 'RecoveryDemand']])
        bool_list.append(all(component_properties == [1, 1, 5, 0, 1]))
        component_properties = distribution_models['CoolingWater'].system_matrix.get_component_properties(
            electric_power_plant, [['supply', 'Supply'], ['demand', 'OperationDemand']])
        bool_list.append(all(component_properties == [1, 1, 0, 1, 1]))
        component_properties = distribution_models['Communication'].system_matrix.get_component_properties(
            electric_power_plant, [['supply', 'Supply'], ['demand', 'OperationDemand']])
        bool_list.append(all(component_properties == [1, 1, 0, 1, 1]))
        assert all(bool_list)

    def test_get_current_resource_amount(self, distribution_models: dict):
        bool_list = []
        building_stock_unit = distribution_models['ElectricPower'].components[7]
        bool_list.append(
            distribution_models['ElectricPower'].system_matrix.get_current_resource_amount(building_stock_unit,
                                                                                           'supply', 'Supply') == 0.0)
        bool_list.append(
            distribution_models['ElectricPower'].system_matrix.get_current_resource_amount(building_stock_unit,
                                                                                           'demand',
                                                                                           'OperationDemand') == 1.0)
        bool_list.append(
            distribution_models['CoolingWater'].system_matrix.get_current_resource_amount(building_stock_unit, 'demand',
                                                                                          'OperationDemand') == 0.0)
        bool_list.append(
            distribution_models['Communication'].system_matrix.get_current_resource_amount(building_stock_unit,
                                                                                           'demand',
                                                                                           'OperationDemand') == 1.0)
        assert all(bool_list)

    def test_set_demand_met_indicator(self, distribution_models: dict):
        distribution_models['ElectricPower'].system_matrix.set_demand_met_indicator(0, 0.5)
        distribution_models['CoolingWater'].system_matrix.set_demand_met_indicator(0, 0.5)
        distribution_models['Communication'].system_matrix.set_demand_met_indicator(0, 0.5)
        assert all([distribution_models['ElectricPower'].system_matrix.matrix[
                        0, distribution_models['ElectricPower'].system_matrix.DEMAND_MET_COL_ID] == 0.5,
                    distribution_models['CoolingWater'].system_matrix.matrix[
                        0, distribution_models['CoolingWater'].system_matrix.DEMAND_MET_COL_ID] == 0.5,
                    distribution_models['Communication'].system_matrix.matrix[
                        0, distribution_models['Communication'].system_matrix.DEMAND_MET_COL_ID] == 0.5])

    def test_get_demand(self, distribution_models: dict):
        assert all([distribution_models['ElectricPower'].system_matrix.get_demand(0) ==
                    distribution_models['ElectricPower'].system_matrix.matrix[
                        0, distribution_models['ElectricPower'].system_matrix.DEMAND_COL_ID],
                    distribution_models['Communication'].system_matrix.get_demand(0) ==
                    distribution_models['Communication'].system_matrix.matrix[
                        0, distribution_models['Communication'].system_matrix.DEMAND_COL_ID],
                    distribution_models['CoolingWater'].system_matrix.get_demand(0) ==
                    distribution_models['CoolingWater'].system_matrix.matrix[
                        0, distribution_models['CoolingWater'].system_matrix.DEMAND_COL_ID]])

    def test_get_initial_demand_met_indicators(self, distribution_models: dict):
        assert distribution_models['ElectricPower'].system_matrix.get_initial_demand_met_indicator() == 1.0


class TestUtilityDistributionModel_ThreeLocalitiesCommunity():

    COMPONENT_LIBRARY_FILE = "./tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_ComponentLibrary.json"
    SYSTEM_CONFIGURATION_FILE = './tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_SystemConfiguration.json'

    @pytest.fixture
    def system_creator(self):
        return SystemCreator.JSONSystemCreator()

    @pytest.fixture
    def component_library(self):
        return ComponentLibraryCreator.JSONComponentLibraryCreator(self.COMPONENT_LIBRARY_FILE).form_library()

    @pytest.fixture
    def system(self, system_creator, component_library):
        system = System.BuiltEnvironmentSystem(self.SYSTEM_CONFIGURATION_FILE, component_library, system_creator)
        set_bsu_communication_resource_name(system.components)
        system.time_step = 0
        return system

    @pytest.fixture
    def distribution_models(self, system_creator, component_library):
        system_creator.setup(component_library, self.SYSTEM_CONFIGURATION_FILE)
        components = system_creator.create_components()
        set_bsu_communication_resource_name(components)
        resources = system_creator.get_resource_parameters(components)
        distribution_models = {resource_name: resource_parameters['DistributionModel'] for
                               resource_name, resource_parameters in resources.items()}
        return distribution_models

    def test_init_(self, distribution_models: dict, system: System.System):
        bool_list = []
        bool_list.append(
            distribution_models['ElectricPower'].system_matrix.RECOVERY_DEMAND_ROW_OFFSET == len(system.components))
        bool_list.append(
            isinstance(distribution_models['ElectricPower'].priority, DistributionPriority.ComponentBasedPriority))
        bool_list.append(distribution_models['ElectricPower'].transfer_service_distribution_model == None)
        bool_list.append(np.all(distribution_models['ElectricPower'].system_matrix.matrix == np.zeros(
            (2 * len(system.components), distribution_models['ElectricPower'].system_matrix.NUM_COLUMN_SETS))))
        assert all(bool_list)

    def test_add_supplier(self, distribution_models: dict):
        power_plant_row_id = 1
        bool_list = []
        target_component_is_supplier = [True, False, False]
        target_suppliers_length = [1, 0, 0]
        for target_bool, target_length, distribution_model in zip(target_component_is_supplier, target_suppliers_length,
                                                                  distribution_models.values()):
            distribution_model.system_matrix.fill_system_matrix()
            suppliers = []
            suppliers, component_is_supplier = distribution_model.add_supplier(power_plant_row_id, suppliers)
            bool_list.append(len(suppliers) == target_length)
            bool_list.append(component_is_supplier == target_bool)
        assert all(bool_list)

    def test_add_supplier_with_damage(self, distribution_models: dict, system: System.System):
        system.set_initial_damage()
        system.update()
        target_damaged_supply_values = [3.0, 1.8, 1.0]
        bool_list = []
        for target_value, distribution_model in zip(target_damaged_supply_values, distribution_models.values()):
            distribution_model.components = system.components
            distribution_model.fill_system_matrix()
            suppliers = []
            for component_row_id in range(len(distribution_model.components)):
                suppliers, component_is_supplier = distribution_model.add_supplier(component_row_id, suppliers)               

            bool_list.append(math.isclose(suppliers[0][2], target_value))

        assert all(bool_list)

    def test_suppliers_meet_component_demand_no_damage(self, distribution_models: dict):
        building_stock_id = 7
        component_demand_type = 'OperationDemand'
        bool_list = []
        for distribution_model in distribution_models.values():
            distribution_model.fill_system_matrix()
            suppliers = []
            component_priorities, component_demand_types = distribution_model.get_component_priorities()
            for component_row_id, component_demand_type in zip(component_priorities, component_demand_types):                
                suppliers, component_is_supplier = distribution_model.add_supplier(component_row_id, suppliers) 
            component_demand = distribution_model.get_demand(building_stock_id)
            component_localities = [distribution_model.system_matrix.matrix[building_stock_id, distribution_model.system_matrix.START_LOCALITY_COL_ID],
                                distribution_model.system_matrix.matrix[building_stock_id, distribution_model.system_matrix.END_LOCALITY_COL_ID]]
            transfer_service_demand = distribution_model.get_transfer_service_demand(building_stock_id, component_demand_type)
            demand_after_distribution, suppliers= distribution_model.suppliers_meet_component_demand(suppliers, component_demand, component_localities, transfer_service_demand)
            bool_list.append(math.isclose(demand_after_distribution, 0, abs_tol=1e-5))
        assert all(bool_list)

    def test_suppliers_meet_component_demand_with_damage(self, distribution_models: dict, system: System.System):
        system.set_initial_damage()
        system.update()
        building_stock_id = 7
        component_demand_type = 'OperationDemand'
        bool_list = []
        target_demand_values = [0.0, 0.0, 1.0]
        set_supplier_amount = [2.0, 0.0, 0.0]
        for target_value, supplier_amount, distribution_model in zip(target_demand_values, set_supplier_amount,
                                                                     distribution_models.values()):
            distribution_model.components = system.components
            distribution_model.fill_system_matrix()
            suppliers = [[1.0, 1.0, supplier_amount]]
            component_demand = distribution_model.get_demand(building_stock_id)
            component_localities = [distribution_model.system_matrix.matrix[building_stock_id, distribution_model.system_matrix.START_LOCALITY_COL_ID],
                                distribution_model.system_matrix.matrix[building_stock_id, distribution_model.system_matrix.END_LOCALITY_COL_ID]]
            transfer_service_demand = distribution_model.get_transfer_service_demand(building_stock_id, component_demand_type)
            demand_after_distribution, suppliers= distribution_model.suppliers_meet_component_demand(suppliers, 
                                                                                                    component_demand, 
                                                                                                    component_localities, 
                                                                                                    transfer_service_demand)
            print(demand_after_distribution)
            bool_list.append(math.isclose(demand_after_distribution, target_value, abs_tol=1e-10))
        assert all(bool_list)

    def test_reduce_component_supply(self, distribution_models: dict):
        power_plant_row_id = 1
        base_station_row_id = 0
        percent_of_met_demand = 0.4
        reduced_supply_of_the_power_plant = [5.0, 0.0, 0.0]
        reduced_supply_of_the_base_station = [0.0, 1.0, 1.0]
        for power_plant_supply, base_station_supply, distribution_model in zip(reduced_supply_of_the_power_plant,
                                                                               reduced_supply_of_the_base_station,
                                                                               distribution_models.values()):
            distribution_model.components[power_plant_row_id].supply['Supply']['ElectricPower'].set_current_amount(5.0)
            distribution_model.components[base_station_row_id].supply['Supply']['Communication'].set_current_amount(1.0)
            distribution_model.reduce_component_supply(power_plant_row_id, percent_of_met_demand)
            distribution_model.reduce_component_supply(base_station_row_id, percent_of_met_demand)
            assert math.isclose(
                distribution_model.components[power_plant_row_id].get_current_resource_amount('supply', 
                                                                                              'Supply',
                                                                                              'ElectricPower'),
                power_plant_supply)
            assert math.isclose(
                distribution_model.components[base_station_row_id].get_current_resource_amount('supply', 
                                                                                              'Supply',
                                                                                              'Communication'),
                base_station_supply)


    def test_get_demand(self, distribution_models: dict):
        bool_list = []
        demand_of_the_power_plant = [0.0, 1.0, 1.0]
        power_plant_row_id = 1
        for target_demand, distribution_model in zip(demand_of_the_power_plant, distribution_models.values()):
            distribution_model.fill_system_matrix()
            bool_list.append(distribution_model.get_demand(power_plant_row_id) == target_demand)
        assert all(bool_list)

    def test_get_transfer_service_demand(self, distribution_models: dict):
        # TODO: Implement when method is ready.
        pass

    def test_modify_demand_to_account_for_resource_transfer(self, distribution_models: dict):
        # TODO: Implement when method is ready.
        pass

    def test_get_system_supply_no_damage(self, distribution_models: dict):
        target_supplies = [5.0, 3.0, 3.0]
        bool_list = []
        for target_supply, distribution_model in zip(target_supplies, distribution_models.values()):
            distribution_model.fill_system_matrix()
            current_supply = distribution_model.get_total_supply(scope=['All'])
            bool_list.append(math.isclose(target_supply, current_supply))

        assert all(bool_list)

    def test_get_system_supply_with_damage(self, distribution_models: dict, system: System.System):
        target_supplies = [3.0, 1.8, 1.0]
        bool_list = []
        system.set_initial_damage()
        system.update()
        for target_supply, distribution_model in zip(target_supplies, distribution_models.values()):
            distribution_model.components = system.components
            distribution_model.fill_system_matrix()
            current_supply = distribution_model.get_total_supply(scope=['All'])
            bool_list.append(math.isclose(target_supply, current_supply))

        assert all(bool_list)

    def test_get_system_demand_no_damage(self, distribution_models: dict):
        target_demands = [4.0, 1.0, 3.0]
        bool_list = []
        for target_demand, distribution_model in zip(target_demands, distribution_models.values()):
            distribution_model.fill_system_matrix()
            current_demand = distribution_model.get_total_demand(scope=['All'])
            bool_list.append(math.isclose(target_demand, current_demand))

        assert all(bool_list)

    def test_get_system_demand_with_damage(self, distribution_models: dict, system: System.System):
        target_demands = [2.6, 1.0, 12.0]
        bool_list = []
        system.set_initial_damage()
        system.time_step = 1
        system.update()
        for target_demand, distribution_model in zip(target_demands, distribution_models.values()):
            distribution_model.components = system.components
            distribution_model.fill_system_matrix()
            current_demand = distribution_model.get_total_demand(scope=['All'])
            bool_list.append(math.isclose(target_demand, current_demand))

        assert all(bool_list)

    def test_get_system_consumption_no_damage(self, distribution_models: dict):
        target_consumptions = [4.0, 1.0, 3.0]
        bool_list = []
        for target_consumption, distribution_model in zip(target_consumptions, distribution_models.values()):
            distribution_model.fill_system_matrix()
            current_consumption = distribution_model.get_total_consumption(scope=['All'])
            bool_list.append(math.isclose(target_consumption, current_consumption))

        assert all(bool_list)

    def test_get_system_consumption_with_damage(self, distribution_models: dict, system: System.System):
        target_demands = [2.6, 1.0, 1.0]
        bool_list = []
        system.set_initial_damage()
        system.time_step = 1
        system.update()
        for target_demand, distribution_model in zip(target_demands, distribution_models.values()):
            distribution_model.components = system.components
            distribution_model.distribute()
            current_consumption = distribution_model.get_total_consumption(scope=['All'])
            bool_list.append(math.isclose(target_demand, current_consumption))

        assert all(bool_list)

class TestHospitalDistributionModel():

    MAIN_FILE = './tests/test_inputs/test_inputs_Hospital_Main.json'
    EXCEL_INPUT_1 = './tests/test_inputs/test_inputs_Hospital_ExcelInput1.xlsx'
    EXCEL_INPUT_2 = './tests/test_inputs/test_inputs_Hospital_ExcelInput2.xlsx'
    EXCEL_INPUT_3 = './tests/test_inputs/test_inputs_Hospital_ExcelInput3.xlsx'
    ADDITIONAL_DATA_LOCATION = './tests/test_inputs/'
    MCI_SCENARIO_PARAMETERS = {}

    def initiate_system(self, excel_input_file_name: str):
        excel_input_data = main.read_excel_input(excel_input_file_name)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        main.format_input_from_excel(excel_input_data, self.MCI_SCENARIO_PARAMETERS, input_dict, self.ADDITIONAL_DATA_LOCATION, 
                                    default_patient_library_file='test_inputs_Hospital_PatientLibrary.json',
                                    default_stress_scenario_file='test_inputs_Hospital_StressScenario.json')
        system = main.create_system(input_dict)
        return system

class TestUtilityDistributionModel_Hospital(TestHospitalDistributionModel):
    
    def test_nurse_distribution(self):
        system = self.initiate_system(self.EXCEL_INPUT_1)
        distribution_model = system.resources['Nurse']['DistributionModel']
        distribution_model.components[9].supply['Supply']['Nurse'].current_amount = 0
        distribution_model.components[9].supply['Supply']['Nurse'].initial_amount = 0
        system.set_initial_damage()
        system.time_step = 1
        system.receive_patients()        
        system.update()        
        distribution_model.distribute()
        assert system.components[1].patients[0].demand_met[0]['Nurse'] == 0
        system.update_patients()
        assert system.components[1].patients[0].unmet_demand_info['Nurse'] == [1]

        distribution_model.components[9].supply['Supply']['Nurse'].current_amount = 6
        distribution_model.components[9].supply['Supply']['Nurse'].initial_amount = 6
        distribution_model.distribute()
        assert system.components[1].patients[0].demand_met[0]['Nurse'] == 1.0
        system.update_patients()
        assert system.components[1].patients[0].unmet_demand_info['Nurse'] == [1]

        system.time_step = 2
        distribution_model.components[9].supply['Supply']['Nurse'].current_amount = 6
        distribution_model.components[9].supply['Supply']['Nurse'].initial_amount = 6
        system.receive_patients() 
        system.update()   
        distribution_model.distribute() 
        assert system.components[1].patients[0].demand_met[0]['Nurse'] == 1.0
        assert math.isclose(system.components[2].patients[0].demand_met[1]['Nurse'], 1/1.5)
        system.update_patients()
        assert system.components[2].patients[0].unmet_demand_info['Nurse'] == [1, 2]

        distribution_model.components[9].supply['Supply']['Nurse'].current_amount = 8
        distribution_model.components[9].supply['Supply']['Nurse'].initial_amount = 8
        distribution_model.distribute() 
        assert system.components[1].patients[0].demand_met[0]['Nurse'] == 1.0
        assert system.components[2].patients[0].demand_met[1]['Nurse'] == 1.0

        system.time_step = 3
        distribution_model.components[9].supply['Supply']['Nurse'].current_amount = 7
        distribution_model.components[9].supply['Supply']['Nurse'].initial_amount = 7
        system.receive_patients() 
        system.update()  
        distribution_model.distribute() 
        assert system.components[1].patients[0].demand_met[0]['Nurse'] == 1.0
        assert math.isclose(system.components[2].patients[0].demand_met[1]['Nurse'], 1/1.5)
        assert math.isclose(system.components[2].patients[1].demand_met[1]['Nurse'], 1/1.5)    
        
    def test_fuel_distribution(self):
        system = self.initiate_system(self.EXCEL_INPUT_1)
        system.time_step = 1
        distribution_model = system.resources['Fuel']['DistributionModel']
        distribution_model.distribute()
        assert distribution_model.components[6].supply['Supply']['ElectricPower'].current_amount > 0

        system.update()
        distribution_model.components[7].supply['Supply']['Fuel'].current_amount = 0
        distribution_model.distribute()
        assert distribution_model.components[6].supply['Supply']['ElectricPower'].current_amount == 0

        system.update()
        distribution_model.components[7].supply['Supply']['Fuel'].current_amount = 400
        distribution_model.distribute()
        assert distribution_model.components[6].supply['Supply']['ElectricPower'].current_amount == 1000000 * 0.8

        system.update()
        distribution_model.components[7].supply['Supply']['Fuel'].current_amount = 500
        distribution_model.distribute()
        assert distribution_model.components[6].supply['Supply']['ElectricPower'].current_amount == 1000000

    def test_oxygen_distribution(self):
        system = self.initiate_system(self.EXCEL_INPUT_1)
        distribution_model = system.resources['Oxygen']['DistributionModel']
        # Oxygen Reservoir
        distribution_model.components[11].supply['Supply']['Oxygen'].current_amount = 0
        distribution_model.components[11].supply['Supply']['Oxygen'].initial_amount = 0
        # Oxygen Concentrator
        distribution_model.components[12].supply['Supply']['Oxygen'].current_amount = 0
        distribution_model.components[12].supply['Supply']['Oxygen'].initial_amount = 0

        system.set_initial_damage()
        system.time_step = 1
        system.receive_patients()        
        system.update()        
        distribution_model.distribute()
        assert system.components[1].patients[0].demand_met[0]['Oxygen'] == 0
        system.update_patients()

        distribution_model.components[11].supply['Supply']['Oxygen'].current_amount = 720
        distribution_model.components[11].supply['Supply']['Oxygen'].initial_amount = 720
        distribution_model.components[12].supply['Supply']['Oxygen'].current_amount = 0
        distribution_model.components[12].supply['Supply']['Oxygen'].initial_amount = 0
        system.time_step = 2
        system.receive_patients()        
        system.update()        
        distribution_model.distribute()
        assert system.components[1].patients[0].demand_met[0]['Oxygen'] == 1.0
        system.update_patients()

        distribution_model.components[11].supply['Supply']['Oxygen'].current_amount = 360
        distribution_model.components[11].supply['Supply']['Oxygen'].initial_amount = 360
        distribution_model.components[12].supply['Supply']['Oxygen'].current_amount = 300
        distribution_model.components[12].supply['Supply']['Oxygen'].initial_amount = 300
        system.time_step = 3
        system.receive_patients()        
        system.update()        
        distribution_model.distribute()
        assert system.components[1].patients[0].demand_met[0]['Oxygen'] == 0.0
        assert system.components[2].patients[0].demand_met[1]['Oxygen'] == 0.0
        system.update_patients()
        assert system.components[1].patients[0].unmet_demand_info['Oxygen'] == [3]
        assert system.components[2].patients[0].unmet_demand_info['Oxygen'] == [3]

        distribution_model.components[11].supply['Supply']['Oxygen'].current_amount = 360
        distribution_model.components[11].supply['Supply']['Oxygen'].initial_amount = 360
        distribution_model.components[12].supply['Supply']['Oxygen'].current_amount = 360
        distribution_model.components[12].supply['Supply']['Oxygen'].initial_amount = 360
        system.time_step = 4
        system.receive_patients()        
        system.update() 
        distribution_model.distribute()
        assert system.components[1].patients[0].demand_met[0]['Oxygen'] == 1.0    
        system.update_resilience_calculators()      
        system.update()       
        assert distribution_model.components[11].supply['Supply']['Oxygen'].current_amount == 0
        assert distribution_model.components[12].supply['Supply']['Oxygen'].current_amount == 360       
     
class TestTimeStepsOfAutonomyDistributionModel(TestHospitalDistributionModel):
    
    def test_drugs_distribution(self):
        system = self.initiate_system(self.EXCEL_INPUT_1)
        system.components[0].patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][7]['ResourceAmount'] = 1
        system.components[0].patient_library['Patient 1'][1]['OperatingTheater']['ResourcesRequired'][7]['ResourceAmount'] = 1
        distribution_model = system.resources['MedicalDrugs']['DistributionModel']
        # Pharmacy
        distribution_model.components[10].supply['Supply']['MedicalDrugs'].current_amount = 1
        distribution_model.components[10].supply['Supply']['MedicalDrugs'].initial_amount = 1

        system.set_initial_damage()
        system.time_step = 1
        system.receive_patients()        
        system.update()        
        distribution_model.distribute()
        assert system.components[1].patients[0].demand_met[0]['MedicalDrugs'] == 1
        system.update_patients()
        system.update_resilience_calculators()

        system.time_step = 2
        system.receive_patients()        
        system.update()        
        distribution_model.distribute()
        assert system.components[1].patients[0].demand_met[0]['MedicalDrugs'] == 0
        assert system.components[2].patients[0].demand_met[1]['MedicalDrugs'] == 0
        system.update_patients()
        assert system.components[1].patients[0].unmet_demand_info['MedicalDrugs'] == [2]
        assert system.components[2].patients[0].unmet_demand_info['MedicalDrugs'] == [2]
        system.update_resilience_calculators()    

        distribution_model.components[10].supply['Supply']['MedicalDrugs'].current_amount = 5
        distribution_model.components[10].supply['Supply']['MedicalDrugs'].initial_amount = 5
        for time_step in range(3, 7):
            system.time_step = time_step
            system.receive_patients()        
            system.update()        
            distribution_model.distribute()
            assert system.components[1].patients[0].demand_met[0]['MedicalDrugs'] == 1
            assert system.components[2].patients[0].demand_met[1]['MedicalDrugs'] == 1
            assert system.components[2].patients[1].demand_met[1]['MedicalDrugs'] == 1
            system.update_patients()
            system.update_resilience_calculators()

        system.time_step = 8
        system.receive_patients()        
        system.update()        
        distribution_model.distribute()
        assert system.components[1].patients[0].demand_met[0]['MedicalDrugs'] == 0
        assert system.components[2].patients[0].demand_met[1]['MedicalDrugs'] == 0
        assert system.components[2].patients[1].demand_met[1]['MedicalDrugs'] == 0
        system.update_patients()
        assert system.components[1].patients[0].unmet_demand_info['MedicalDrugs'] == [8]
        assert system.components[2].patients[0].unmet_demand_info['MedicalDrugs'] == [8]
        assert system.components[2].patients[1].unmet_demand_info['MedicalDrugs'] == [8]


