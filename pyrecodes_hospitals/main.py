from pyrecodes_hospitals import ComponentLibraryCreator
from pyrecodes_hospitals import SystemCreator
from pyrecodes_hospitals import System
import json
import pandas as pd
import numpy as np
import scipy
import math

BIG_NUMBER = 1000000
DEPARTMENTS = ['All', 'EmergencyDepartment', 'OperatingTheater', 'Medical/SurgicalDepartment', 'HighDependencyUnit', 'RestOfHospital']
RESOURCES_TO_PLOT = ['Nurse', 'Fuel', 'Water', 'Oxygen', 'MedicalDrugs', 'EmergencyDepartment_Bed', 'OperatingTheater_Bed', 'Medical/SurgicalDepartment_Bed', 'HighDependencyUnit_Bed', 'RestOfHospital_Bed', 'Stretcher', 'Blood', 'MCI_Kit_NonWalking_EmergencyDepartment', 'MCI_Kit_NonWalking_OperatingTheater', 'MCI_Kit_NonWalking_HighDependencyUnit', 'MCI_Kit_NonWalking_Medical/SurgicalDepartment', 'MCI_Kit_Walking_EmergencyDepartment']
ALL_RESOURCES = ['Nurse', 'ElectricPower', 'MCI_Kit_NonWalking_EmergencyDepartment', 'MCI_Kit_NonWalking_OperatingTheater', 'MCI_Kit_NonWalking_HighDependencyUnit', 'MCI_Kit_Walking_EmergencyDepartment', 'MCI_Kit_NonWalking_Medical/SurgicalDepartment', 'Fuel', 'Water', 'Oxygen', 'MedicalDrugs', 'EmergencyDepartment_Bed', 'OperatingTheater_Bed', 'Medical/SurgicalDepartment_Bed', 'HighDependencyUnit_Bed', 'RestOfHospital_Bed', 'Stretcher', 'Blood']
RESOURCE_TO_COMPONENT_MAP = {"Water": "WaterSupplySystem", 
                             "Fuel": "FuelReservoir",
                             "Oxygen": "OxygenReservoir",
                             "Blood": "BloodBank",
                             "MedicalDrugs": "Pharmacy",
                             "MCI_Kit_NonWalking_EmergencyDepartment": "Pharmacy",
                             "MCI_Kit_NonWalking_OperatingTheater": "Pharmacy",
                             "MCI_Kit_NonWalking_HighDependencyUnit": "Pharmacy",
                             "MCI_Kit_NonWalking_Medical/SurgicalDepartment": "Pharmacy",
                             "MCI_Kit_Walking_EmergencyDepartment": "Pharmacy",
                             "OperatingTheater_Bed": "OperatingTheater",
                             "EmergencyDepartment_Bed": "EmergencyDepartment",
                             "HighDependencyUnit_Bed": "HighDependencyUnit",
                             "Medical/SurgicalDepartment_Bed": "Medical/SurgicalDepartment",
                             "RestOfHospital_Bed": "RestOfHospital",
                             "Stretchers": "StretcherStock"}

def read_file(file_name: str) -> dict:
    with open(file_name, 'r') as file:
        file = json.load(file)
    return file

def form_component_library(input_dict: dict) -> dict:
    component_library_target_object = getattr(ComponentLibraryCreator, input_dict['ComponentLibrary']['ComponentLibraryCreatorClass'])  
    component_library_object = component_library_target_object(input_dict['ComponentLibrary']['ComponentLibraryFile'])
    return component_library_object.form_library()

def create_system(input_dict: dict) -> None:
    component_library = form_component_library(input_dict)
    system_creator_target_object = getattr(SystemCreator, input_dict['System']['SystemCreatorClass'])  
    system_creator = system_creator_target_object()
    system_target_object = getattr(System, input_dict['System']['SystemClass'])  
    return system_target_object(input_dict['System']['SystemConfigurationFile'], 
                                    component_library, 
                                    system_creator)

