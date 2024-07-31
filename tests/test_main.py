from pyrecodes_hospitals import main
import math
import numpy as np
from pyrecodes_hospitals import System

class TestMain():
   
    MAIN_FILE = './tests/test_inputs/test_inputs_Hospital_Main.json'
    EXCEL_INPUT_1 = './tests/test_inputs/test_inputs_Hospital_ExcelInput1.xlsx'
    EXCEL_INPUT_2 = './tests/test_inputs/test_inputs_Hospital_ExcelInput2.xlsx'
    EXCEL_INPUT_3 = './tests/test_inputs/test_inputs_Hospital_ExcelInput3.xlsx'
    ADDITIONAL_DATA_LOCATION = './tests/test_inputs/'
    MCI_SCENARIO_PARAMETERS = {} # change this to a file location test_inputs_MCI....

    def test_form_component_library(self):
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)        
        component_library = main.form_component_library(input_dict)
        assert isinstance(component_library, dict)

    def test_create_system(self):
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)        
        system = main.create_system(input_dict)
        assert isinstance(system, System.HospitalSystem)
    
    def test_get_patient_types(self):
        excel_input = main.read_excel_input(self.EXCEL_INPUT_1)
        patient_types = main.get_patient_types(excel_input)
        assert patient_types == ['Patient 1']

        excel_input = main.read_excel_input(self.EXCEL_INPUT_2)
        patient_types = main.get_patient_types(excel_input)
        assert patient_types == ['Red', 'Yellow', 'Green', 'Blue']

        excel_input = main.read_excel_input(self.EXCEL_INPUT_3)
        patient_types = main.get_patient_types(excel_input)
        assert patient_types == ['MinorSurgical Red', 'MajorSurgical Red', 'Green', 'Inpatient', 'HDU Patient', 'Blue']
    
    def test_format_component_library_file(self):
        excel_input = main.read_excel_input(self.EXCEL_INPUT_1)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        main.format_component_library_file(excel_input, input_dict, self.ADDITIONAL_DATA_LOCATION)
        component_library = main.read_file(input_dict['ComponentLibrary']['ComponentLibraryFile'])
        assert isinstance(component_library, dict)
        assert list(component_library['PatientSource']['OperationDemand'].keys()) == ['Patient 1']
        assert component_library['EmergencyDepartment']['Supply']['EmergencyDepartment_Bed']['Amount'] == 20
        assert component_library['EmergencyDepartment']['OperationDemand']['Nurse']['Amount'] == 0
        assert component_library['EmergencyDepartment']['OperationDemand']['Nurse']['MinMaxConstraints']['Min'] == 5
        assert component_library['EmergencyDepartment']['OperationDemand']['Nurse']['MinMaxConstraints']['Max'] == 1000

        assert component_library['OperatingTheater']['Supply']['OperatingTheater_Bed']['Amount'] == 5
        assert component_library['OperatingTheater']['OperationDemand']['Nurse']['Amount'] == 0
        assert component_library['OperatingTheater']['OperationDemand']['Nurse']['MinMaxConstraints']['Min'] == 0
        assert component_library['OperatingTheater']['OperationDemand']['Nurse']['MinMaxConstraints']['Max'] == 1000
        assert component_library['OperatingTheater']['OperationDemand']['ElectricPower']['Amount'] == 1

        assert component_library['Medical/SurgicalDepartment']['Supply']['Medical/SurgicalDepartment_Bed']['Amount'] == 100
        assert component_library['Medical/SurgicalDepartment']['OperationDemand']['Nurse']['Amount'] == 0
        assert component_library['Medical/SurgicalDepartment']['OperationDemand']['Nurse']['MinMaxConstraints']['Min'] == 20
        assert component_library['Medical/SurgicalDepartment']['OperationDemand']['Nurse']['MinMaxConstraints']['Max'] == 1000
        assert component_library['Medical/SurgicalDepartment']['OperationDemand']['ElectricPower']['Amount'] == 1

        assert component_library['HighDependencyUnit']['Supply']['HighDependencyUnit_Bed']['Amount'] == 50
        assert component_library['HighDependencyUnit']['OperationDemand']['Nurse']['Amount'] == 0
        assert component_library['HighDependencyUnit']['OperationDemand']['Nurse']['MinMaxConstraints']['Min'] == 10
        assert component_library['HighDependencyUnit']['OperationDemand']['Nurse']['MinMaxConstraints']['Max'] == 1000
        assert component_library['HighDependencyUnit']['OperationDemand']['ElectricPower']['Amount'] == 1

        assert component_library['RestOfHospital']['Supply']['RestOfHospital_Bed']['Amount'] == 100
        assert component_library['RestOfHospital']['OperationDemand']['Nurse']['Amount'] == 0
        assert component_library['RestOfHospital']['OperationDemand']['Nurse']['MinMaxConstraints']['Min'] == 40
        assert component_library['RestOfHospital']['OperationDemand']['Nurse']['MinMaxConstraints']['Max'] == 1000
        assert component_library['RestOfHospital']['OperationDemand']['ElectricPower']['Amount'] == 1

        assert component_library['HumanResources']['Supply']['Nurse']['Amount'] == 200

        assert component_library['ElectricPowerSupplySystem']['OperationDemand']['Fuel']['Amount'] == 500
        assert component_library['FuelReservoir']['Supply']['Fuel']['Amount'] == 10000

        assert component_library['WaterSupplySystem']['OperationDemand']['Water']['Amount'] == 5
        assert component_library['WaterSupplySystem']['Supply']['Water']['Amount'] == 1000

        assert component_library['OxygenReservoir']['Supply']['Oxygen']['Amount'] == 100
        assert component_library['OxygenConcentrator']['Supply']['Oxygen']['Amount'] == 1000

        assert component_library['Pharmacy']['Supply']['MCI_Kit_NonWalking_EmergencyDepartment']['Amount'] == 100
        assert component_library['Pharmacy']['Supply']['MCI_Kit_NonWalking_OperatingTheater']['Amount'] == 100
        assert component_library['Pharmacy']['Supply']['MCI_Kit_NonWalking_HighDependencyUnit']['Amount'] == 100
        assert component_library['Pharmacy']['Supply']['MCI_Kit_Walking_EmergencyDepartment']['Amount'] == 100
        assert component_library['Pharmacy']['Supply']['MedicalDrugs']['Amount'] == 24

        assert component_library['OperatingTheater']['Supply']['OperatingTheater_Bed']['Amount'] == 5
        assert component_library['EmergencyDepartment']['Supply']['EmergencyDepartment_Bed']['Amount'] == 20
        assert component_library['HighDependencyUnit']['Supply']['HighDependencyUnit_Bed']['Amount'] == 50
        assert component_library['Medical/SurgicalDepartment']['Supply']['Medical/SurgicalDepartment_Bed']['Amount'] == 100
        assert component_library['RestOfHospital']['Supply']['RestOfHospital_Bed']['Amount'] == 100

        assert component_library['BloodBank']['Supply']['Blood']['Amount'] == 500    

    def test_format_stress_scenario_patients(self):
        excel_input = main.read_excel_input(self.EXCEL_INPUT_1)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        stress_scenario_dict = main.read_file(main.read_file(input_dict['System']['SystemConfigurationFile'])['DamageInput']['Parameters'])
        main.clean_stress_scenario_dict(stress_scenario_dict)
        main.format_stress_scenario_patients(excel_input, stress_scenario_dict, self.ADDITIONAL_DATA_LOCATION)
        
        assert stress_scenario_dict['StressScenarioName'] == 'Test Scenario 1'
        assert stress_scenario_dict['ComponentsToChange'][0]['ComponentName'] == 'PatientSource'
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][0]['Resource'] == 'Patient 1'
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][0]['AtTimeStep'] == list(range(11))
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][0]['Amount'] == [0] + [1]*10

        excel_input = main.read_excel_input(self.EXCEL_INPUT_2)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        stress_scenario_dict = main.read_file(main.read_file(input_dict['System']['SystemConfigurationFile'])['DamageInput']['Parameters'])
        main.clean_stress_scenario_dict(stress_scenario_dict)
        main.format_stress_scenario_patients(excel_input, stress_scenario_dict, self.ADDITIONAL_DATA_LOCATION)
        
        assert stress_scenario_dict['StressScenarioName'] == 'Test Scenario 2'

        assert stress_scenario_dict['ComponentsToChange'][0]['ComponentName'] == 'PatientSource'
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][0]['Resource'] == 'Red'
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][0]['AtTimeStep'] == list(range(21))
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][0]['Amount'] == [0] + [1]*15 + [0]*5

        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][1]['Resource'] == 'Yellow'
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][1]['AtTimeStep'] == list(range(21))
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][1]['Amount'] == [0] + [2] + [1]*19

        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][2]['Resource'] == 'Green'
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][2]['AtTimeStep'] == list(range(21))
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][2]['Amount'] == [0] + [22] + [6]*19

        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][3]['Resource'] == 'Blue'
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][3]['AtTimeStep'] == list(range(21))
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][3]['Amount'] == [0] + [5] + [0]*6 + [5] +[0]*6 + [5] + [0]*5

    def test_format_stress_scenario_supply_increase_due_to_restocking(self):
        excel_input = main.read_excel_input(self.EXCEL_INPUT_1)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        stress_scenario_dict = main.read_file(main.read_file(input_dict['System']['SystemConfigurationFile'])['DamageInput']['Parameters'])
        main.clean_stress_scenario_dict(stress_scenario_dict)
        main.format_stress_scenario_supply_increase_due_to_restocking(excel_input, stress_scenario_dict, self.ADDITIONAL_DATA_LOCATION)

        assert stress_scenario_dict['ComponentsToChange'][1]['ComponentName'] == 'WaterSupplySystem'
        assert stress_scenario_dict['ComponentsToChange'][1]['ResourcesToChange'][0]['Resource'] == 'Water'
        assert stress_scenario_dict['ComponentsToChange'][1]['ResourcesToChange'][0]['AtTimeStep'] == [5]
        assert stress_scenario_dict['ComponentsToChange'][1]['ResourcesToChange'][0]['Amount'] == [30000]

        assert stress_scenario_dict['ComponentsToChange'][2]['ComponentName'] == 'FuelReservoir'
        assert stress_scenario_dict['ComponentsToChange'][2]['ResourcesToChange'][0]['Resource'] == 'Fuel'
        assert stress_scenario_dict['ComponentsToChange'][2]['ResourcesToChange'][0]['AtTimeStep'] == [6]
        assert stress_scenario_dict['ComponentsToChange'][2]['ResourcesToChange'][0]['Amount'] == [50000]

        assert stress_scenario_dict['ComponentsToChange'][3]['ComponentName'] == 'Pharmacy'
        assert stress_scenario_dict['ComponentsToChange'][3]['ResourcesToChange'][0]['Resource'] == 'MedicalDrugs'
        assert stress_scenario_dict['ComponentsToChange'][3]['ResourcesToChange'][0]['AtTimeStep'] == [12]
        assert stress_scenario_dict['ComponentsToChange'][3]['ResourcesToChange'][0]['Amount'] == [96]

        assert stress_scenario_dict['ComponentsToChange'][4]['ComponentName'] == 'OxygenReservoir'
        assert stress_scenario_dict['ComponentsToChange'][4]['ResourcesToChange'][0]['Resource'] == 'Oxygen'
        assert stress_scenario_dict['ComponentsToChange'][4]['ResourcesToChange'][0]['AtTimeStep'] == [10]
        assert stress_scenario_dict['ComponentsToChange'][4]['ResourcesToChange'][0]['Amount'] == [2000]
    
    def test_format_stress_scenario_supply_increase(self):
        excel_input = main.read_excel_input(self.EXCEL_INPUT_1)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        stress_scenario_dict = main.read_file(main.read_file(input_dict['System']['SystemConfigurationFile'])['DamageInput']['Parameters'])
        main.clean_stress_scenario_dict(stress_scenario_dict)
        main.format_stress_scenario_bed_supply_increase(excel_input, stress_scenario_dict, self.ADDITIONAL_DATA_LOCATION)
        main.format_stress_scenario_supply_increase_due_to_restocking(excel_input, stress_scenario_dict, self.ADDITIONAL_DATA_LOCATION)

        assert stress_scenario_dict['ComponentsToChange'][1]['ComponentName'] == 'WaterSupplySystem'
        assert stress_scenario_dict['ComponentsToChange'][1]['ResourcesToChange'][0]['Resource'] == 'Water'
        assert stress_scenario_dict['ComponentsToChange'][1]['ResourcesToChange'][0]['AtTimeStep'] == [5]
        assert stress_scenario_dict['ComponentsToChange'][1]['ResourcesToChange'][0]['Amount'] == [30000]

        assert stress_scenario_dict['ComponentsToChange'][2]['ComponentName'] == 'FuelReservoir'
        assert stress_scenario_dict['ComponentsToChange'][2]['ResourcesToChange'][0]['Resource'] == 'Fuel'
        assert stress_scenario_dict['ComponentsToChange'][2]['ResourcesToChange'][0]['AtTimeStep'] == [6]
        assert stress_scenario_dict['ComponentsToChange'][2]['ResourcesToChange'][0]['Amount'] == [50000]

        assert stress_scenario_dict['ComponentsToChange'][3]['ComponentName'] == 'Pharmacy'
        assert stress_scenario_dict['ComponentsToChange'][3]['ResourcesToChange'][0]['Resource'] == 'MedicalDrugs'
        assert stress_scenario_dict['ComponentsToChange'][3]['ResourcesToChange'][0]['AtTimeStep'] == [12]
        assert stress_scenario_dict['ComponentsToChange'][3]['ResourcesToChange'][0]['Amount'] == [96]

        assert stress_scenario_dict['ComponentsToChange'][4]['ComponentName'] == 'OxygenReservoir'
        assert stress_scenario_dict['ComponentsToChange'][4]['ResourcesToChange'][0]['Resource'] == 'Oxygen'
        assert stress_scenario_dict['ComponentsToChange'][4]['ResourcesToChange'][0]['AtTimeStep'] == [10]
        assert stress_scenario_dict['ComponentsToChange'][4]['ResourcesToChange'][0]['Amount'] == [2000]

        assert stress_scenario_dict['ComponentsToChange'][5]['ComponentName'] == 'BloodBank'
        assert stress_scenario_dict['ComponentsToChange'][5]['ResourcesToChange'][0]['Resource'] == 'Blood'
        assert stress_scenario_dict['ComponentsToChange'][5]['ResourcesToChange'][0]['AtTimeStep'] == [10]
        assert stress_scenario_dict['ComponentsToChange'][5]['ResourcesToChange'][0]['Amount'] == [200]

        assert stress_scenario_dict['ComponentsToChange'][6]['ComponentName'] == 'EmergencyDepartment'
        assert stress_scenario_dict['ComponentsToChange'][6]['ResourcesToChange'][0]['Resource'] == 'EmergencyDepartment_Bed'
        assert stress_scenario_dict['ComponentsToChange'][6]['ResourcesToChange'][0]['AtTimeStep'] == [1]
        assert stress_scenario_dict['ComponentsToChange'][6]['ResourcesToChange'][0]['Amount'] == [20]

        assert stress_scenario_dict['ComponentsToChange'][7]['ComponentName'] == 'OperatingTheater'
        assert stress_scenario_dict['ComponentsToChange'][7]['ResourcesToChange'][0]['Resource'] == 'OperatingTheater_Bed'
        assert stress_scenario_dict['ComponentsToChange'][7]['ResourcesToChange'][0]['AtTimeStep'] == [1]
        assert stress_scenario_dict['ComponentsToChange'][7]['ResourcesToChange'][0]['Amount'] == [5]

        assert stress_scenario_dict['ComponentsToChange'][8]['ComponentName'] == 'HighDependencyUnit'
        assert stress_scenario_dict['ComponentsToChange'][8]['ResourcesToChange'][0]['Resource'] == 'HighDependencyUnit_Bed'
        assert stress_scenario_dict['ComponentsToChange'][8]['ResourcesToChange'][0]['AtTimeStep'] == [0]
        assert stress_scenario_dict['ComponentsToChange'][8]['ResourcesToChange'][0]['Amount'] == [10]

        assert stress_scenario_dict['ComponentsToChange'][9]['ComponentName'] == 'Medical/SurgicalDepartment'
        assert stress_scenario_dict['ComponentsToChange'][9]['ResourcesToChange'][0]['Resource'] == 'Medical/SurgicalDepartment_Bed'
        assert stress_scenario_dict['ComponentsToChange'][9]['ResourcesToChange'][0]['AtTimeStep'] == [0]
        assert stress_scenario_dict['ComponentsToChange'][9]['ResourcesToChange'][0]['Amount'] == [50]

        assert stress_scenario_dict['ComponentsToChange'][10]['ComponentName'] == 'RestOfHospital'
        assert stress_scenario_dict['ComponentsToChange'][10]['ResourcesToChange'][0]['Resource'] == 'RestOfHospital_Bed'
        assert stress_scenario_dict['ComponentsToChange'][10]['ResourcesToChange'][0]['AtTimeStep'] == [0]
        assert stress_scenario_dict['ComponentsToChange'][10]['ResourcesToChange'][0]['Amount'] == [-50]

        excel_input = main.read_excel_input(self.EXCEL_INPUT_2)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        stress_scenario_dict = main.read_file(main.read_file(input_dict['System']['SystemConfigurationFile'])['DamageInput']['Parameters'])
        main.clean_stress_scenario_dict(stress_scenario_dict)
        main.format_stress_scenario_bed_supply_increase(excel_input, stress_scenario_dict, self.ADDITIONAL_DATA_LOCATION)
        main.format_stress_scenario_supply_increase_due_to_restocking(excel_input, stress_scenario_dict, self.ADDITIONAL_DATA_LOCATION)

        assert stress_scenario_dict['ComponentsToChange'][1]['ComponentName'] == 'WaterSupplySystem'
        assert stress_scenario_dict['ComponentsToChange'][1]['ResourcesToChange'] == []

        assert stress_scenario_dict['ComponentsToChange'][2]['ComponentName'] == 'FuelReservoir'
        assert stress_scenario_dict['ComponentsToChange'][2]['ResourcesToChange'] == []

        assert stress_scenario_dict['ComponentsToChange'][3]['ComponentName'] == 'Pharmacy'
        assert stress_scenario_dict['ComponentsToChange'][3]['ResourcesToChange'] == []

        assert stress_scenario_dict['ComponentsToChange'][4]['ComponentName'] == 'OxygenReservoir'
        assert stress_scenario_dict['ComponentsToChange'][4]['ResourcesToChange'] == []

        assert stress_scenario_dict['ComponentsToChange'][5]['ComponentName'] == 'BloodBank'
        assert stress_scenario_dict['ComponentsToChange'][5]['ResourcesToChange'] == []

        assert stress_scenario_dict['ComponentsToChange'][6]['ComponentName'] == 'EmergencyDepartment'
        assert stress_scenario_dict['ComponentsToChange'][6]['ResourcesToChange'][0]['Resource'] == 'EmergencyDepartment_Bed'
        assert stress_scenario_dict['ComponentsToChange'][6]['ResourcesToChange'][0]['AtTimeStep'] == [1]
        assert stress_scenario_dict['ComponentsToChange'][6]['ResourcesToChange'][0]['Amount'] == [0]

        assert stress_scenario_dict['ComponentsToChange'][7]['ComponentName'] == 'OperatingTheater'
        assert stress_scenario_dict['ComponentsToChange'][7]['ResourcesToChange'][0]['Resource'] == 'OperatingTheater_Bed'
        assert stress_scenario_dict['ComponentsToChange'][7]['ResourcesToChange'][0]['AtTimeStep'] == [1]
        assert stress_scenario_dict['ComponentsToChange'][7]['ResourcesToChange'][0]['Amount'] == [0]

        assert stress_scenario_dict['ComponentsToChange'][8]['ComponentName'] == 'HighDependencyUnit'
        assert stress_scenario_dict['ComponentsToChange'][8]['ResourcesToChange'][0]['Resource'] == 'HighDependencyUnit_Bed'
        assert stress_scenario_dict['ComponentsToChange'][8]['ResourcesToChange'][0]['AtTimeStep'] == [0]
        assert stress_scenario_dict['ComponentsToChange'][8]['ResourcesToChange'][0]['Amount'] == [0]

        assert stress_scenario_dict['ComponentsToChange'][9]['ComponentName'] == 'Medical/SurgicalDepartment'
        assert stress_scenario_dict['ComponentsToChange'][9]['ResourcesToChange'][0]['Resource'] == 'Medical/SurgicalDepartment_Bed'
        assert stress_scenario_dict['ComponentsToChange'][9]['ResourcesToChange'][0]['AtTimeStep'] == [0]
        assert stress_scenario_dict['ComponentsToChange'][9]['ResourcesToChange'][0]['Amount'] == [0]

        assert stress_scenario_dict['ComponentsToChange'][10]['ComponentName'] == 'RestOfHospital'
        assert stress_scenario_dict['ComponentsToChange'][10]['ResourcesToChange'][0]['Resource'] == 'RestOfHospital_Bed'
        assert stress_scenario_dict['ComponentsToChange'][10]['ResourcesToChange'][0]['AtTimeStep'] == [0]
        assert stress_scenario_dict['ComponentsToChange'][10]['ResourcesToChange'][0]['Amount'] == [0]
   
    def test_add_supply_increase(self):
        # Tested in test_format_stress_scenario_supply_increase
        # No need to test again
        pass

    def test_add_bed_supply_increase(self):
        # Tested in test_format_stress_scenario_supply_increase
        # No need to test again
        pass

    def test_clean_stress_scenario_dict(self):
        stress_scenario_dict = {
            "StressScenarioName": "Test Scenario 1",
            "ComponentsToChange": [
                {
                    "ComponentName": "PatientSource",
                    "ResourcesToChange": [
                        {
                            "Resource": "Patient 1",
                            "AtTimeStep": list(range(11)),
                            "Amount": [0] + [1]*10
                        }
                    ]
                }
            ]
        }
        main.clean_stress_scenario_dict(stress_scenario_dict)
        assert stress_scenario_dict == {
            "StressScenarioName": "Test Scenario 1",
            "ComponentsToChange": [
                {
                    "ComponentName": "PatientSource",
                    "ResourcesToChange": []
                }
            ]
        }
    
    def test_format_stress_scenario_file(self):
        excel_input = main.read_excel_input(self.EXCEL_INPUT_1)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        main.format_stress_scenario_file(excel_input, self.MCI_SCENARIO_PARAMETERS, input_dict, self.ADDITIONAL_DATA_LOCATION)
        stress_scenario_dict = main.read_file(main.read_file(input_dict['System']['SystemConfigurationFile'])['DamageInput']['Parameters'])

        assert stress_scenario_dict['StressScenarioName'] == 'Test Scenario 1'
        assert stress_scenario_dict['ComponentsToChange'][0]['ComponentName'] == 'PatientSource'
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][0]['Resource'] == 'Patient 1'
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][0]['AtTimeStep'] == list(range(11))
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][0]['Amount'] == [0] + [1]*10

        assert stress_scenario_dict['ComponentsToChange'][1]['ComponentName'] == 'WaterSupplySystem'
        assert stress_scenario_dict['ComponentsToChange'][1]['ResourcesToChange'][0]['Resource'] == 'Water'
        assert stress_scenario_dict['ComponentsToChange'][1]['ResourcesToChange'][0]['AtTimeStep'] == [5]
        assert stress_scenario_dict['ComponentsToChange'][1]['ResourcesToChange'][0]['Amount'] == [30000]

        assert stress_scenario_dict['ComponentsToChange'][2]['ComponentName'] == 'FuelReservoir'
        assert stress_scenario_dict['ComponentsToChange'][2]['ResourcesToChange'][0]['Resource'] == 'Fuel'
        assert stress_scenario_dict['ComponentsToChange'][2]['ResourcesToChange'][0]['AtTimeStep'] == [6]
        assert stress_scenario_dict['ComponentsToChange'][2]['ResourcesToChange'][0]['Amount'] == [50000]

        assert stress_scenario_dict['ComponentsToChange'][3]['ComponentName'] == 'Pharmacy'
        assert stress_scenario_dict['ComponentsToChange'][3]['ResourcesToChange'][0]['Resource'] == 'MedicalDrugs'
        assert stress_scenario_dict['ComponentsToChange'][3]['ResourcesToChange'][0]['AtTimeStep'] == [12]
        assert stress_scenario_dict['ComponentsToChange'][3]['ResourcesToChange'][0]['Amount'] == [96]

        assert stress_scenario_dict['ComponentsToChange'][4]['ComponentName'] == 'OxygenReservoir'
        assert stress_scenario_dict['ComponentsToChange'][4]['ResourcesToChange'][0]['Resource'] == 'Oxygen'
        assert stress_scenario_dict['ComponentsToChange'][4]['ResourcesToChange'][0]['AtTimeStep'] == [10]
        assert stress_scenario_dict['ComponentsToChange'][4]['ResourcesToChange'][0]['Amount'] == [2000]

        assert stress_scenario_dict['ComponentsToChange'][5]['ComponentName'] == 'BloodBank'
        assert stress_scenario_dict['ComponentsToChange'][5]['ResourcesToChange'][0]['Resource'] == 'Blood'
        assert stress_scenario_dict['ComponentsToChange'][5]['ResourcesToChange'][0]['AtTimeStep'] == [10]
        assert stress_scenario_dict['ComponentsToChange'][5]['ResourcesToChange'][0]['Amount'] == [200]

        assert stress_scenario_dict['ComponentsToChange'][6]['ComponentName'] == 'EmergencyDepartment'
        assert stress_scenario_dict['ComponentsToChange'][6]['ResourcesToChange'][0]['Resource'] == 'EmergencyDepartment_Bed'
        assert stress_scenario_dict['ComponentsToChange'][6]['ResourcesToChange'][0]['AtTimeStep'] == [1]
        assert stress_scenario_dict['ComponentsToChange'][6]['ResourcesToChange'][0]['Amount'] == [20]

        assert stress_scenario_dict['ComponentsToChange'][7]['ComponentName'] == 'OperatingTheater'
        assert stress_scenario_dict['ComponentsToChange'][7]['ResourcesToChange'][0]['Resource'] == 'OperatingTheater_Bed'
        assert stress_scenario_dict['ComponentsToChange'][7]['ResourcesToChange'][0]['AtTimeStep'] == [1]
        assert stress_scenario_dict['ComponentsToChange'][7]['ResourcesToChange'][0]['Amount'] == [5]

        assert stress_scenario_dict['ComponentsToChange'][8]['ComponentName'] == 'HighDependencyUnit'
        assert stress_scenario_dict['ComponentsToChange'][8]['ResourcesToChange'][0]['Resource'] == 'HighDependencyUnit_Bed'
        assert stress_scenario_dict['ComponentsToChange'][8]['ResourcesToChange'][0]['AtTimeStep'] == [0]
        assert stress_scenario_dict['ComponentsToChange'][8]['ResourcesToChange'][0]['Amount'] == [10]

        assert stress_scenario_dict['ComponentsToChange'][9]['ComponentName'] == 'Medical/SurgicalDepartment'
        assert stress_scenario_dict['ComponentsToChange'][9]['ResourcesToChange'][0]['Resource'] == 'Medical/SurgicalDepartment_Bed'
        assert stress_scenario_dict['ComponentsToChange'][9]['ResourcesToChange'][0]['AtTimeStep'] == [0]
        assert stress_scenario_dict['ComponentsToChange'][9]['ResourcesToChange'][0]['Amount'] == [50]

        assert stress_scenario_dict['ComponentsToChange'][10]['ComponentName'] == 'RestOfHospital'
        assert stress_scenario_dict['ComponentsToChange'][10]['ResourcesToChange'][0]['Resource'] == 'RestOfHospital_Bed'
        assert stress_scenario_dict['ComponentsToChange'][10]['ResourcesToChange'][0]['AtTimeStep'] == [0]
        assert stress_scenario_dict['ComponentsToChange'][10]['ResourcesToChange'][0]['Amount'] == [-50]

        excel_input = main.read_excel_input(self.EXCEL_INPUT_2)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        main.format_stress_scenario_file(excel_input, self.MCI_SCENARIO_PARAMETERS, input_dict, self.ADDITIONAL_DATA_LOCATION)
        stress_scenario_dict = main.read_file(main.read_file(input_dict['System']['SystemConfigurationFile'])['DamageInput']['Parameters'])

        assert stress_scenario_dict['StressScenarioName'] == 'Test Scenario 2'

        assert stress_scenario_dict['ComponentsToChange'][0]['ComponentName'] == 'PatientSource'
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][0]['Resource'] == 'Red'
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][0]['AtTimeStep'] == list(range(21))
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][0]['Amount'] == [0] + [1]*15 + [0]*5

        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][1]['Resource'] == 'Yellow'
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][1]['AtTimeStep'] == list(range(21))
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][1]['Amount'] == [0] + [2] + [1]*19

        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][2]['Resource'] == 'Green'
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][2]['AtTimeStep'] == list(range(21))
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][2]['Amount'] == [0] + [22] + [6]*19

        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][3]['Resource'] == 'Blue'
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][3]['AtTimeStep'] == list(range(21))
        assert stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'][3]['Amount'] == [0] + [5] + [0]*6 + [5] +[0]*6 + [5] + [0]*5 

        assert stress_scenario_dict['ComponentsToChange'][1]['ComponentName'] == 'WaterSupplySystem'
        assert stress_scenario_dict['ComponentsToChange'][1]['ResourcesToChange'] == []

        assert stress_scenario_dict['ComponentsToChange'][2]['ComponentName'] == 'FuelReservoir'
        assert stress_scenario_dict['ComponentsToChange'][2]['ResourcesToChange'] == []

        assert stress_scenario_dict['ComponentsToChange'][3]['ComponentName'] == 'Pharmacy'
        assert stress_scenario_dict['ComponentsToChange'][3]['ResourcesToChange'] == []

        assert stress_scenario_dict['ComponentsToChange'][4]['ComponentName'] == 'OxygenReservoir'
        assert stress_scenario_dict['ComponentsToChange'][4]['ResourcesToChange'] == []

        assert stress_scenario_dict['ComponentsToChange'][5]['ComponentName'] == 'BloodBank'
        assert stress_scenario_dict['ComponentsToChange'][5]['ResourcesToChange'] == []

        assert stress_scenario_dict['ComponentsToChange'][6]['ComponentName'] == 'EmergencyDepartment'
        assert stress_scenario_dict['ComponentsToChange'][6]['ResourcesToChange'][0]['Resource'] == 'EmergencyDepartment_Bed'
        assert stress_scenario_dict['ComponentsToChange'][6]['ResourcesToChange'][0]['AtTimeStep'] == [1]
        assert stress_scenario_dict['ComponentsToChange'][6]['ResourcesToChange'][0]['Amount'] == [0]

        assert stress_scenario_dict['ComponentsToChange'][7]['ComponentName'] == 'OperatingTheater'
        assert stress_scenario_dict['ComponentsToChange'][7]['ResourcesToChange'][0]['Resource'] == 'OperatingTheater_Bed'
        assert stress_scenario_dict['ComponentsToChange'][7]['ResourcesToChange'][0]['AtTimeStep'] == [1]
        assert stress_scenario_dict['ComponentsToChange'][7]['ResourcesToChange'][0]['Amount'] == [0]

        assert stress_scenario_dict['ComponentsToChange'][8]['ComponentName'] == 'HighDependencyUnit'
        assert stress_scenario_dict['ComponentsToChange'][8]['ResourcesToChange'][0]['Resource'] == 'HighDependencyUnit_Bed'
        assert stress_scenario_dict['ComponentsToChange'][8]['ResourcesToChange'][0]['AtTimeStep'] == [0]
        assert stress_scenario_dict['ComponentsToChange'][8]['ResourcesToChange'][0]['Amount'] == [0]

        assert stress_scenario_dict['ComponentsToChange'][9]['ComponentName'] == 'Medical/SurgicalDepartment'
        assert stress_scenario_dict['ComponentsToChange'][9]['ResourcesToChange'][0]['Resource'] == 'Medical/SurgicalDepartment_Bed'
        assert stress_scenario_dict['ComponentsToChange'][9]['ResourcesToChange'][0]['AtTimeStep'] == [0]
        assert stress_scenario_dict['ComponentsToChange'][9]['ResourcesToChange'][0]['Amount'] == [0]

        assert stress_scenario_dict['ComponentsToChange'][10]['ComponentName'] == 'RestOfHospital'
        assert stress_scenario_dict['ComponentsToChange'][10]['ResourcesToChange'][0]['Resource'] == 'RestOfHospital_Bed'
        assert stress_scenario_dict['ComponentsToChange'][10]['ResourcesToChange'][0]['AtTimeStep'] == [0]
        assert stress_scenario_dict['ComponentsToChange'][10]['ResourcesToChange'][0]['Amount'] == [0]

    def test_format_patient_library_file(self):
        excel_input = main.read_excel_input(self.EXCEL_INPUT_1)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        main.format_component_library_file(excel_input, input_dict, self.ADDITIONAL_DATA_LOCATION, default_patient_library_file='test_inputs_Hospital_PatientTypeLibrary.json')
        main.format_patient_library_file(excel_input, input_dict, self.ADDITIONAL_DATA_LOCATION)
        patient_library = main.read_file(self.ADDITIONAL_DATA_LOCATION + 'test_inputs_Hospital_PatientTypeLibrary.json')

        assert list(patient_library.keys()) == ['Patient 1']
        assert len(patient_library['Patient 1']) == 4
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['BaselineLengthOfStay'] == 1
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['BaselineMortalityRate'] == 0.05

        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][0]['ResourceName'] == 'Nurse'
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][0]['ResourceAmount'] == 3
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][0]['ConsequencesOfUnmetDemand'][0] == {'Mortality Rate Increase [per missing nurse]': 1.2}

        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][1]['ResourceName'] == 'Water'
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][1]['ResourceAmount'] == 10
        assert list(patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][1]['ConsequencesOfUnmetDemand'][0].keys()) == ['None']

        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][2]['ResourceName'] == 'Oxygen'
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][2]['ResourceAmount'] == 720
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][2]['ConsequencesOfUnmetDemand'][0] == {'Death In [hours]': 0}

        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][3]['ResourceName'] == 'MCI_Kit_NonWalking_EmergencyDepartment'
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][3]['ResourceAmount'] == 1
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][3]['ConsequencesOfUnmetDemand'][0] == {'Death In [hours]': 1}

        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][4]['ResourceName'] == 'EmergencyDepartment_Bed'
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][4]['ResourceAmount'] == 1
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][4]['ConsequencesOfUnmetDemand'][0] == {'Death In [hours]': 0}

        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][5]['ResourceName'] == 'Blood'
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][5]['ResourceAmount'] == 3
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][5]['ConsequencesOfUnmetDemand'][0] == {'Death In [hours]': 1}

        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][6]['ResourceName'] == 'Stretcher'
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][6]['ResourceAmount'] == 1
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][6]['ConsequencesOfUnmetDemand'][0] == {'Death In [hours]': 0}

        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][7]['ResourceName'] == 'MedicalDrugs'
        assert patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][7]['ResourceAmount'] == 0
        assert list(patient_library['Patient 1'][0]['EmergencyDepartment']['ResourcesRequired'][7]['ConsequencesOfUnmetDemand'][0].keys()) == ['None']

        excel_input = main.read_excel_input(self.EXCEL_INPUT_2)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        main.format_patient_library_file(excel_input, input_dict, self.ADDITIONAL_DATA_LOCATION)
        patient_library = main.read_file(self.ADDITIONAL_DATA_LOCATION + 'test_inputs_Hospital_PatientTypeLibrary.json')

        assert list(patient_library.keys()) == ['Red', 'Yellow', 'Green', 'Blue']
        assert len(patient_library['Red']) == 4
        assert len(patient_library['Yellow']) == 5
        assert len(patient_library['Green']) == 2
        assert len(patient_library['Blue']) == 2

        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['BaselineLengthOfStay'] == 500
        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['BaselineMortalityRate'] == 0.0

        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][0]['ResourceName'] == 'Nurse'
        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][0]['ResourceAmount'] == 0.1
        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][0]['ConsequencesOfUnmetDemand'][0] == {'Mortality Rate Increase [per missing nurse]': 1.2}

        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][1]['ResourceName'] == 'Water'
        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][1]['ResourceAmount'] == 10
        assert list(patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][1]['ConsequencesOfUnmetDemand'][0].keys()) == ['None']

        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][2]['ResourceName'] == 'Oxygen'
        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][2]['ResourceAmount'] == 240
        assert list(patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][2]['ConsequencesOfUnmetDemand'][0].keys()) == ['None']

        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][3]['ResourceName'] == 'MCI_Kit_NonWalking_Medical/SurgicalDepartment'
        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][3]['ResourceAmount'] == 0
        assert list(patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][3]['ConsequencesOfUnmetDemand'][0].keys()) == ['None']

        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][4]['ResourceName'] == 'Medical/SurgicalDepartment_Bed'
        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][4]['ResourceAmount'] == 1
        assert list(patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][4]['ConsequencesOfUnmetDemand'][0].keys()) == ['None']

        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][5]['ResourceName'] == 'Blood'
        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][5]['ResourceAmount'] == 0
        assert list(patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][5]['ConsequencesOfUnmetDemand'][0].keys()) == ['None']

        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][6]['ResourceName'] == 'Stretcher'
        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][6]['ResourceAmount'] == 0
        assert list(patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][6]['ConsequencesOfUnmetDemand'][0].keys()) == ['None']

        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][7]['ResourceName'] == 'MedicalDrugs'
        assert patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][7]['ResourceAmount'] == 0
        assert list(patient_library['Blue'][0]['Medical/SurgicalDepartment']['ResourcesRequired'][7]['ConsequencesOfUnmetDemand'][0].keys()) == ['None']

    def test_modify_consumable_resource_demand(self):
        baseline_length_of_stay = 10
        demand_amount = 5
        assert main.modify_consumable_resource_demand(baseline_length_of_stay, demand_amount) == 0.5

        baseline_length_of_stay = 0
        demand_amount = 5
        assert main.modify_consumable_resource_demand(baseline_length_of_stay, demand_amount) == 0

        baseline_length_of_stay = 20
        demand_amount = 5
        assert main.modify_consumable_resource_demand(baseline_length_of_stay, demand_amount) == 5/20

    def test_format_system_configuration_file(self):
        excel_input = main.read_excel_input(self.EXCEL_INPUT_1)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        main.format_system_configuration_file(excel_input, input_dict, self.ADDITIONAL_DATA_LOCATION, default_stress_scenario_file='Example_StressScenario.json')
        system_configuration = main.read_file(input_dict['System']['SystemConfigurationFile'])
        patient_types = main.get_patient_types(excel_input)
        assert system_configuration['Constants']['MAX_TIME_STEP'] == 10
        assert system_configuration['DamageInput']['Parameters'] == self.ADDITIONAL_DATA_LOCATION + 'Example_StressScenario.json'
        assert system_configuration['ResilienceCalculator'][0]['Type'] == 'ReCoDeSResilienceCalculator'
        assert system_configuration['ResilienceCalculator'][0]['Parameters']['Scope'] == ['All']
        assert system_configuration['ResilienceCalculator'][0]['Parameters']['Resources'] == main.ALL_RESOURCES

        calculator_id = 0
        for department in main.DEPARTMENTS:
            calculator_id += 1
            assert system_configuration['ResilienceCalculator'][calculator_id]['Type'] == 'ReCoDeSResilienceCalculator'
            assert system_configuration['ResilienceCalculator'][calculator_id]['Parameters']['Scope'] == [department]
            assert system_configuration['ResilienceCalculator'][calculator_id]['Parameters']['Resources'] == main.RESOURCES_TO_PLOT

        for department in main.DEPARTMENTS:
            for patient_type in patient_types + ['All']:
                calculator_id += 1
                assert system_configuration['ResilienceCalculator'][calculator_id]['Type'] == 'HospitalMeasureOfServiceCalculator'
                assert system_configuration['ResilienceCalculator'][calculator_id]['Parameters']['Scope'] == [department]
                assert system_configuration['ResilienceCalculator'][calculator_id]['Parameters']['Resources'] == [patient_type]

        assert system_configuration['ResilienceCalculator'][-1]['Type'] == 'CauseOfDeathCalculator'
        assert system_configuration['ResilienceCalculator'][-1]['Parameters']['Scope'] == ['All']
        assert system_configuration['ResilienceCalculator'][-1]['Parameters']['Resources'] == ['All']      

    def test_set_max_time_step(self):
        excel_input = main.read_excel_input(self.EXCEL_INPUT_1)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        main.format_system_configuration_file(excel_input, input_dict, self.ADDITIONAL_DATA_LOCATION, default_stress_scenario_file='Example_StressScenario.json')
        system_configuration = main.read_file(input_dict['System']['SystemConfigurationFile'])
        assert system_configuration['Constants']['MAX_TIME_STEP'] == 10

        excel_input = main.read_excel_input(self.EXCEL_INPUT_2)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        main.format_system_configuration_file(excel_input, input_dict, self.ADDITIONAL_DATA_LOCATION, default_stress_scenario_file='Example_StressScenario.json')
        system_configuration = main.read_file(input_dict['System']['SystemConfigurationFile'])
        assert system_configuration['Constants']['MAX_TIME_STEP'] == 20

        excel_input = main.read_excel_input(self.EXCEL_INPUT_3)
        input_dict = main.read_main_file(self.MAIN_FILE, self.ADDITIONAL_DATA_LOCATION)
        main.format_system_configuration_file(excel_input, input_dict, self.ADDITIONAL_DATA_LOCATION, default_stress_scenario_file='Example_StressScenario.json')
        system_configuration = main.read_file(input_dict['System']['SystemConfigurationFile'])
        assert system_configuration['Constants']['MAX_TIME_STEP'] == 360
        
    def test_format_resilience_calculators(self):
        # Tested in test_format_system_configuration_file
        # No need to test again
        pass

    def test_update_default_dict(self):
        # Tested in other methods
        # No need to test again
        pass

    def test_get_value_from_excel_sheet_row_row(self):
        # Tested in other methods
        # No need to test again
        pass

    def test_get_value_from_excel_sheet_row_col(self):
        # Tested in other methods
        # No need to test again
        pass

    def test_get_mortality_rate_per_time_step(self):
        BIG_NUMBER = 10000000
        mortality_rate_during_entire_stay_list = [0.05, 0.0, 0.01, 0.05, 0.1, 0.5, 0.5, 1.0, 0.3, 0.3]
        length_of_stay_list = [1, 2, 10, 100, 5, 1, 2, 1, 10, 3]
        for mortality_rate_during_entire_stay, length_of_stay in zip(mortality_rate_during_entire_stay_list, length_of_stay_list):
            mortality_rate_per_time_step = main.get_mortality_rate_per_time_step(mortality_rate_during_entire_stay, length_of_stay)
            random_matrix = np.random.rand(BIG_NUMBER, length_of_stay)
            deaths_during_stay = np.sum(random_matrix < mortality_rate_per_time_step, axis=1)
            number_of_deaths = np.count_nonzero(deaths_during_stay == 1)
            assert math.isclose(number_of_deaths/BIG_NUMBER, mortality_rate_during_entire_stay, rel_tol=0.1)





