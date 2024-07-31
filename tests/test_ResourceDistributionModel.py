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
    component_library_file = "./tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_ComponentLibrary.json"
    system_configuration_file = './tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_SystemConfiguration.json'

    @pytest.fixture
    def system_creator(self):
        return SystemCreator.JSONSystemCreator()

    @pytest.fixture
    def component_library(self):
        return ComponentLibraryCreator.JSONComponentLibraryCreator(self.component_library_file).form_library()

    @pytest.fixture
    def system(self, system_creator, component_library):
        system = System.BuiltEnvironmentSystem(self.system_configuration_file, component_library, system_creator)
        system.time_step = 0
        # set_bsu_communication_resource_name(system.components)
        return system

    @pytest.fixture
    def distribution_models(self, system_creator, component_library):
        system_creator.setup(component_library, self.system_configuration_file)
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
    component_library_file = "./Example 1/ThreeLocalitiesCommunity_ComponentLibrary.json"
    system_configuration_file = './Example 1/ThreeLocalitiesCommunity.json'

    @pytest.fixture
    def system_creator(self):
        return SystemCreator.JSONSystemCreator()

    @pytest.fixture
    def component_library(self):
        return ComponentLibraryCreator.JSONComponentLibraryCreator(self.component_library_file).form_library()

    @pytest.fixture
    def system(self, system_creator, component_library):
        system = System.BuiltEnvironmentSystem(self.system_configuration_file, component_library, system_creator)
        set_bsu_communication_resource_name(system.components)
        return system

    @pytest.fixture
    def distribution_models(self, system_creator, component_library):
        system_creator.setup(component_library, self.system_configuration_file)
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
        reduced_supply_of_the_power_plant = [0.0, 0.0, 0.0]
        reduced_supply_of_the_base_station = [0.0, 0.0, 0.0]
        bool_list = []
        for power_plant_supply, base_station_supply, distribution_model in zip(reduced_supply_of_the_power_plant,
                                                                               reduced_supply_of_the_base_station,
                                                                               distribution_models.values()):
            distribution_model.reduce_component_supply(power_plant_row_id, percent_of_met_demand)
            distribution_model.reduce_component_supply(base_station_row_id, percent_of_met_demand)
            bool_list.append(math.isclose(distribution_model.system_matrix.get_current_resource_amount(
                distribution_model.components[power_plant_row_id], Component.SupplyOrDemand.SUPPLY.value, 'Supply'),
                power_plant_supply))
            bool_list.append(math.isclose(distribution_model.system_matrix.get_current_resource_amount(
                distribution_model.components[base_station_row_id], Component.SupplyOrDemand.SUPPLY.value, 'Supply'),
                base_station_supply))
        assert all(bool_list)

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
            current_supply = distribution_model.get_system_supply()
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
            current_supply = distribution_model.get_system_supply()
            bool_list.append(math.isclose(target_supply, current_supply))

        assert all(bool_list)

    def test_get_system_demand_no_damage(self, distribution_models: dict):
        target_demands = [4.0, 1.0, 3.0]
        bool_list = []
        for target_demand, distribution_model in zip(target_demands, distribution_models.values()):
            distribution_model.fill_system_matrix()
            current_demand = distribution_model.get_system_demand()
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
            current_demand = distribution_model.get_system_demand()
            bool_list.append(math.isclose(target_demand, current_demand))

        assert all(bool_list)

    def test_get_system_consumption_no_damage(self, distribution_models: dict):
        target_consumptions = [4.0, 1.0, 3.0]
        bool_list = []
        for target_consumption, distribution_model in zip(target_consumptions, distribution_models.values()):
            distribution_model.fill_system_matrix()
            current_consumption = distribution_model.get_system_consumption()
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
            current_consumption = distribution_model.get_system_consumption()
            bool_list.append(math.isclose(target_demand, current_consumption))

        assert all(bool_list)