def format_input_from_excel(excel_input_data: dict, MCI_scenario_parameters: dict, input_dict: dict, additional_data_location: str, 
                            default_patient_library_file='Hospital_PatientTypeLibrary.json',
                            default_stress_scenario_file='Hospital_StressScenario.json') -> dict:
    format_component_library_file(excel_input_data, input_dict, additional_data_location, default_patient_library_file)
    format_system_configuration_file(excel_input_data, input_dict, additional_data_location, default_stress_scenario_file)
    format_stress_scenario_file(excel_input_data, MCI_scenario_parameters, input_dict, additional_data_location)
    format_patient_library_file(excel_input_data, input_dict, additional_data_location)

def get_patient_types(excel_input_data: dict) -> list:
    patient_types = excel_input_data['PatientProfiles'].iloc[1:, 0].dropna().values.tolist()
    if np.nan in patient_types:
        patient_types.remove(np.nan)
    return patient_types

def format_component_library_file(excel_input_data: dict, input_dict: dict, additional_data_location: str, default_patient_library_file='Hospital_PatientTypeLibrary.json') -> None:
    component_library_dict = read_file(input_dict['ComponentLibrary']['ComponentLibraryFile'])
    format_patient_library_file_location(component_library_dict, additional_data_location, default_patient_library_file)
    excel_to_dict_map = read_file(additional_data_location + 'ExcelToDictMap_ComponentLibrary.json')
    updated_dict = update_default_dict(excel_input_data['ResourceSupply'], component_library_dict, excel_to_dict_map, excel_key_type='row_row')
    patient_types = get_patient_types(excel_input_data)
    updated_dict['PatientSource']['OperationDemand'] = {}
    for patient_type in patient_types:
        updated_dict['PatientSource']['OperationDemand'][patient_type] = {
                "Amount": 0,
                "ResourceClassName": "ConcreteResource",
                "FunctionalityToAmountRelation": "Constant"
            }

    with open(input_dict['ComponentLibrary']['ComponentLibraryFile'], 'w') as file:
        json.dump(updated_dict, file)

def format_patient_library_file_location(component_library_dict: dict, additional_data_location: str, default_patient_library_file) -> None:
    component_library_dict['PatientSource']['PatientLibrary'] = additional_data_location + default_patient_library_file

def format_stress_scenario_patients(excel_input_data: dict, stress_scenario_dict: dict, additional_data_location: str, standard_mapping=2) -> None:    
    excel_to_dict_map = read_file(additional_data_location + 'ExcelToDictMap_StressScenario.json')['StressScenarioInfo']
    stress_scenario_dict = update_default_dict(excel_input_data['StressScenario'], stress_scenario_dict, excel_to_dict_map[:standard_mapping], excel_key_type='row_col')
    time_stepping_indices = np.where(excel_input_data['StressScenario'] == excel_to_dict_map[standard_mapping][0][0])
    time_stepping = excel_input_data['StressScenario'].iloc[time_stepping_indices[0][0]+1:, time_stepping_indices[1][0]].values.tolist()    
    # patient_types_indices = np.where(excel_input_data['StressScenario'] == excel_to_dict_map[standard_mapping+1][0][0])
    # patient_types = excel_input_data['StressScenario'].iloc[patient_types_indices[0][0]+1, patient_types_indices[1][0]:].values.tolist()
    patient_types = get_patient_types(excel_input_data)
    for patient_type in patient_types:
        patient_admission_dict = {'Resource': patient_type,
                                  "SupplyOrDemand": "demand",
                                  "SupplyOrDemandType": "OperationDemand",
                                  "AtTimeStep": time_stepping}
        patient_type_indices = np.where(excel_input_data['StressScenario'] == patient_type)
        patient_type_admissions = excel_input_data['StressScenario'].iloc[patient_type_indices[0][0]+1:, patient_type_indices[1][0]].values.tolist()
        patient_type_admissions = [0 if math.isnan(x) else x for x in patient_type_admissions]
        patient_admission_dict['Amount'] = patient_type_admissions
        stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'].append(patient_admission_dict)       

