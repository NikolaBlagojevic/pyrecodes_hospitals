
from pyrecodes_hospitals import main
from pyrecodes_hospitals import ResilienceCalculator
import math
import random

INPUT_DICT = './tests/test_inputs/test_inputs_Hospital_Main.json'
EXCEL_INPUT_1 = './tests/test_inputs/test_inputs_Hospital_ExcelInput1.xlsx'
EXCEL_INPUT_2 = './tests/test_inputs/test_inputs_Hospital_ExcelInput2.xlsx'
EXCEL_INPUT_4 = './tests/test_inputs/test_inputs_Hospital_ExcelInput4.xlsx'
ADDITIONAL_DATA_LOCATION = './tests/test_inputs/'
MCI_SCENARIO_PARAMETERS = {}

def initiate_system(excel_input_file_name: str, additional_data_location: str):
    excel_input_data = main.read_excel_input(excel_input_file_name)
    input_dict = main.read_main_file(INPUT_DICT, additional_data_location)
    main.format_input_from_excel(excel_input_data, MCI_SCENARIO_PARAMETERS, input_dict, additional_data_location, 
                                 default_patient_library_file='test_inputs_Hospital_PatientLibrary.json',
                                 default_stress_scenario_file='test_inputs_Hospital_StressScenario.json')
    system = main.create_system(input_dict)
    return system

def run_system_time_step(system, time_step: int):
    system.time_step = time_step
    system.receive_patients()        
    system.update()
    system.distribute_resources()
    system.update_patients()    
    system.update_resilience_calculators()
    return system

