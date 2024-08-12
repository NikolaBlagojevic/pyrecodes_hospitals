import pytest
import numpy as np
import math
from pyrecodes_hospitals import main
from pyrecodes_hospitals import System
from pyrecodes_hospitals import SystemCreator
from pyrecodes_hospitals import ComponentLibraryCreator

class TestSystem():

    @pytest.fixture()
    def system_creator(self) -> SystemCreator.SystemCreator:
        return SystemCreator.JSONSystemCreator()

    @pytest.fixture()
    def component_library_creator(self) -> ComponentLibraryCreator.ComponentLibraryCreator:
        return ComponentLibraryCreator.JSONComponentLibraryCreator(self.COMPONENT_LIBRARY_FILE)

    @pytest.fixture()
    def system(self, system_creator: SystemCreator.SystemCreator, component_library_creator: ComponentLibraryCreator.ComponentLibraryCreator) -> System.System:
        component_library = component_library_creator.form_library()       
        system = System.BuiltEnvironmentSystem(self.SYSTEM_CONFIGURATION_FILE, component_library, system_creator)
        return system

class TestDistributionListCreator(TestSystem):

    COMPONENT_LIBRARY_FILE = "./tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_ComponentLibrary.json"
    SYSTEM_CONFIGURATION_FILE = './tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_SystemConfiguration.json'

    @pytest.fixture
    def distribution_list_creator(self, system: System.System):
        return System.DistributionListCreator(system.components, system.resources)

    def test_form_resource_distribution_vector(self, distribution_list_creator):
        interdependent_resources = ['ElectricPower', 'Communication', 'CoolingWater']
        vector = distribution_list_creator.form_resource_distribution_vector(interdependent_resources)
        assert vector == ['ElectricPower', 'Communication', 'CoolingWater', 'ElectricPower', 'Communication',
                          'CoolingWater', 'ElectricPower', 'Communication', 'CoolingWater']

    def test_get_independent_interdependent_resoruces_original(self, distribution_list_creator):
        target_interdependent_resources = ['ElectricPower', 'CoolingWater', 'Communication']
        resource_distribution_list = []
        independent_resources, interdependent_resources = distribution_list_creator.get_independent_interdependent_resources(
            resource_distribution_list)
        assert independent_resources == [] and interdependent_resources == target_interdependent_resources

    def test_get_resource_group(self, distribution_list_creator):
        assert distribution_list_creator.get_resource_group('Utilities') == ['ElectricPower', 'CoolingWater',
                                                                             'Communication']

    def test_get_resource_distribution_list(self, distribution_list_creator):
        target_list = ['ElectricPower', 'CoolingWater', 'Communication', 'ElectricPower', 'CoolingWater',
                       'Communication', 'ElectricPower', 'CoolingWater', 'Communication']
        assert distribution_list_creator.get_resource_distribution_list() == target_list