def format_stress_scenario_supply_increase_due_to_restocking(excel_input_data: dict, stress_scenario_dict: dict, additional_data_location: str, standard_mapping=2) -> None:
    excel_to_dict_map = read_file(additional_data_location + 'ExcelToDictMap_StressScenario.json')
    excel_fields = [[4, 1], [5, 1], [6, 1], [7, 1], [8, 1]]
    for excel_field in excel_fields:
        if excel_input_data['StressScenario'].iloc[excel_field[0], excel_field[1]] == 'Yes':   
            resource_name = excel_input_data['StressScenario'].iloc[excel_field[0], excel_field[1]-1].split(' ')[0]         
            add_supply_increase(excel_input_data, excel_to_dict_map[f'{resource_name}SupplyIncrease'], resource_name, stress_scenario_dict)
    return stress_scenario_dict

def format_stress_scenario_bed_supply_increase(excel_input_data: dict, stress_scenario_dict: dict, additional_data_location: str, standard_mapping=2) -> None:
    excel_to_dict_map = read_file(additional_data_location + 'ExcelToDictMap_StressScenario.json')
    add_bed_supply_increase(excel_input_data, excel_to_dict_map['BedSupplyIncrease'], stress_scenario_dict)
    return stress_scenario_dict

def format_predefined_stress_scenario_patients(MCI_scenario_parameters: dict, stress_scenario_dict: dict) -> None:
    scenario_name = MCI_scenario_parameters['MCI_type']
    stress_scenario_dict['StressScenarioName'] = scenario_name
    total_number_of_patients = MCI_scenario_parameters['number_of_patients']
    patient_types = list(MCI_scenario_parameters['patient_arrival'].keys())
    time_stepping = list(range(0, MCI_scenario_parameters['investigated_period'] * 24, 1))
    for patient_type in patient_types:
        number_of_patients = []
        for time_step in time_stepping:        
            patient_ratio = get_element_from_list_with_default(MCI_scenario_parameters['patient_arrival'][patient_type], time_step, 0)
            number_of_patients.append(int(total_number_of_patients * patient_ratio))
        patient_admission_dict = {'Resource': patient_type,
                                    "SupplyOrDemand": "demand",
                                    "SupplyOrDemandType": "OperationDemand",
                                    "AtTimeStep": time_stepping,
                                    "Amount": number_of_patients}
        stress_scenario_dict['ComponentsToChange'][0]['ResourcesToChange'].append(patient_admission_dict)

def get_element_from_list_with_default(lst, index, default):
    try:
        return lst[index]
    except IndexError:
        return default

def add_supply_increase(excel_input_data: dict, excel_to_dict_map: list, resource_name: str, stress_scenario_dict: dict) -> None:
    time_to_restock = get_value_from_excel_sheet_row_row(excel_input_data['ResourceSupply'], excel_to_dict_map[0][0])
    restocked_amount = get_value_from_excel_sheet_row_row(excel_input_data['ResourceSupply'], excel_to_dict_map[1][0])   
    supply_increase_dict = {"ComponentName": RESOURCE_TO_COMPONENT_MAP[resource_name],
                            "InitialDemand": [],
                            "ResourcesToChange": [
                                {"Resource": resource_name,
                                    "SupplyOrDemand": "supply",
                                    "SupplyOrDemandType": "Supply",
                                    "AtTimeStep": [time_to_restock],
                                    "Amount": [restocked_amount]}
                            ]}
    for component_to_change in stress_scenario_dict['ComponentsToChange']:
        if component_to_change['ComponentName'] == RESOURCE_TO_COMPONENT_MAP[resource_name]:
            component_to_change['ResourcesToChange'] = supply_increase_dict['ResourcesToChange']
            return
    
                            
def add_bed_supply_increase(excel_input_data: dict, excel_to_dict_map: list, stress_scenario_dict: dict) -> None:
    for excel_keys in excel_to_dict_map:
        time_to_restock = get_value_from_excel_sheet_row_row(excel_input_data['ResourceSupply'], [excel_keys[0][0], excel_keys[0][3]])
        MCI_amount = get_value_from_excel_sheet_row_row(excel_input_data['ResourceSupply'], [excel_keys[0][1], excel_keys[0][3]])
        original_amount = get_value_from_excel_sheet_row_row(excel_input_data['ResourceSupply'], [excel_keys[0][2], excel_keys[0][3]])
        added_amount = MCI_amount - original_amount
        supply_increase_dict = {"ComponentName": excel_keys[1][1],
                                "InitialDemand": [],
                                "ResourcesToChange": [
                                    {"Resource": f"{excel_keys[1][1]}_Bed",
                                        "SupplyOrDemand": "supply",
                                        "SupplyOrDemandType": "Supply",
                                        "AtTimeStep": [time_to_restock],
                                        "Amount": [added_amount]}
                                ]}
        for component_to_change in stress_scenario_dict['ComponentsToChange']:
            if component_to_change['ComponentName'] == excel_keys[1][1]:
                component_to_change['ResourcesToChange'].append(supply_increase_dict['ResourcesToChange'][0])