class TestReCoDeSResilienceCalculator():

    PARAMETERS = {
                "Scope": ["All"],
                "Resources": [
                    "Nurse",
                    "Oxygen",
                    "EmergencyDepartment_Bed",
                    "Blood"
                ]
            }

    def test_init_(self):
        resilience_calculator = ResilienceCalculator.ReCoDeSResilienceCalculator(self.PARAMETERS)
        assert resilience_calculator.system_supply == {'Nurse': [], 'Oxygen': [], 'EmergencyDepartment_Bed': [], 'Blood': []}
        assert resilience_calculator.system_demand == {'Nurse': [], 'Oxygen': [], 'EmergencyDepartment_Bed': [], 'Blood': []}
        assert resilience_calculator.system_consumption == {'Nurse': [], 'Oxygen': [], 'EmergencyDepartment_Bed': [], 'Blood': []}
        assert resilience_calculator.resources == ['Nurse', 'Oxygen', 'EmergencyDepartment_Bed', 'Blood']
        assert resilience_calculator.scope == ['All']
    
    def test_calculate_resilience(self):
        resilience_calculator = ResilienceCalculator.ReCoDeSResilienceCalculator(self.PARAMETERS)
        resilience_calculator.system_demand = {'Nurse': [20, 25, 20], 'Oxygen': [0, 0, 0], 'EmergencyDepartment_Bed': [50, 50, 50], 'Blood': [10, 20, 30]}
        resilience_calculator.system_consumption = {'Nurse': [15, 20, 20], 'Oxygen': [0, 0, 0], 'EmergencyDepartment_Bed': [0, 0, 0], 'Blood': [5, 15, 25]}
        assert resilience_calculator.calculate_resilience() == {'Nurse': 10, 'Oxygen': 0, 'EmergencyDepartment_Bed': 150, 'Blood': 15}
    
    def test_update(self):
        system = initiate_system(EXCEL_INPUT_1, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage()
        system = run_system_time_step(system, 0)
        resilience_calculator = ResilienceCalculator.ReCoDeSResilienceCalculator(self.PARAMETERS)
        resilience_calculator.update(system.resources)
        assert resilience_calculator.system_supply == {'Nurse': [200], 'Oxygen': [1100], 'EmergencyDepartment_Bed': [20], 'Blood': [500]}     
        assert resilience_calculator.system_demand == {'Nurse': [75], 'Oxygen': [0], 'EmergencyDepartment_Bed': [0], 'Blood': [0]}
        assert resilience_calculator.system_consumption == {'Nurse': [75], 'Oxygen': [0], 'EmergencyDepartment_Bed': [0], 'Blood': [0]}

        system = run_system_time_step(system, 1)
        resilience_calculator.update(system.resources)
        assert resilience_calculator.system_supply == {'Nurse': [200, 200], 'Oxygen': [1100, 1100], 'EmergencyDepartment_Bed': [20, 40], 'Blood': [500, 500]}     
        assert math.isclose(resilience_calculator.system_demand['Nurse'][1], 75)
        assert resilience_calculator.system_demand['Oxygen'] == [0, 720]
        assert resilience_calculator.system_demand['EmergencyDepartment_Bed'] == [0, 1]
        assert resilience_calculator.system_demand['Blood'] == [0, 3]
        assert math.isclose(resilience_calculator.system_consumption['Nurse'][1], 75)
        assert resilience_calculator.system_consumption['Oxygen'] == [0, 720]
        assert resilience_calculator.system_consumption['EmergencyDepartment_Bed'] == [0, 1]
        assert resilience_calculator.system_consumption['Blood'] == [0, 3]

        system = run_system_time_step(system, 2)
        resilience_calculator.update(system.resources)
        assert resilience_calculator.system_supply == {'Nurse': [200, 200, 200], 'Oxygen': [1100, 1100, 1000], 'EmergencyDepartment_Bed': [20, 40, 40], 'Blood': [500, 500, 497]}
        assert math.isclose(resilience_calculator.system_demand['Nurse'][2], 76.5)
        assert resilience_calculator.system_demand['Oxygen'] == [0, 720, 1440]
        assert resilience_calculator.system_demand['EmergencyDepartment_Bed'] == [0, 1, 1]
        assert resilience_calculator.system_demand['Blood'] == [0, 3, 5]
        assert math.isclose(resilience_calculator.system_consumption['Nurse'][2], 76.5)
        assert resilience_calculator.system_consumption['Oxygen'] == [0, 720, 1000]
        assert resilience_calculator.system_consumption['EmergencyDepartment_Bed'] == [0, 1, 1]
        assert resilience_calculator.system_consumption['Blood'] == [0, 3, 5]

        system = run_system_time_step(system, 3)
        resilience_calculator.update(system.resources)
        assert resilience_calculator.system_supply == {'Nurse': [200, 200, 200, 200], 'Oxygen': [1100, 1100, 1000, 1000], 'EmergencyDepartment_Bed': [20, 40, 40, 40], 'Blood': [500, 500, 497, 492]}
        assert math.isclose(resilience_calculator.system_demand['Nurse'][3], 76.5)
        assert resilience_calculator.system_demand['Oxygen'] == [0, 720, 1440, 1440]
        assert resilience_calculator.system_demand['EmergencyDepartment_Bed'] == [0, 1, 1, 1]
        assert resilience_calculator.system_demand['Blood'] == [0, 3, 5, 5]   
        assert math.isclose(resilience_calculator.system_consumption['Nurse'][3], 76.5)
        assert resilience_calculator.system_consumption['Oxygen'] == [0, 720, 1000, 1000]
        assert resilience_calculator.system_consumption['EmergencyDepartment_Bed'] == [0, 1, 1, 1]
        assert resilience_calculator.system_consumption['Blood'] == [0, 3, 5, 5]

        system = initiate_system(EXCEL_INPUT_2, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage()
        system = run_system_time_step(system, 0)
        resilience_calculator = ResilienceCalculator.ReCoDeSResilienceCalculator(self.PARAMETERS)
        resilience_calculator.update(system.resources)
        assert resilience_calculator.system_supply == {'Nurse': [50], 'Oxygen': [0], 'EmergencyDepartment_Bed': [0], 'Blood': [0]}     
        assert resilience_calculator.system_demand == {'Nurse': [39], 'Oxygen': [0], 'EmergencyDepartment_Bed': [0], 'Blood': [0]}
        assert resilience_calculator.system_consumption == {'Nurse': [39], 'Oxygen': [0], 'EmergencyDepartment_Bed': [0], 'Blood': [0]}

        system = run_system_time_step(system, 1)
        resilience_calculator.update(system.resources)
        assert resilience_calculator.system_supply == {'Nurse': [50, 50], 'Oxygen': [0, 0], 'EmergencyDepartment_Bed': [0, 0], 'Blood': [0, 0]}     
        assert math.isclose(resilience_calculator.system_demand['Nurse'][1], 3 + 2*3 + 22*0.05 + 6 + 10 + 10 + 10)        
        assert resilience_calculator.system_demand['Oxygen'] == [0, 3360]
        assert resilience_calculator.system_demand['EmergencyDepartment_Bed'] == [0, 3]
        assert resilience_calculator.system_demand['Blood'] == [0, 9]
        assert math.isclose(resilience_calculator.system_consumption['Nurse'][1],  3 + 2*3 + 22*0.05 + 6 + 10 + 10 + 10)
        assert resilience_calculator.system_consumption['Oxygen'] == [0, 0]
        assert resilience_calculator.system_consumption['EmergencyDepartment_Bed'] == [0, 0]
        assert resilience_calculator.system_consumption['Blood'] == [0, 0]

        system = run_system_time_step(system, 2)
        resilience_calculator.update(system.resources)
        assert resilience_calculator.system_supply == {'Nurse': [50, 50, 50], 'Oxygen': [0, 0, 0], 'EmergencyDepartment_Bed': [0, 0, 0], 'Blood': [0, 0, 0]}
        assert math.isclose(resilience_calculator.system_demand['Nurse'][2], 2*3+3+3+6*0.05 + 6 + 10 + 10 + 10)
        assert resilience_calculator.system_demand['Oxygen'] == [0, 3360, 5*240 + 720+2*720+720]
        assert resilience_calculator.system_demand['EmergencyDepartment_Bed'] == [0, 3, 4]
        assert resilience_calculator.system_demand['Blood'] == [0, 9, 3+3+2*3]
        assert math.isclose(resilience_calculator.system_consumption['Nurse'][2], 2*3+3+3+6*0.05 + 6 + 10 + 10 + 10)
        assert resilience_calculator.system_consumption['Oxygen'] == [0, 0, 0]
        assert resilience_calculator.system_consumption['EmergencyDepartment_Bed'] == [0, 0, 0]
        assert resilience_calculator.system_consumption['Blood'] == [0, 0, 0]

        system = run_system_time_step(system, 3)
        resilience_calculator.update(system.resources)
        assert resilience_calculator.system_supply == {'Nurse': [50, 50, 50, 50], 'Oxygen': [0, 0, 0, 0], 'EmergencyDepartment_Bed': [0, 0, 0, 0], 'Blood': [0, 0, 0, 0]}
        assert math.isclose(resilience_calculator.system_demand['Nurse'][3], 6*0.05+3+3+3 + 6 + 10 + 10 + 10)
        assert resilience_calculator.system_demand['Oxygen'] == [0, 3360,  5*240 + 720+2*720+720, 720+720+5*240+720]
        assert resilience_calculator.system_demand['EmergencyDepartment_Bed'] == [0, 3, 4, 3]
        assert resilience_calculator.system_demand['Blood'] == [0, 9, 3+3+2*3, 3+3+3]   
        assert math.isclose(resilience_calculator.system_consumption['Nurse'][3], 6*0.05+3+3+3 + 6 + 10 + 10 + 10)
        assert resilience_calculator.system_consumption['Oxygen'] == [0, 0, 0, 0]
        assert resilience_calculator.system_consumption['EmergencyDepartment_Bed'] == [0, 0, 0, 0]
        assert resilience_calculator.system_consumption['Blood'] == [0, 0, 0, 0]
    
class TestPatientFlowCalculator:

    PARAMETERS_1 = {
                "Scope": ["All"],
                "Resources": [
                    "Red",
                    "Green"
                ]
            }
    
    PARAMETERS_2 = {
                "Scope": "EmergencyDepartment",
                "Resources": [
                    "Patient 1"                    
                ]
            }

    def test_update_scope_all(self):
        system = initiate_system(EXCEL_INPUT_2, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage()     
        resilience_calculator = ResilienceCalculator.PatientFlowCalculator(self.PARAMETERS_1)

        system = run_system_time_step(system, 0)
        resilience_calculator.update(system.components)
        assert resilience_calculator.system_supply == {'Red': [0], 'Green': [0]}
        assert resilience_calculator.system_demand == {'Red': [0], 'Green': [0]}
        assert resilience_calculator.system_consumption == {'Red': [0], 'Green': [0]}

        system = run_system_time_step(system, 1)
        resilience_calculator.update(system.components)
        assert resilience_calculator.system_supply == {'Red': [0, 0], 'Green': [0, 22]}
        assert resilience_calculator.system_demand == {'Red': [0, 1], 'Green': [0, 22]}
        assert resilience_calculator.system_consumption == {'Red': [0, 0], 'Green': [0, 22]}

        system = run_system_time_step(system, 2)
        resilience_calculator.update(system.components)
        assert resilience_calculator.system_supply == {'Red': [0, 0, 0], 'Green': [0, 22, 6]}
        assert resilience_calculator.system_demand == {'Red': [0, 1, 1], 'Green': [0, 22, 6]}
        assert resilience_calculator.system_consumption == {'Red': [0, 0, 0], 'Green': [0, 22, 6]}
    
    def test_update_scope_OT(self):
        system = initiate_system(EXCEL_INPUT_1, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage()     
        resilience_calculator = ResilienceCalculator.PatientFlowCalculator(self.PARAMETERS_2)

        system = run_system_time_step(system, 0)
        resilience_calculator.update(system.components)
        system = run_system_time_step(system, 1)
        resilience_calculator.update(system.components)
        system = run_system_time_step(system, 2)
        resilience_calculator.update(system.components)
        system = run_system_time_step(system, 3)
        resilience_calculator.update(system.components)
        system = run_system_time_step(system, 4)
        resilience_calculator.update(system.components)
        assert resilience_calculator.system_supply == {'Patient 1': [0, 1, 1, 1, 1]}
        assert resilience_calculator.system_demand == {'Patient 1': [0, 1, 1, 1, 1]}
        assert resilience_calculator.system_consumption == {'Patient 1': [0, 1, 1, 1, 1]}
    

class TestDeadPatientsCalculator:

    PARAMETERS = {
                "Scope": ["All"],
                "Resources": [
                    "Red",
                    "Yellow",
                    "Blue",
                    "Green"
                ]
            }
    
    def test_update_scope_all(self):
        system = initiate_system(EXCEL_INPUT_2, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage()     
        resilience_calculator = ResilienceCalculator.DeadPatientsCalculator(self.PARAMETERS)

        for time_step in range(0, 5):
            system = run_system_time_step(system, time_step)
            resilience_calculator.update(system.components)

        assert resilience_calculator.dead_patients['Green'] == [0, 0, 0, 0, 0]
        assert resilience_calculator.dead_patients['Red'] == [0, 1, 2, 3, 4]

class TestHospitalMeasuresOfServiceCalculator:

    PARAMETERS = {
                "Scope": ["All"],
                "Resources": [
                    "Red",
                    "Green"
                ]
            }
    
    PARAMETERS_PATIENT_1 = {
                "Scope": ["All"],
                "Resources": [
                    "Patient 1"
                ]
            }
    
    PARAMETERS_ALL_PATIENTS = {
                "Scope": ["All"],
                "Resources": [
                    "Red",
                    "Green",
                    "Yellow",
                    "Blue"
                ]
            }
    
    PARAMETERS_ED = {
                "Scope": ["EmergencyDepartment"],
                "Resources": [
                    "Red",
                    "Green",
                    "Yellow",
                    "Blue"
                ]
            }
    
    PARAMETERS_OT = {
                "Scope": ["OperatingTheater"],
                "Resources": [
                    "Red",
                    "Green",
                    "Yellow",
                    "Blue"
                ]
            }
    
    PARAMETERS_OT_YELLOW = {
                "Scope": ["OperatingTheater"],
                "Resources": [
                    "Yellow"
                ]
            }

    PARAMETERS_RED = {
                "Scope": ["All"],
                "Resources": [
                    "Red"
                ]
            }
    
    PARAMETERS_GREEN = {
                "Scope": ["All"],
                "Resources": [
                    "Green"
                ]
            }
    
    def test_init(self):
        resilience_calculator = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS)
        assert resilience_calculator.measures_of_service == {}
        assert resilience_calculator.scope == ["All"]
        assert resilience_calculator.resources == ["Red", "Green"]
    
    def test_calculate_length_of_stay(self):
        system = initiate_system(EXCEL_INPUT_4, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage()     
        resilience_calculator = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS)
        for time_step in range(0, 10):
            system = run_system_time_step(system, time_step)
        assert resilience_calculator.calculate_length_of_stay(system.components[1].patients[0]) == 1
        assert resilience_calculator.calculate_length_of_stay(system.components[1].patients[-1]) == 1
        assert resilience_calculator.calculate_length_of_stay(system.components[2].patients[0]) == 3
        assert resilience_calculator.calculate_length_of_stay(system.components[3].patients[0]) == 9

    def test_collect_all_patients(self):
        random.seed(0)
        system = initiate_system(EXCEL_INPUT_4, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage()  
        resilience_calculator = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_ALL_PATIENTS)
        resilience_calculator_RED = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_RED)
        resilience_calculator_ED = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_ED)
        resilience_calculator_OT_Yellow = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_OT_YELLOW)
        system = run_system_time_step(system, 0)
        assert len(resilience_calculator.collect_all_patients(system.components)) == 0
        assert len(resilience_calculator_RED.collect_all_patients(system.components)) == 0
        assert len(resilience_calculator_ED.collect_all_patients(system.components)) == 0
        assert len(resilience_calculator_OT_Yellow.collect_all_patients(system.components)) == 0
        system = run_system_time_step(system, 1)
        assert len(resilience_calculator.collect_all_patients(system.components)) == 30
        assert len(resilience_calculator_RED.collect_all_patients(system.components)) == 1
        assert len(resilience_calculator_ED.collect_all_patients(system.components)) == 25
        assert len(resilience_calculator_OT_Yellow.collect_all_patients(system.components)) == 0
        system = run_system_time_step(system, 2)
        assert len(resilience_calculator.collect_all_patients(system.components)) == 38
        assert len(resilience_calculator_RED.collect_all_patients(system.components)) == 2
        assert len(resilience_calculator_ED.collect_all_patients(system.components)) == 33
        assert len(resilience_calculator_OT_Yellow.collect_all_patients(system.components)) == 2
        system = run_system_time_step(system, 3)
        assert len(resilience_calculator.collect_all_patients(system.components)) == 46
        assert len(resilience_calculator_RED.collect_all_patients(system.components)) == 3
        assert len(resilience_calculator_ED.collect_all_patients(system.components)) == 41
        assert len(resilience_calculator_OT_Yellow.collect_all_patients(system.components)) == 3
        assert len(resilience_calculator.collect_all_patients(system.components, time_interval=[0, 2])) == 36
        assert len(resilience_calculator_RED.collect_all_patients(system.components, time_interval=[0, 2])) == 1
        assert len(resilience_calculator_ED.collect_all_patients(system.components, time_interval=[0, 2])) == 36
        system = run_system_time_step(system, 4)
        assert len(resilience_calculator.collect_all_patients(system.components)) == 54
        assert len(resilience_calculator_RED.collect_all_patients(system.components)) == 4
        assert len(resilience_calculator_OT_Yellow.collect_all_patients(system.components)) == 4
        assert len(resilience_calculator.collect_all_patients(system.components, time_interval=[0, 2])) == 42
        assert len(resilience_calculator_RED.collect_all_patients(system.components, time_interval=[0, 2])) == 1 
        assert len(resilience_calculator_OT_Yellow.collect_all_patients(system.components, time_interval=[0, 2])) == 0
        assert len(resilience_calculator_OT_Yellow.collect_all_patients(system.components, time_interval=[0, 5])) == 4
    
    def test_collect_all_patients_ED(self):
        system = initiate_system(EXCEL_INPUT_4, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage() 
        resilience_calculator = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_ED)
        system = run_system_time_step(system, 0)
        assert len(resilience_calculator.collect_all_patients(system.components)) == 0
        system = run_system_time_step(system, 1)
        assert len(resilience_calculator.collect_all_patients(system.components)) == 25
        system = run_system_time_step(system, 2)
        assert len(resilience_calculator.collect_all_patients(system.components, time_interval=[2, 3])) == 3
        assert len(resilience_calculator.collect_all_patients(system.components, time_interval=[0, 3])) == 33
        system = run_system_time_step(system, 3)
        assert len(resilience_calculator.collect_all_patients(system.components)) == 41
        system = run_system_time_step(system, 4)
        assert len(resilience_calculator.collect_all_patients(system.components, time_interval=[0, 1])) == 0
    
    def test_calculate_surgical_volume(self):
        random.seed(0)
        system = initiate_system(EXCEL_INPUT_4, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage() 
        resilience_calculator = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_ALL_PATIENTS)
        system = run_system_time_step(system, 0)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (0, 0)
        system = run_system_time_step(system, 1)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (0, 0)
        system = run_system_time_step(system, 2)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (0, 0)
        system = run_system_time_step(system, 3)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (3, 0)
        system = run_system_time_step(system, 4)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (5, 0)

        system = initiate_system(EXCEL_INPUT_4, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage() 
        system.components[12].supply['Supply']['Oxygen'].current_amount = 3120
        system.components[12].supply['Supply']['Oxygen'].initial_amount = 3120
        resilience_calculator = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_ALL_PATIENTS)
        system = run_system_time_step(system, 0)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (0, 0)
        system = run_system_time_step(system, 1)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (0, 0)
        system = run_system_time_step(system, 2)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (0, 0)
        system = run_system_time_step(system, 3)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (1, 1)
        system = run_system_time_step(system, 4)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (2, 3)
        system = run_system_time_step(system, 5)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (3, 4)
        system = run_system_time_step(system, 6)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (4, 5)

        system = initiate_system(EXCEL_INPUT_4, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage() 
        system.components[2].supply['Supply']['OperatingTheater_Bed'].current_amount = 1
        system.components[2].supply['Supply']['OperatingTheater_Bed'].initial_amount = 1
        resilience_calculator = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_ALL_PATIENTS)
        system = run_system_time_step(system, 0)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (0, 0)
        system = run_system_time_step(system, 1)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (0, 0)
        system = run_system_time_step(system, 2)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (0, 0)
        system = run_system_time_step(system, 3)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (1, 2)
        system = run_system_time_step(system, 4)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (1, 4)
        system = run_system_time_step(system, 5)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (2, 5)
        system = run_system_time_step(system, 6)
        assert resilience_calculator.calculate_surgical_volume(system.components) == (2, 7)

    def test_calculate_average_length_of_stay(self):
        random.seed(0)
        system = initiate_system(EXCEL_INPUT_4, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage() 
        resilience_calculator = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_ALL_PATIENTS)
        resilience_calculator_RED = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_RED)
        system = run_system_time_step(system, 0)
        system = run_system_time_step(system, 1)
        assert resilience_calculator.calculate_average_length_of_stay(system.components) == 1
        assert resilience_calculator_RED.calculate_average_length_of_stay(system.components) == 1        
        system = run_system_time_step(system, 2)
        assert math.isclose(resilience_calculator.calculate_average_length_of_stay(system.components), (3+5+28+10)/38)
        assert math.isclose(resilience_calculator_RED.calculate_average_length_of_stay(system.components), (1+2)/2)
        system = run_system_time_step(system, 3)
        assert math.isclose(resilience_calculator.calculate_average_length_of_stay(system.components), (3+2+1+3+3+2+1+22+6+6+5*3)/46)
        assert math.isclose(resilience_calculator_RED.calculate_average_length_of_stay(system.components), (1+2+3)/3)      
    
    def test_calculate_mortality_rate_based_on_dead_patients(self):
        random.seed(0)
        system = initiate_system(EXCEL_INPUT_4, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage()
        resilience_calculator = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_ALL_PATIENTS)
        resilience_calculator_RED = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_RED)
        resilience_calculator_ED = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_ED)
        resilience_calculator_OT = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_OT)
        resilience_calculator_OT_YELLOW = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_OT_YELLOW)
        
        system = run_system_time_step(system, 0)
        assert resilience_calculator.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 1]) == 0
        assert resilience_calculator_RED.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 1]) == 0
        assert resilience_calculator_ED.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 1]) == 0
        assert resilience_calculator_OT.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 1]) == 0
        system = run_system_time_step(system, 1)
        assert resilience_calculator.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 2]) == 0
        assert resilience_calculator_RED.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 2]) == 0
        assert resilience_calculator.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 3]) == 0
        assert resilience_calculator_RED.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 3]) == 0

        system = initiate_system(EXCEL_INPUT_4, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage() 
        system.components[12].supply['Supply']['Oxygen'].current_amount = 3120
        system.components[12].supply['Supply']['Oxygen'].initial_amount = 3120        
        for time_step in range(10):
            system = run_system_time_step(system, time_step)
        assert math.isclose(resilience_calculator.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 4]), 9/99)
        assert math.isclose(resilience_calculator_RED.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 4]), 0)
        assert math.isclose(resilience_calculator_ED.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 4]), 0)
        assert math.isclose(resilience_calculator_OT.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 4]), 9/17)
        assert math.isclose(resilience_calculator_OT_YELLOW.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 4]), 9/9)

        assert math.isclose(resilience_calculator.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 5]), 9/99)
        assert math.isclose(resilience_calculator_RED.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 5]), 0)
        assert math.isclose(resilience_calculator_ED.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 5]), 0)
        assert math.isclose(resilience_calculator_OT.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 5]), 9/17)
        assert math.isclose(resilience_calculator_OT_YELLOW.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[0, 5]), 9/9)

        assert math.isclose(resilience_calculator.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[1, 5]), 9/99)
        assert math.isclose(resilience_calculator_RED.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[1, 5]), 0)  
        assert math.isclose(resilience_calculator_ED.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[1, 5]), 0)
        assert math.isclose(resilience_calculator_OT.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[1, 5]), 9/17) 
        assert math.isclose(resilience_calculator_OT_YELLOW.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[1, 5]), 9/9) 

        assert math.isclose(resilience_calculator.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[4, 10]), 0)
        assert math.isclose(resilience_calculator_RED.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[4, 10]), 0)
        assert math.isclose(resilience_calculator_ED.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[4, 10]), 0)
        assert math.isclose(resilience_calculator_OT.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[4, 10]), 0)
        assert math.isclose(resilience_calculator_OT_YELLOW.calculate_mortality_rate_based_on_dead_patients(system.components, time_interval=[4, 10]), 0)

    def test_calculate_baseline_mortality_rate(self):
        system = initiate_system(EXCEL_INPUT_4, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage()
        resilience_calculator = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_ALL_PATIENTS)
        resilience_calculator_RED = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_RED)
        resilience_calculator_ED = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_ED)
        resilience_calculator_OT = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_OT)
        resilience_calculator_OT_YELLOW = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_OT_YELLOW)
        resilience_calculator.update(system.components)
        for time_step in range(0, 2):
            system = run_system_time_step(system, time_step)
        assert math.isclose(resilience_calculator.calculate_baseline_mortality_rate(system.components), 0.00566, rel_tol=0.05)
        assert math.isclose(resilience_calculator_RED.calculate_baseline_mortality_rate(system.components), 0.05)
        assert math.isclose(resilience_calculator_ED.calculate_baseline_mortality_rate(system.components), 0.006)
        assert math.isclose(resilience_calculator_OT.calculate_baseline_mortality_rate(system.components), 0)
        assert math.isclose(resilience_calculator_OT_YELLOW.calculate_baseline_mortality_rate(system.components), 0)

        for time_step in range(2, 5):
            system = run_system_time_step(system, time_step)
        assert math.isclose(resilience_calculator.calculate_baseline_mortality_rate(system.components), (4*0.05+0.0566*5)/54, rel_tol=0.05)
        assert math.isclose(resilience_calculator_RED.calculate_baseline_mortality_rate(system.components), 0.05)
        assert math.isclose(resilience_calculator_ED.calculate_baseline_mortality_rate(system.components), (4*0.05+5*0.05)/49)
        assert math.isclose(resilience_calculator_OT.calculate_baseline_mortality_rate(system.components), 0)
        assert math.isclose(resilience_calculator_OT_YELLOW.calculate_baseline_mortality_rate(system.components), 0)

    def test_calculate_resilience(self):
        random.seed(0)
        system = initiate_system(EXCEL_INPUT_1, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage()
        system.components[12].supply['Supply']['Oxygen'].current_amount = 10e6
        system.components[12].supply['Supply']['Oxygen'].initial_amount = 10e6
        resilience_calculator = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_PATIENT_1)
        resilience_calculator.update(system.components)
        for time_step in range(0, 20):
            system = run_system_time_step(system, time_step)
        assert resilience_calculator.calculate_resilience() == {'MortalityRateBefore24H': 0.05, 'MortalityRateAfter24H': 0.05, 'AverageLengthOfStay': 145/10, 'SurgeriesPerformed': 10, 'SurgeriesCancelled': 0}

        system = initiate_system(EXCEL_INPUT_4, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage()
        system.components[12].supply['Supply']['Oxygen'].current_amount = 3120
        system.components[12].supply['Supply']['Oxygen'].initial_amount = 3120
        resilience_calculator = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_ALL_PATIENTS)
        resilience_calculator.update(system.components)
        resilience_calculator_RED = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_RED)
        resilience_calculator_RED.update(system.components)
        resilience_calculator_GREEN = ResilienceCalculator.HospitalMeasureOfServiceCalculator(self.PARAMETERS_GREEN)
        resilience_calculator_GREEN.update(system.components)
        for time_step in range(4):
            system = run_system_time_step(system, time_step)
        measures_of_service = resilience_calculator.calculate_resilience()
        assert math.isclose(measures_of_service['MortalityRateBefore24H'], 3/46)
        assert math.isclose(measures_of_service['MortalityRateAfter24H'], 0.0083911, rel_tol=0.05)
        assert math.isclose(measures_of_service['SurgeriesPerformed'], 1)
        assert math.isclose(measures_of_service['SurgeriesCancelled'], 1)
        assert math.isclose(measures_of_service['AverageLengthOfStay'], (3+2+1+3+2+2+1+22+6+6+5*3)/46)
    
        measures_of_service = resilience_calculator_RED.calculate_resilience()
        assert math.isclose(measures_of_service['MortalityRateBefore24H'], 0.05)
        assert math.isclose(measures_of_service['MortalityRateAfter24H'], 0.05)
        assert math.isclose(measures_of_service['SurgeriesPerformed'], 1)
        assert math.isclose(measures_of_service['SurgeriesCancelled'], 0)
        assert math.isclose(measures_of_service['AverageLengthOfStay'], 6/3)

        assert resilience_calculator_GREEN.calculate_resilience() == {'MortalityRateBefore24H': 0, 'MortalityRateAfter24H': 0, 'AverageLengthOfStay': 1, 'SurgeriesPerformed': 0, 'SurgeriesCancelled': 0}
        
        resilience_calculator.ONE_DAY = 4
        resilience_calculator_RED.ONE_DAY = 4
        for time_step in range(4, 6):
            system = run_system_time_step(system, time_step)
        
        measures_of_service = resilience_calculator.calculate_resilience()
        assert math.isclose(measures_of_service['MortalityRateBefore24H'], 5/62)
        assert math.isclose(measures_of_service['MortalityRateAfter24H'], 0.00974, rel_tol=0.05)
        assert math.isclose(measures_of_service['SurgeriesPerformed'], 3)
        assert math.isclose(measures_of_service['SurgeriesCancelled'], 4)
        assert math.isclose(measures_of_service['AverageLengthOfStay'], 1.58064516)

        measures_of_service = resilience_calculator_RED.calculate_resilience()
        assert math.isclose(measures_of_service['MortalityRateBefore24H'], 0.05)
        assert math.isclose(measures_of_service['MortalityRateAfter24H'], 0.05)
        assert math.isclose(measures_of_service['SurgeriesPerformed'], 3)
        assert math.isclose(measures_of_service['SurgeriesCancelled'], 0)
        assert math.isclose(measures_of_service['AverageLengthOfStay'], 3.0)

