import pytest
from pyrecodes_hospitals import DamageInput
from pyrecodes_hospitals import SystemCreator
from pyrecodes_hospitals import System
from pyrecodes_hospitals import ComponentLibraryCreator
from pyrecodes_hospitals import main

class TestListDamageInput():
    system_configuration_file = './tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_SystemConfiguration.json'
    component_library_file = "./tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_ComponentLibrary.json"

    @pytest.fixture()
    def json_system_creator(self) -> SystemCreator.SystemCreator:
        return SystemCreator.JSONSystemCreator()

    def read_configuration_file(self, json_system_creator):
        json_system_creator.read_file(self.system_configuration_file)
        self.system_creator = json_system_creator

    def construct_damage_input(self, json_system_creator):
        self.read_configuration_file(json_system_creator)
        target_damage_input_class = getattr(DamageInput, self.system_creator.get_damage_input_type())
        self.damage_input = target_damage_input_class(self.system_creator.get_damage_input_parameters())

    def construct_system(self, json_system_creator):
        component_library = ComponentLibraryCreator.JSONComponentLibraryCreator(
            self.component_library_file).form_library()
        system = System.BuiltEnvironmentSystem(self.system_configuration_file, component_library, json_system_creator)
        self.system = system

    def test_get_initial_damage(self, json_system_creator):
        self.construct_damage_input(json_system_creator)
        self.damage_input.get_initial_damage()
        assert self.damage_input.damage_levels == [0.0, 0.4, 0.0, 0.0, 0.4, 0.0, 0.0, 0.4, 0.4, 0.0, 0.0]

    def test_set_initial_damage(self, json_system_creator):
        self.construct_system(json_system_creator)
        self.system.set_initial_damage()
        damage_levels = []
        for component in self.system.components:
            print(component)
            damage_levels.append(component.get_damage_level())
        assert damage_levels == [0.0, 0.4, 0.0, 0.0, 0.4, 0.0, 0.0, 0.4, 0.4, 0.0, 0.0]
    
# Test only the damage input class used for the Hospital Stress Scenario
class TestHospitalStressScenarioInput:

    PARAMETERS = './tests/test_inputs/test_inputs_Hospital_StressScenario.json'
    MAIN_FILE = './tests/test_inputs/test_inputs_Hospital_Main.json'
    EXCEL_INPUT_1 = './tests/test_inputs/test_inputs_Hospital_ExcelInput1.xlsx'
    ADDITIONAL_DATA_LOCATION = './tests/test_inputs/'
    MCI_SCENARIO_PARAMETERS = {}

    def test_get_initial_damage(self):
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        excel_input = main.read_excel_input(self.EXCEL_INPUT_1)
        main.format_input_from_excel(excel_input, self.MCI_SCENARIO_PARAMETERS, input_dict, self.ADDITIONAL_DATA_LOCATION, default_stress_scenario_file='test_inputs_Hospital_StressScenario.json')
        damage_input_parameters = main.read_file(input_dict['System']['SystemConfigurationFile'])['DamageInput']['Parameters']
        damage_input = DamageInput.HospitalStressScenarioInput(damage_input_parameters)
        damage_input.get_initial_damage()
        assert isinstance(damage_input.stress_scenario, dict)
    
    def test_set_initial_damage(self):
        excel_input = main.read_excel_input(self.EXCEL_INPUT_1)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        main.format_input_from_excel(excel_input, self.MCI_SCENARIO_PARAMETERS, input_dict, self.ADDITIONAL_DATA_LOCATION, default_stress_scenario_file='test_inputs_Hospital_StressScenario.json')
        system = main.create_system(input_dict)
        damage_input_parameters = main.read_file(input_dict['System']['SystemConfigurationFile'])['DamageInput']['Parameters']
        damage_input = DamageInput.HospitalStressScenarioInput(damage_input_parameters)
        damage_input.set_initial_damage(system.components)
        assert system.components[0].predefined_resource_dynamics == [{
                                                "Resource": "Patient 1",
                                                "SupplyOrDemand": "demand",
                                                "SupplyOrDemandType": "OperationDemand",
                                                "AtTimeStep": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                                                "Amount": [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
                                            }
                                        ]
        assert system.components[1].predefined_resource_dynamics == [
                                            {"Resource": "EmergencyDepartment_Bed",
                                            "SupplyOrDemand": "supply",
                                            "SupplyOrDemandType": "Supply",
                                            "AtTimeStep": [1],
                                            "Amount": [20]
                                            }
                                        ]