def clean_stress_scenario_dict(stress_scenario_dict: dict) -> None:
    for component_to_change in stress_scenario_dict['ComponentsToChange']:
        component_to_change['ResourcesToChange'] = []
    
def format_stress_scenario_file(excel_input_data: dict, MCI_scenario_parameters: dict, input_dict: dict, additional_data_location: str, standard_mapping=2) -> None:
    stress_scenario_dict = read_file(read_file(input_dict['System']['SystemConfigurationFile'])['DamageInput']['Parameters'])
    clean_stress_scenario_dict(stress_scenario_dict)
    format_stress_scenario_bed_supply_increase(excel_input_data, stress_scenario_dict, additional_data_location, standard_mapping)

    if MCI_scenario_parameters:   
        format_predefined_stress_scenario_patients(MCI_scenario_parameters, stress_scenario_dict)
    else:
        # if MCI scenario parameters are not provided, the user defined scenario is defined already in the excel file
        format_stress_scenario_patients(excel_input_data, stress_scenario_dict, additional_data_location, standard_mapping)
        format_stress_scenario_supply_increase_due_to_restocking(excel_input_data, stress_scenario_dict, additional_data_location, standard_mapping)

    with open(read_file(input_dict['System']['SystemConfigurationFile'])['DamageInput']['Parameters'], 'w') as file:
        json.dump(stress_scenario_dict, file)