class TestCauseOfDeathCalculator():

    PARAMETERS = {
                "Resources": [
                    "All"
                ],
                "Scope": [
                    "All"
                ]
            }

    def test_calculate_resilience(self):  
        random.seed(0)
        resilience_calculator = ResilienceCalculator.CauseOfDeathCalculator(self.PARAMETERS)
        system = initiate_system(EXCEL_INPUT_4, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage()
        resilience_calculator.update(system.components)
        for time_step in range(0, 10):
            system = run_system_time_step(system, time_step)
        assert resilience_calculator.calculate_resilience() == {'Red': {}, 'Yellow': {}, 'Green': {}, 'Blue': {}}

        system = initiate_system(EXCEL_INPUT_4, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage()
        system.components[12].supply['Supply']['Oxygen'].current_amount = 3120
        system.components[12].supply['Supply']['Oxygen'].initial_amount = 3120
        resilience_calculator.update(system.components)
        for time_step in range(0, 10):
            system = run_system_time_step(system, time_step)
        assert resilience_calculator.calculate_resilience() == {'Red': {}, 'Yellow': {'Oxygen': 9}, 'Green': {}, 'Blue': {}}

        system = initiate_system(EXCEL_INPUT_4, ADDITIONAL_DATA_LOCATION)
        system.set_initial_damage()
        system.components[12].supply['Supply']['Oxygen'].current_amount = 3120
        system.components[12].supply['Supply']['Oxygen'].initial_amount = 3120
        system.components[2].supply['Supply']['OperatingTheater_Bed'].current_amount = 1
        system.components[2].supply['Supply']['OperatingTheater_Bed'].initial_amount = 1
        resilience_calculator.update(system.components)
        for time_step in range(0, 10):
            system = run_system_time_step(system, time_step)
        assert resilience_calculator.calculate_resilience() == {'Red': {'OperatingTheater_Bed': 4}, 'Yellow': {'Oxygen': 5, 'OperatingTheater_Bed': 9}, 'Green': {}, 'Blue': {}}

        
        