class TestUtilityDistributionModel_NorthEast_SF():
    component_library_file = "./tests/test_inputs/test_inputs_NorthEast_SF_Housing_ComponentLibrary.json"
    system_configuration_file = "./tests/test_inputs/test_inputs_NorthEast_SF_Housing_SystemConfiguration.json"
    recovery_resource_supply = {"FirstResponderEngineer": 5,
                                "SeniorEngineer": 4,
                                "Contractor": 10,
                                "Money": 5500000000,
                                "PlanCheckEngineeringTeam": 10,
                                "SitePreparationCrew": 10,
                                "CleanUpCrew": 10,
                                "EngineeringDesignTeam": 10,
                                "DemolitionCrew": 10,
                                "RepairCrew": 500}
   
    @pytest.fixture
    def system_creator(self):
        return SystemCreator.R2DSystemCreator()

    @pytest.fixture
    def component_library(self):
        return ComponentLibraryCreator.JSONComponentLibraryCreator(self.component_library_file).form_library()

    @pytest.fixture
    def system(self, system_creator, component_library):
        system = System.BuiltEnvironmentSystem(self.system_configuration_file, component_library, system_creator)
        return system

    @pytest.fixture
    def distribution_models(self, system_creator, component_library):
        system_creator.setup(component_library, self.system_configuration_file)
        components = system_creator.create_components()
        set_bsu_communication_resource_name(components)
        self.set_recovery_resource_supply(components)   
        resources = system_creator.get_resource_parameters(components)        
        distribution_models = {resource_name: resource_parameters['DistributionModel'] for resource_name, resource_parameters in resources.items()}
        return distribution_models

    def set_recovery_resource_supply(self, components: list([Component.Component])):
        emergency_response_center = components[0]
        for resource_name, resource_amount in self.recovery_resource_supply.items():
            emergency_response_center.supply['Supply'][resource_name].initial_amount = resource_amount
            emergency_response_center.supply['Supply'][resource_name].current_amount = resource_amount

    def test_housing_distribution_no_damage(self, distribution_models: dict):
        distribution_models['Housing'].distribute()
        bool_list = []
        target_total_supply = 0
        for component in distribution_models['Housing'].components[1:]:
            bool_list.append(
                component.supply['Supply']['Housing'].current_amount == component.demand['OperationDemand'][
                    'Housing'].current_amount)
            target_total_supply += component.supply['Supply']['Housing'].current_amount
        bool_list.append(target_total_supply == distribution_models['Housing'].get_system_consumption())
        bool_list.append(target_total_supply == distribution_models['Housing'].get_system_supply())
        assert all(bool_list)

    def test_housing_distribution_with_damage(self, system: System.System, distribution_models: dict):
        system.set_initial_damage()
        system.update()
        distribution_models['Housing'].components = system.components
        distribution_models['Housing'].distribute()
        bool_list = []
        target_total_supply = 0
        target_total_demand = 0
        for component in distribution_models['Housing'].components[1:]:      
            if component.name in ['DS0_ResidentialBuilding', 'DS1_ResidentialBuilding']:
                bool_list.append(component.supply['Supply']['Housing'].current_amount == component.demand['OperationDemand']['Housing'].current_amount)                
                target_total_supply += component.supply['Supply']['Housing'].current_amount
            else:
                bool_list.append(math.isclose(component.supply['Supply']['Housing'].current_amount, 0))
            bool_list.append(component.supply['Supply']['Housing'].initial_amount == component.demand['OperationDemand']['Housing'].current_amount)
            target_total_demand += component.demand['OperationDemand']['Housing'].current_amount

        bool_list.append(math.isclose(target_total_supply, distribution_models['Housing'].get_system_consumption()))
        bool_list.append(math.isclose(target_total_supply, distribution_models['Housing'].get_system_supply()))
        bool_list.append(target_total_demand == distribution_models['Housing'].get_system_demand())
        assert all(bool_list)

    def test_recovery_resource_distribution_no_damage(self, distribution_models: dict):
        bool_list = []
        for resource_name, distribution_model in distribution_models.items():
            if not (resource_name == 'Housing'):
                distribution_model.distribute()
                bool_list.append(distribution_model.get_system_consumption() == 0)
                bool_list.append(distribution_model.get_system_demand() == 0)
                bool_list.append(distribution_model.get_system_supply() == self.recovery_resource_supply[resource_name])

        for component in distribution_models['Housing'].components:
            for recovery_activity in component.recovery_model.recovery_activities.values():
                bool_list.append(recovery_activity.demand_met == 1.0)

        assert all(bool_list)

    def test_rapid_inspection_distribution_with_damage(self, system: System.System, distribution_models: dict):
        system.set_initial_damage()
        system.update()  

        bool_list = []               
        self.set_recovery_resource_supply(system.components)
        distribution_models['FirstResponderEngineer'].components = system.components
        distribution_models['FirstResponderEngineer'].distribute()
        bool_list.append(math.isclose(distribution_models['FirstResponderEngineer'].get_system_consumption(), 8*0.1))
        bool_list.append(math.isclose(distribution_models['FirstResponderEngineer'].get_system_demand(), 8*0.1))
        bool_list.append(distribution_models['FirstResponderEngineer'].get_system_supply() == self.recovery_resource_supply['FirstResponderEngineer'])
        
        for component in distribution_models['FirstResponderEngineer'].components:
            for recovery_activity in component.recovery_model.recovery_activities.values():
                bool_list.append(recovery_activity.demand_met == 1.0)
  
        assert all(bool_list)

    def test_detailed_inspection_distribution_with_damage(self, system: System.System, distribution_models: dict):
        system.set_initial_damage()
        system.update()
        self.set_recovery_resource_supply(system.components)
        system.recover()   
        system.update()        
        bool_list = []                       
        demand_per_component = 2
        components_with_demand_id = [component_id for component_id, component in enumerate(system.components) if 'SeniorEngineer' in component.demand['RecoveryDemand']]         
        distribution_models['SeniorEngineer'].components = system.components
        distribution_models['SeniorEngineer'].distribute()
        component_priorities, demand_type = distribution_models['SeniorEngineer'].get_component_priorities()              
        bool_list.append(math.isclose(distribution_models['SeniorEngineer'].get_system_consumption(), min(self.recovery_resource_supply['SeniorEngineer'], len(components_with_demand_id)*demand_per_component)))
        bool_list.append(math.isclose(distribution_models['SeniorEngineer'].get_system_demand(), len(components_with_demand_id)*demand_per_component))
        bool_list.append(distribution_models['SeniorEngineer'].get_system_supply() == self.recovery_resource_supply['SeniorEngineer'])
        num_components_with_met_demand = math.floor(self.recovery_resource_supply['SeniorEngineer'] / demand_per_component)
        counter = 0
        for component_offset_id in component_priorities[1:]:  
            component_id = component_offset_id - distribution_models['SeniorEngineer'].system_matrix.RECOVERY_DEMAND_ROW_OFFSET
            component = system.components[component_id]                        
            if component.name in ['DS2_ResidentialBuilding', 'DS3_ResidentialBuilding', 'DS4_ResidentialBuilding'] and component_id in components_with_demand_id:
                if counter < num_components_with_met_demand:
                    bool_list.append(component.recovery_model.recovery_activities['DetailedInspection'].demand_met == 1.0)
                    counter += 1
                else:
                    bool_list.append(component.recovery_model.recovery_activities['DetailedInspection'].demand_met == 0.0)             
        assert all(bool_list)

    def test_set_unmet_demand_for_recovery_activities(self, distribution_models: dict):
        pass

class TestTimeStepsOfAutonomyDistributionModel():
    
    FILENAME = './tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_Main.json'

    @pytest.fixture
    def system(self):
        input_dict = main.read_file(self.FILENAME)
        system = main.create_system(input_dict)
        return system

    @pytest.fixture
    def distribution_models(self, system_creator, component_library):
        system_creator.setup(component_library, self.system_configuration_file)
        components = system_creator.create_components()
        set_bsu_communication_resource_name(components)
        self.set_recovery_resource_supply(components)
        resources = system_creator.get_resource_parameters(components)
        distribution_models = {resource_name: resource_parameters['DistributionModel'] for resource_name, resource_parameters in resources.items()}
        return distribution_models