def format_patient_library_file(excel_input_data: dict, input_dict: dict, additional_data_location: str, department_column_offset=6, data_source_string='Data source') -> None:
    # patient_library_dict = read_file(read_file(input_dict['ComponentLibrary']['ComponentLibraryFile'])["PatientSource"]["PatientLibrary"])
    patient_library_dict = {}
    EXIT = {"EXIT": {
                "BaselineLengthOfStay": BIG_NUMBER,
                "BaselineMortalityRate": 0,
                "ResourcesRequired": []
        }}
    
    # map Excel Triage categories to labels used for MCI Kit resources. 
    # Not applicable is not relevant, as the amount is 0, but the resource name has to be consistent.
    TRIAGE_CATEGORIES = {'Non-walking': 'NonWalking', 'Walking': 'Walking', 'Not applicable': 'NonWalking'} 

    patient_types = get_patient_types(excel_input_data)
    for patient_type in patient_types:
        patient_type_info = []
        patient_type_indices = np.where(excel_input_data['PatientProfiles'] == patient_type)
        departments = excel_input_data['PatientProfiles'].iloc[patient_type_indices[0][0], patient_type_indices[1][0]+1:].dropna().values.tolist()
        departments = [department for department in departments if department != data_source_string]
        department_column_index = patient_type_indices[1][0]+1
        department_row_index = patient_type_indices[0][0]
        triage_category = TRIAGE_CATEGORIES[excel_input_data['PatientProfiles'].iloc[department_row_index+2, department_column_index+1]]
        for department in departments:
            if excel_input_data['PatientProfiles'].iloc[department_row_index+1, department_column_index+1] == 'Inf':
                excel_input_data['PatientProfiles'].iloc[department_row_index+1, department_column_index+1] = BIG_NUMBER
            baseline_length_of_stay = excel_input_data['PatientProfiles'].iloc[department_row_index+3, department_column_index+1]
            mortality_rate_during_entire_stay = excel_input_data['PatientProfiles'].iloc[department_row_index+4, department_column_index+1]
            baseline_mortality_rate = get_mortality_rate_per_time_step(mortality_rate_during_entire_stay, baseline_length_of_stay)
            department_info = {
                "BaselineLengthOfStay": baseline_length_of_stay,
                "BaselineMortalityRate": baseline_mortality_rate,
                "ResourcesRequired": [
                    {"ResourceName": "Nurse", "ResourceAmount": excel_input_data['PatientProfiles'].iloc[department_row_index+6, department_column_index+1],
                     "ConsequencesOfUnmetDemand": [{excel_input_data['PatientProfiles'].iloc[department_row_index+6, department_column_index+3]: 
                                                    excel_input_data['PatientProfiles'].iloc[department_row_index+6, department_column_index+4]}]},
                    {"ResourceName": "Water", "ResourceAmount": excel_input_data['PatientProfiles'].iloc[department_row_index+7, department_column_index+1],
                     "ConsequencesOfUnmetDemand": [{excel_input_data['PatientProfiles'].iloc[department_row_index+7, department_column_index+3]:
                                                    excel_input_data['PatientProfiles'].iloc[department_row_index+7, department_column_index+4]}]},
                    {"ResourceName": "Oxygen", "ResourceAmount": excel_input_data['PatientProfiles'].iloc[department_row_index+8, department_column_index+1],
                     "ConsequencesOfUnmetDemand": [{excel_input_data['PatientProfiles'].iloc[department_row_index+8, department_column_index+3]:
                                                    excel_input_data['PatientProfiles'].iloc[department_row_index+8, department_column_index+4]}]},
                    {"ResourceName": f"MCI_Kit_{triage_category}_{department}", "ResourceAmount": modify_consumable_resource_demand(baseline_length_of_stay, excel_input_data['PatientProfiles'].iloc[department_row_index+9, department_column_index+1]),
                     "ConsequencesOfUnmetDemand": [{excel_input_data['PatientProfiles'].iloc[department_row_index+9, department_column_index+3]:
                                                    excel_input_data['PatientProfiles'].iloc[department_row_index+9, department_column_index+4]}]},
                    {"ResourceName": f"{department}_Bed", "ResourceAmount": excel_input_data['PatientProfiles'].iloc[department_row_index+10, department_column_index+1],
                     "ConsequencesOfUnmetDemand": [{excel_input_data['PatientProfiles'].iloc[department_row_index+10, department_column_index+3]:
                                                    excel_input_data['PatientProfiles'].iloc[department_row_index+10, department_column_index+4]}]},
                    {"ResourceName": "Blood", "ResourceAmount": modify_consumable_resource_demand(baseline_length_of_stay, excel_input_data['PatientProfiles'].iloc[department_row_index+11, department_column_index+1]),
                     "ConsequencesOfUnmetDemand": [{excel_input_data['PatientProfiles'].iloc[department_row_index+11, department_column_index+3]:
                                                    excel_input_data['PatientProfiles'].iloc[department_row_index+11, department_column_index+4]}]},
                    {"ResourceName": "Stretcher", "ResourceAmount": excel_input_data['PatientProfiles'].iloc[department_row_index+12, department_column_index+1],
                     "ConsequencesOfUnmetDemand": [{excel_input_data['PatientProfiles'].iloc[department_row_index+12, department_column_index+3]:
                                                    excel_input_data['PatientProfiles'].iloc[department_row_index+12, department_column_index+4]}]},
                    {"ResourceName": "MedicalDrugs", "ResourceAmount": excel_input_data['PatientProfiles'].iloc[department_row_index+13, department_column_index+1],
                     "ConsequencesOfUnmetDemand": [{excel_input_data['PatientProfiles'].iloc[department_row_index+13, department_column_index+3]:
                                                    excel_input_data['PatientProfiles'].iloc[department_row_index+13, department_column_index+4]}]},
                ]
            }
            department_column_index += department_column_offset
            patient_type_info.append({department: department_info})
        patient_type_info.append(EXIT)
        patient_library_dict[patient_type] = patient_type_info
            
    with open(read_file(input_dict['ComponentLibrary']['ComponentLibraryFile'])["PatientSource"]["PatientLibrary"], 'w') as file:
        json.dump(patient_library_dict, file)

def modify_consumable_resource_demand(baseline_length_of_stay: int, demand_amount: int) -> int:
    # The demand for some consumable resources is modified based on the length of stay - evenly distributed during the length of stay to prevent overconsumption. 
    # The excel input for these resources is the total demand for the entire length of stay (e.g., MCI kits, blood).
    # (i.e., demanding the amount needed for the entire length of stay at each time step of stay)
    if baseline_length_of_stay > 0:
        return demand_amount/baseline_length_of_stay
    else:
        return 0