class TestThreeLocalitiesSystem(TestSystem):
    COMPONENT_LIBRARY_FILE = "./tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_ComponentLibrary.json"
    SYSTEM_CONFIGURATION_FILE = './tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_SystemConfiguration.json'    
    
    def test_initial_system_state(self, system: System.System):
        # //TODO: Implement. Check initial components' state, system supply, demand and consumption.
        pass

    def test_calculate_resilience(self, system: System.System):
        # //TODO: Implement when method is ready.
        pass

    def test_distribute_resources(self, system: System.System):
        system.distribute_resources()
        system.time_step = 0
        bool_list = []
        target_consumptions = [4, 1, 3]
        demand_col = system.resources['ElectricPower']['DistributionModel'].system_matrix.DEMAND_COL_ID
        demand_met_col = system.resources['ElectricPower']['DistributionModel'].system_matrix.DEMAND_MET_COL_ID
        for target_consumption, resource in zip(target_consumptions, system.resources.values()):
            consumption = np.sum(np.multiply(resource['DistributionModel'].system_matrix.matrix[:, demand_col],
                                             resource['DistributionModel'].system_matrix.matrix[:, demand_met_col]))
            bool_list.append(math.isclose(consumption, target_consumption, abs_tol=1e-10))

        system.set_initial_damage()
        system.update()
        system.distribute_resources()
        target_consumptions = [0, 0, 0]
        for target_consumption, resource in zip(target_consumptions, system.resources.values()):
            consumption = np.sum(np.multiply(resource['DistributionModel'].system_matrix.matrix[:, demand_col],
                                             resource['DistributionModel'].system_matrix.matrix[:, demand_met_col]))
            print(consumption)
            bool_list.append(math.isclose(consumption, target_consumption, abs_tol=1e-10))

        assert all(bool_list)

    def test_set_configuration_file(self, system: System.System):
        assert system.configuration_file == self.SYSTEM_CONFIGURATION_FILE

    def test_set_component_library(self, system: System.System, component_library_creator: dict):
        # //TODO: eq method implemented. Consider changing __init__ method for components
        # formed_component_library = component_library.form_library()
        # assert system.component_library == formed_component_library
        pass

    def test_set_initial_damage(self, system: System.System):
        target_damage_levels = [0.0, 0.4, 0.0, 0.0, 0.4, 0.0, 0.0, 0.4, 0.4, 0.0, 0.0]
        system.set_initial_damage()
        bool_list = []
        for target_damage_level, component in zip(target_damage_levels, system.components):
            bool_list.append(component.get_damage_level() == target_damage_level)
        assert all(bool_list)

    def test_update(self, system: System.System):
        bool_list = []
        system.time_step = 0
        for component in system.components:
            bool_list.append(component.functionality_level == 1)

        system.set_initial_damage()
        system.update()
        target_functionality_levels = [1.0, 0.6, 1.0, 1.0, 0.6, 1.0, 1.0, 0.6, 0.0, 1.0, 1.0]
        for target_functionality_level, component in zip(target_functionality_levels, system.components):
            bool_list.append(component.functionality_level == target_functionality_level)

        assert all(bool_list)

    def test_recovery_target_met(self, system: System.System):
        MAX_COMPONENT_REPAIR_DURATION = 10
        bool_list = []
        system.time_step = 0
        bool_list.append(system.recovery_target_met() == False)
        system.time_step = system.DISASTER_TIME_STEP
        bool_list.append(system.recovery_target_met() == False)
        system.set_initial_damage()
        bool_list.append(system.recovery_target_met() == False)
        for time_step in range(MAX_COMPONENT_REPAIR_DURATION):
            system.time_step = time_step       
            system.recover()            
        bool_list.append(system.recovery_target_met() == True)
        assert all(bool_list)

    def test_set_resource_distribution_list(self, system: System.System):
        assert system.resource_distribution_list == ['ElectricPower', 'CoolingWater', 'Communication', 'ElectricPower',
                                                     'CoolingWater', 'Communication', 'ElectricPower', 'CoolingWater',
                                                     'Communication']

    def test_set_system_creator(self, system: System.System):
        assert isinstance(system.system_creator, SystemCreator.JSONSystemCreator)

    def test_create_system(self, system: System.System):
        pass

    def test_init_(self):
        pass

    def test_start_resilience_assessment(self, system: System.System):
        pass

class TestHospitalSystem(TestSystem):

    MAIN_FILE = './tests/test_inputs/test_inputs_Hospital_Main.json'
    ADDITIONAL_DATA_LOCATION = './tests/test_inputs/'
    EXCEL_INPUT_1 = './tests/test_inputs/test_inputs_Hospital_ExcelInput1.xlsx'

    def create_system(self, excel_input) -> System.System:
        excel_input = main.read_excel_input(excel_input)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        main.format_input_from_excel(excel_input, {}, input_dict, self.ADDITIONAL_DATA_LOCATION, 
                                     default_patient_library_file='test_inputs_Hospital_PatientTypeLibrary.json',
                                     default_stress_scenario_file='test_inputs_Hospital_StressScenario.json')
        system = main.create_system(input_dict)
        return system
    
    def test_start_resilience_assessment(self, ):
        system = self.create_system(self.EXCEL_INPUT_1)
        system.start_resilience_assessment()
        # What else to test here?
        assert system.time_step == 10

    def test_update(self):
        system = self.create_system(self.EXCEL_INPUT_1)
        system.time_step = 0
        system.update()
        assert system.components[0].demand['OperationDemand']['Patient 1'].current_amount == 0
        assert system.components[1].supply['Supply']['EmergencyDepartment_Bed'].current_amount == 20
        assert system.components[1].demand['OperationDemand']['Nurse'].current_amount == 5
        # What else to test here?
    
    def test_receive_patients(self):
        system = self.create_system(self.EXCEL_INPUT_1)
        system.set_initial_damage()
        system.time_step = 0        
        system.receive_patients()
        for component in system.components:
            assert component.patients == []
        system.time_step = 1        
        system.receive_patients()
        for component in system.components:
            if component.name == 'EmergencyDepartment':
                assert len(component.patients) == 1
        system.time_step = 2   
        system.receive_patients()
        for component in system.components:
            if component.name == 'EmergencyDepartment':
                assert len(component.patients) == 2
        system.update()
        system.update_patients()
        system.distribute_resources()
        system.update_resilience_calculators()
        system.time_step = 3
        system.receive_patients()
        for component in system.components:
            if component.name == 'EmergencyDepartment':
                assert len(component.patients) == 1
            elif component.name == 'OperatingTheater':
                assert len(component.patients) == 2



        