def format_system_configuration_file(excel_input_data: dict, input_dict: dict, additional_data_location: str, default_stress_scenario_file='Hospital_StressScenario.json') -> None:
    system_configuration_dict = read_file(input_dict['System']['SystemConfigurationFile'])
    patient_types = get_patient_types(excel_input_data)
    set_max_time_step(system_configuration_dict, excel_input_data, additional_data_location)
    format_resilience_calculators(system_configuration_dict, patient_types)
    format_stress_scenario_file_location(system_configuration_dict, additional_data_location, default_stress_scenario_file)
    
    with open(input_dict['System']['SystemConfigurationFile'], 'w') as file:
        json.dump(system_configuration_dict, file)

def set_max_time_step(system_configuration_dict: dict, excel_input_data: dict, additional_data_location: str, standard_mapping=2):
    excel_to_dict_map = read_file(additional_data_location + 'ExcelToDictMap_StressScenario.json')['StressScenarioInfo']
    time_stepping_indices = np.where(excel_input_data['StressScenario'] == excel_to_dict_map[standard_mapping][0][0])
    time_stepping = excel_input_data['StressScenario'].iloc[time_stepping_indices[0][0]+1:, time_stepping_indices[1][0]].values.tolist()  
    system_configuration_dict['Constants']['MAX_TIME_STEP'] = max(time_stepping)

def format_resilience_calculators(system_configuration_dict: dict, patient_types: list) -> None:
    resilience_calculators = []

    resilience_calculators.append({
            "Type": "ReCoDeSResilienceCalculator",
            "Parameters": {
                "Scope": ['All'],
                "Resources": ALL_RESOURCES
            }
        })
    
    for department in DEPARTMENTS:
        resilience_calculators.append({
            "Type": "ReCoDeSResilienceCalculator",
            "Parameters": {
                "Scope": [department],
                "Resources": RESOURCES_TO_PLOT                
            }
        }) 

    for department in DEPARTMENTS:
        for patient_type in patient_types + ['All']:
            resilience_calculators.append({
                "Type": "HospitalMeasureOfServiceCalculator",
                "Parameters": {
                    "Resources": [patient_type],
                    "Scope": [department]
                }
            })

    # add cause of death resilience calculator
    resilience_calculators.append({
        "Type": "CauseOfDeathCalculator",
        "Parameters": {
            "Resources": ['All'],
            "Scope": ['All']
        }
    })

    system_configuration_dict['ResilienceCalculator'] = resilience_calculators

def format_stress_scenario_file_location(system_configuration_dict: dict, additional_data_location: str, default_stress_scenario_file='Hospital_StressScenario.json') -> None:
    # if additional_data_location not in system_configuration_dict['DamageInput']['Parameters']:
    system_configuration_dict['DamageInput']['Parameters'] = additional_data_location + default_stress_scenario_file

def update_default_dict(excel_sheet: pd.DataFrame, default_dict: dict, excel_to_dict_map: dict, excel_key_type: str) -> None:
    for excel_key, dict_key in excel_to_dict_map:
        if excel_key_type == 'row_col':
            value = get_value_from_excel_sheet_row_col(excel_sheet, excel_key)
        elif excel_key_type == 'row_row':
            value = get_value_from_excel_sheet_row_row(excel_sheet, excel_key)
        current_dict = default_dict
        for key in dict_key[:-1]:
            current_dict = current_dict[key]
        current_dict[dict_key[-1]] = value
    return default_dict

def get_value_from_excel_sheet_row_col(excel_sheet: pd.DataFrame, excel_key: list) -> None:
    # Get the value from the excel sheet if the strings in the excel key describe the row and column of the value 
    row_index = np.where(excel_sheet == excel_key[0])[0][0]
    col_index = np.where(excel_sheet == excel_key[1])[1][0]
    return excel_sheet.iloc[row_index, col_index]

def get_value_from_excel_sheet_row_row(excel_sheet: pd.DataFrame, excel_key: list, row_1_col_index=0, row_2_col_index=1, value_col_index=2) -> None:
    # Get the value from the excel sheet if the strings in the excel key describe the rows to get the value. Column ID is fixed.
    row_index_1 = [np.where(excel_sheet == excel_key[0])[0][i] for i, col_id in enumerate(np.where(excel_sheet == excel_key[0])[1]) if col_id == row_1_col_index]
    row_index_2 = [np.where(excel_sheet == excel_key[1])[0][i] for i, col_id in enumerate(np.where(excel_sheet == excel_key[1])[1]) if col_id == row_2_col_index]
    row_index = list(set(row_index_1) & set(row_index_2))[0]
    return excel_sheet.iloc[row_index, value_col_index]

def get_mortality_rate_per_time_step(mortality_rate_during_entire_stay: float, length_of_stay: int) -> float:
    if length_of_stay == 1:
        return mortality_rate_during_entire_stay
    elif mortality_rate_during_entire_stay == 0:
        return 0
    else:
        # mortality_rate_per_time_step = mortality_rate_during_entire_stay/length_of_stay
        try:
            mortality_rate_per_time_step = scipy.optimize.newton(binomial_dist_equation_to_solve, mortality_rate_during_entire_stay/length_of_stay, args=(mortality_rate_during_entire_stay, length_of_stay), tol=1e-10, maxiter=1000)
        except RuntimeError:
            # For high values of mortality rate, the equation does not converge. In this case, we approximate by using the average mortality rate.
            print('Please double check the values of baseline mortality rates, they seem to be high. The tool could not find the exact solution for the mortality rate per time step. Approximating by using the average mortality rate. This might cause inaccuracies in the mortality rate estimates.')
            mortality_rate_per_time_step = mortality_rate_during_entire_stay/length_of_stay
    return mortality_rate_per_time_step

def binomial_dist_equation_to_solve(mortality_rate_per_time_step: float, mortality_rate_during_entire_stay: float, length_of_stay: int) -> float:
    # prob of the serial system failing at least once during the stay
    # return 1 - (1 - mortality_rate_per_time_step)**(length_of_stay) - mortality_rate_during_entire_stay
    # prob of exactly one link failing - more realistic, patient can die only once
    return length_of_stay * mortality_rate_per_time_step * (1 - mortality_rate_per_time_step)**(length_of_stay-1) - mortality_rate_during_entire_stay

def run(main_file: str) -> System.System:
    input_dict = read_file(main_file)    
    system = create_system(input_dict)
    system.start_resilience_assessment()
    return system

def read_main_file(main_file: str, additional_data_location: str) -> dict:
    input_dict = read_file(main_file)
    input_dict['System']['SystemConfigurationFile'] = additional_data_location + input_dict['System']['SystemConfigurationFile']
    input_dict['ComponentLibrary']['ComponentLibraryFile'] = additional_data_location + input_dict['ComponentLibrary']['ComponentLibraryFile']
    return input_dict

def run_from_excel(excel_input_data: dict, MCI_scenario_parameters: dict, additional_data_location: str, progressBar=None, app=None) -> System.System:
    main_file = additional_data_location + 'Hospital_Main.json'
    input_dict = read_main_file(main_file, additional_data_location)    
    format_input_from_excel(excel_input_data, MCI_scenario_parameters, input_dict, additional_data_location)
    system = create_system(input_dict)
    system.start_resilience_assessment(progressBar=progressBar, app=app)
    return system

def read_excel_input(input_filename: str) -> dict:
    sheet_names = ['ResourceSupply', 'StressScenario', 'PatientProfiles']
    input_data = pd.read_excel(input_filename, sheet_name=sheet_names, header=None, na_filter=False)
    for sheet_name in sheet_names:
        input_data[sheet_name].replace('', np.nan, inplace=True)
    input_data['ResourceSupply'].ffill(inplace=True) # propagate values in merged cells to the end of the cell
    return input_data

def run_from_gui(input_filename: str, MCI_scenario_parameters:dict, additional_data_location: str, progressBar=None, app=None):
    input_data = read_excel_input(input_filename)
    system = run_from_excel(input_data, MCI_scenario_parameters, additional_data_location, progressBar=progressBar, app=app)
    return system