
import pytest
import math
import copy
from pyrecodes_hospitals import SystemCreator
from pyrecodes_hospitals import ComponentLibraryCreator
from pyrecodes_hospitals import Component


class TestThreeLocalitiesJSONSystemCreator():
    component_library_file = "./tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_ComponentLibrary.json"
    system_configuration_file = './tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_SystemConfiguration.json'

    @pytest.fixture()
    def json_system_creator(self) -> SystemCreator.SystemCreator:
        return SystemCreator.JSONSystemCreator()

    @pytest.fixture()
    def component_library(self) -> ComponentLibraryCreator.JSONComponentLibraryCreator:
        return ComponentLibraryCreator.JSONComponentLibraryCreator(self.component_library_file)

    def form_component_library_for_testing(self, json_system_creator: SystemCreator.SystemCreator,
                                           component_library: ComponentLibraryCreator.ComponentLibraryCreator):
        formed_component_library = component_library.form_library()
        json_system_creator.set_component_library(formed_component_library)
        return json_system_creator

    def test_read_file(self, json_system_creator: SystemCreator.SystemCreator):
        json_system_creator.read_file(self.system_configuration_file)
        assert ('Content' in json_system_creator.system_configuration_file, 'DamageInput' in json_system_creator.system_configuration_file,
                'Resources' in json_system_creator.system_configuration_file) == (True, True, True)

    def test_set_component_library(self, json_system_creator: SystemCreator.SystemCreator,
                                   component_library: ComponentLibraryCreator.ComponentLibraryCreator):
        json_system_creator.set_component_library(component_library)
        assert isinstance(json_system_creator.component_library, ComponentLibraryCreator.JSONComponentLibraryCreator)

    def test_get_damage_input_type(self, json_system_creator: SystemCreator.SystemCreator):
        json_system_creator.read_file(self.system_configuration_file)
        assert json_system_creator.get_damage_input_type() == "ListDamageInput"

    def test_get_damage_input_params(self, json_system_creator: SystemCreator.SystemCreator):
        json_system_creator.read_file(self.system_configuration_file)
        assert json_system_creator.get_damage_input_parameters() == [0.0, 0.4, 0.0, 0.0, 0.4, 0.0, 0.0, 0.4, 0.4, 0.0,
                                                                     0.0]

    def test_get_component_object(self, json_system_creator: SystemCreator.SystemCreator,
                                  component_library: ComponentLibraryCreator.ComponentLibraryCreator):
        json_system_creator = self.form_component_library_for_testing(json_system_creator, component_library)
        assert all([isinstance(json_system_creator.get_component_object('ElectricPowerPlant'),
                               Component.StandardiReCoDeSComponent),
                    isinstance(json_system_creator.get_component_object('BuildingStockUnit'),
                               Component.StandardiReCoDeSComponent),
                    isinstance(json_system_creator.get_component_object('BaseTransceiverStation_1'),
                               Component.StandardiReCoDeSComponent),
                    isinstance(json_system_creator.get_component_object('BaseTransceiverStation_2'),
                               Component.StandardiReCoDeSComponent),
                    isinstance(json_system_creator.get_component_object('CoolingWaterFacility'),
                               Component.StandardiReCoDeSComponent),
                    isinstance(json_system_creator.get_component_object('SuperLink'),
                               Component.StandardiReCoDeSComponent)]) == True

    def test_add_components_empty(self, json_system_creator: SystemCreator.SystemCreator,
                                  component_library: ComponentLibraryCreator.ComponentLibraryCreator):
        json_system_creator = self.form_component_library_for_testing(json_system_creator, component_library)
        assert json_system_creator.components == []

    def test_add_components_multiple_components(self, json_system_creator: SystemCreator.SystemCreator,
                                                component_library: ComponentLibraryCreator.ComponentLibraryCreator):
        json_system_creator = self.form_component_library_for_testing(json_system_creator, component_library)
        num_components = 5
        for _ in range(num_components):
            component = json_system_creator.get_component_object('ElectricPowerPlant')
            json_system_creator.add_component(component)
        assert len(json_system_creator.components) == num_components

    def test_format_locality_id(self, json_system_creator: SystemCreator.SystemCreator):
        locality_strings = ['Locality 12', 'Locality 1', 'Locality 312', 'Locality 3124']
        locality_ids = [12, 1, 312, 3124]
        boolean_list = []
        for locality_id, locality_string in zip(locality_ids, locality_strings):
            boolean_list.append(locality_id == json_system_creator.format_locality_id(locality_string))
        assert all(boolean_list) == True

    def construct_create_link_components_test(self, json_system_creator: SystemCreator.SystemCreator,
                                              component_library: ComponentLibraryCreator.ComponentLibraryCreator,
                                              locality_string: str):
        json_system_creator = self.form_component_library_for_testing(json_system_creator, component_library)
        json_system_creator.read_file(self.system_configuration_file)
        json_system_creator.create_components_between_localities(locality=locality_string,
                                                   content=json_system_creator.system_configuration_file['Content'][locality_string][
                                                       'LinkTo'])
        return json_system_creator

    def construct_create_components_in_localities_test(self, json_system_creator: SystemCreator.SystemCreator,
                                                       component_library: ComponentLibraryCreator.ComponentLibraryCreator,
                                                       locality_string: str):
        json_system_creator = self.form_component_library_for_testing(json_system_creator, component_library)
        json_system_creator.read_file(self.system_configuration_file)
        json_system_creator.create_components_in_localities(locality=locality_string, content=
        json_system_creator.system_configuration_file['Content'][locality_string]['ComponentsInLocality'])
        return json_system_creator

    def test_create_link_components_locality_1(self, json_system_creator: SystemCreator.SystemCreator,
                                               component_library: ComponentLibraryCreator.ComponentLibraryCreator):
        locality_string = 'Locality 1'
        json_system_creator = self.construct_create_link_components_test(json_system_creator, component_library,
                                                                         locality_string)
        assert all([len(json_system_creator.components) == 2,
                    isinstance(json_system_creator.components[0], Component.StandardiReCoDeSComponent),
                    isinstance(json_system_creator.components[1], Component.StandardiReCoDeSComponent),
                    json_system_creator.components[0].locality == [1, 2],
                    json_system_creator.components[1].locality == [1, 3]]) == True

    def test_create_link_components_locality_2(self, json_system_creator: SystemCreator.SystemCreator,
                                               component_library: ComponentLibraryCreator.ComponentLibraryCreator):
        locality_string = 'Locality 2'
        json_system_creator = self.construct_create_link_components_test(json_system_creator, component_library,
                                                                         locality_string)
        assert all([len(json_system_creator.components) == 2,
                    isinstance(json_system_creator.components[0], Component.StandardiReCoDeSComponent),
                    isinstance(json_system_creator.components[1], Component.StandardiReCoDeSComponent),
                    json_system_creator.components[0].locality == [2, 1],
                    json_system_creator.components[1].locality == [2, 3]]) == True

    def test_create_link_components_locality_3(self, json_system_creator: SystemCreator.SystemCreator,
                                               component_library: ComponentLibraryCreator.ComponentLibraryCreator):
        locality_string = 'Locality 3'
        json_system_creator = self.construct_create_link_components_test(json_system_creator, component_library,
                                                                         locality_string)
        assert all([len(json_system_creator.components) == 2,
                    isinstance(json_system_creator.components[0], Component.StandardiReCoDeSComponent),
                    isinstance(json_system_creator.components[1], Component.StandardiReCoDeSComponent),
                    json_system_creator.components[0].locality == [3, 1],
                    json_system_creator.components[1].locality == [3, 2]]) == True

    def test_create_components_in_localities_locality_1(self, json_system_creator: SystemCreator.SystemCreator,
                                                        component_library: ComponentLibraryCreator.ComponentLibraryCreator):
        locality_string = 'Locality 1'
        json_system_creator = self.construct_create_components_in_localities_test(json_system_creator,
                                                                                  component_library, locality_string)
        assert all([len(json_system_creator.components) == 2,
                    isinstance(json_system_creator.components[0], Component.StandardiReCoDeSComponent),
                    json_system_creator.components[0].name == 'BaseTransceiverStation_1',
                    json_system_creator.components[0].locality == [1],
                    json_system_creator.components[1].name == 'ElectricPowerPlant',
                    json_system_creator.components[1].locality == [1]
                    ]) == True

    def test_create_components_in_localities_locality_2(self, json_system_creator: SystemCreator.SystemCreator,
                                                        component_library: ComponentLibraryCreator.ComponentLibraryCreator):
        locality_string = 'Locality 2'
        json_system_creator = self.construct_create_components_in_localities_test(json_system_creator,
                                                                                  component_library, locality_string)
        assert all([len(json_system_creator.components) == 1,
                    isinstance(json_system_creator.components[0], Component.StandardiReCoDeSComponent),
                    json_system_creator.components[0].name == 'CoolingWaterFacility',
                    json_system_creator.components[0].locality == [2]
                    ]) == True

    def test_create_components_in_localities_locality_3(self, json_system_creator: SystemCreator.SystemCreator,
                                                        component_library: ComponentLibraryCreator.ComponentLibraryCreator):
        locality_string = 'Locality 3'
        json_system_creator = self.construct_create_components_in_localities_test(json_system_creator,
                                                                                  component_library, locality_string)
        assert all([len(json_system_creator.components) == 2,
                    isinstance(json_system_creator.components[0], Component.StandardiReCoDeSComponent),
                    json_system_creator.components[0].name == 'BuildingStockUnit',
                    json_system_creator.components[0].locality == [3],
                    json_system_creator.components[1].name == 'BaseTransceiverStation_2',
                    json_system_creator.components[1].locality == [3]
                    ]) == True

    def test_create_components_num_components_created(self, json_system_creator: SystemCreator.SystemCreator,
                                                      component_library: ComponentLibraryCreator.ComponentLibraryCreator):
        json_system_creator = self.form_component_library_for_testing(json_system_creator, component_library)
        json_system_creator.read_file(self.system_configuration_file)
        components = json_system_creator.create_components()
        assert all([len(components) == 11]) == True


class TestNorthEast_SF_Housing_SystemCreator:
    component_library_file = "./tests/test_inputs/test_inputs_NorthEast_SF_Housing_ComponentLibrary.json"
    system_configuration_file = './tests/test_inputs/test_inputs_NorthEast_SF_Housing_SystemConfiguration.json'

    @pytest.fixture()
    def r2d_system_creator(self) -> SystemCreator.SystemCreator:
        return SystemCreator.R2DSystemCreator()

    @pytest.fixture()
    def component_library(self) -> ComponentLibraryCreator.JSONComponentLibraryCreator:
        return ComponentLibraryCreator.JSONComponentLibraryCreator(self.component_library_file).form_library()

    def test_setup(self, r2d_system_creator: SystemCreator.SystemCreator, component_library: dict):
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        target_scenario_id = 1
        bool_list = []
        bool_list.append(type(r2d_system_creator.component_library) == dict)
        target_components = ['EmergencyResponseCenter', 'DS0_ResidentialBuilding', 'DS1_ResidentialBuilding',
                             'DS2_ResidentialBuilding', 'DS3_ResidentialBuilding', 'DS4_ResidentialBuilding']
        for target_component in target_components:
            bool_list.append(target_component in r2d_system_creator.component_library)

        bool_list.append(r2d_system_creator.scenario_id == target_scenario_id)
        target_keys_in_configuration_file = ['Content', 'DamageInput', 'Resources', 'ResilienceCalculator']
        for target_key in target_keys_in_configuration_file:
            bool_list.append(target_key in r2d_system_creator.system_configuration_file)

        assert all(bool_list)

    def test_building_area_per_person(self, r2d_system_creator: SystemCreator.SystemCreator, component_library: dict):
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        r2d_system_creator.set_building_area_per_person()
        target_area_per_person = r2d_system_creator.system_configuration_file['Content']['Locality 1']['ComponentsInLocality'][
            'AreaPerPerson']
        assert target_area_per_person == r2d_system_creator.building_area_per_person['Locality 1']

    def test_create_components(self, r2d_system_creator: SystemCreator.SystemCreator, component_library: dict):
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        components = r2d_system_creator.create_components()
        target_num_components = r2d_system_creator.system_configuration_file['Content']['Locality 1']['ComponentsInLocality'][
                                    'MaxNumBuildings'] + 1
        assert len(r2d_system_creator.components) == target_num_components

    def test_create_recovery_resource_suppliers(self, r2d_system_creator: SystemCreator.SystemCreator,
                                                component_library: dict):
        bool_list = []
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        suppliers = r2d_system_creator.create_recovery_resource_suppliers('Locality 1',
                                                                          r2d_system_creator.system_configuration_file['Content'][
                                                                              'Locality 1'])
        bool_list.append(len(suppliers) == 1)
        bool_list.append(suppliers[0].name == 'EmergencyResponseCenter')
        bool_list.append(type(suppliers[0]).__name__ == 'StandardiReCoDeSComponent')
        assert all(bool_list)

    def test_create_residential_building_components(self, r2d_system_creator: SystemCreator.SystemCreator,
                                                    component_library: dict):
        bool_list = []
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        r2d_system_creator.set_building_area_per_person()
        components = r2d_system_creator.create_residential_building_components('Locality 1',
                                                                               r2d_system_creator.file['Content'][
                                                                                   'Locality 1'])
        target_num_components = r2d_system_creator.file['Content']['Locality 1']['ComponentsInLocality'][
            'MaxNumBuildings']
        bool_list.append(len(components) == target_num_components)
        for component in components:
            bool_list.append('ResidentialBuilding' in component.name)
            bool_list.append(type(component).__name__ == 'StandardiReCoDeSComponent')
        assert all(bool_list)

    def test_load_building_data_information(self, r2d_system_creator: SystemCreator.SystemCreator,
                                            component_library: dict):
        bool_list = []
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        building_info_folder = r2d_system_creator.file['Content']['Locality 1']['ComponentsInLocality'][
            'BuildingsInfoFolder']
        building_id = 8000
        building_data = r2d_system_creator.load_building_data(building_id, building_info_folder)
        bool_list.append(building_data['Information']['GeneralInformation']['BIM_id'] == building_id)
        target_coords = [37.803317, -122.4429]
        bool_list.append(building_data['Information']['GeneralInformation']['Latitude'] == target_coords[0])
        bool_list.append(building_data['Information']['GeneralInformation']['Longitude'] == target_coords[1])
        target_plan_area = 57242.0
        bool_list.append(building_data['Information']['GeneralInformation']['PlanArea'] == target_plan_area)
        target_num_stories = 1
        bool_list.append(building_data['Information']['GeneralInformation']['NumberOfStories'] == target_num_stories)

    def test_load_building_data_damage(self, r2d_system_creator: SystemCreator.SystemCreator, component_library: dict):
        bool_list = []
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        building_info_folder = r2d_system_creator.file['Content']['Locality 1']['ComponentsInLocality'][
            'BuildingsInfoFolder']
        building_id = 8000
        building_data = r2d_system_creator.load_building_data(building_id, building_info_folder)
        scenario_id = 0
        target_damage_state = 2
        bool_list.append(building_data['Damage']['highest_damage_state/S'][scenario_id] == target_damage_state)
        target_reconstruction_cost = 813408.82
        bool_list.append(
            math.isclose(building_data['Damage']['reconstruction/cost'][scenario_id], target_reconstruction_cost))
        target_reconstruction_time = 30
        bool_list.append(building_data['Damage']['reconstruction/time'][scenario_id] == target_reconstruction_time)
        assert all(bool_list)

    def test_get_building_location(self, r2d_system_creator: SystemCreator.SystemCreator, component_library: dict):
        bool_list = []
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        building_info_folder = r2d_system_creator.file['Content']['Locality 1']['ComponentsInLocality'][
            'BuildingsInfoFolder']
        building_ids = [8000, 8001, 8002, 8003]
        target_locations = [[37.803317, -122.4429], [37.799682, -122.434602], [37.797494, -122.434566],
                            [37.796672, -122.43739]]
        for target_location, building_id in zip(target_locations, building_ids):
            building_data = r2d_system_creator.load_building_data(building_id, building_info_folder)
            building_location = r2d_system_creator.get_building_location(building_data)
            bool_list.append(all([math.isclose(i, j) for i, j in zip(target_location, building_location)]))
        assert all(bool_list)

    def test_building_location_inside_building_box(self, r2d_system_creator: SystemCreator.SystemCreator,
                                                   component_library: dict):
        bool_list = []
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        building_info_folder = r2d_system_creator.file['Content']['Locality 1']['ComponentsInLocality'][
            'BuildingsInfoFolder']
        building_ids = [8000, 8001, 8002, 8003]
        bounding_box = {'Latitude': [37.797, 37.8], 'Longitude': [-122.44, -122.43]}
        target_bools = [False, True, True, False]
        for target_bool, building_id in zip(target_bools, building_ids):
            building_data = r2d_system_creator.load_building_data(building_id, building_info_folder)
            building_location = r2d_system_creator.get_building_location(building_data)
            building_in_bounding_box = r2d_system_creator.building_location_inside_bounding_box(building_location,
                                                                                                bounding_box)
            bool_list.append(target_bool == building_in_bounding_box)
        assert all(bool_list)

    def test_building_is_residential(self, r2d_system_creator: SystemCreator.SystemCreator, component_library: dict):
        bool_list = []
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        building_info_folder = r2d_system_creator.file['Content']['Locality 1']['ComponentsInLocality'][
            'BuildingsInfoFolder']
        building_ids = [8000, 8001, 8002, 8003]
        target_bools = [False, True, False, True]
        for target_bool, building_id in zip(target_bools, building_ids):
            building_data = r2d_system_creator.load_building_data(building_id, building_info_folder)
            building_is_residential = r2d_system_creator.building_is_residential(building_data)
            bool_list.append(target_bool == building_is_residential)
        assert all(bool_list)

    def test_get_building_damage_state(self, r2d_system_creator: SystemCreator.SystemCreator, component_library: dict):
        bool_list = []
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        building_info_folder = r2d_system_creator.file['Content']['Locality 1']['ComponentsInLocality'][
            'BuildingsInfoFolder']
        building_id = 8000
        building_data = r2d_system_creator.load_building_data(building_id, building_info_folder)
        scenario_ids = list(range(5))
        target_DSs = [2, 3, 2, 0, 4]
        for target_DS, scenario_id in zip(target_DSs, scenario_ids):
            r2d_system_creator.scenario_id = scenario_id
            damage_state = r2d_system_creator.get_building_damage_state(building_data)
            bool_list.append(damage_state == target_DS)
        assert all(bool_list)

    def test_get_total_building_area(self, r2d_system_creator: SystemCreator.SystemCreator, component_library: dict):
        bool_list = []
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        building_info_folder = r2d_system_creator.file['Content']['Locality 1']['ComponentsInLocality'][
            'BuildingsInfoFolder']
        building_ids = [8000, 8001, 8002, 8004]
        target_areas = [57242.0, 6200.0, 6240.0, 13404.0]
        for target_area, building_id in zip(target_areas, building_ids):
            building_data = r2d_system_creator.load_building_data(building_id, building_info_folder)
            building_area = r2d_system_creator.get_total_building_area(building_data)
            bool_list.append(target_area == building_area)
        assert all(bool_list)

    def test_get_building_housing_capacity(self, r2d_system_creator: SystemCreator.SystemCreator,
                                           component_library: dict):
        bool_list = []
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        building_info_folder = r2d_system_creator.file['Content']['Locality 1']['ComponentsInLocality'][
            'BuildingsInfoFolder']
        building_ids = [8000, 8001, 8002, 8004]
        target_housing_capacities = [105, 11, 11, 24]
        r2d_system_creator.set_building_area_per_person()
        for target_housing_capacity, building_id in zip(target_housing_capacities, building_ids):
            building_data = r2d_system_creator.load_building_data(building_id, building_info_folder)
            building_housing_capacity = r2d_system_creator.get_building_housing_capacity('Locality 1', building_data)
            bool_list.append(target_housing_capacity == building_housing_capacity)
        assert all(bool_list)

    def test_set_building_housing_supply_demand(self, r2d_system_creator: SystemCreator.SystemCreator,
                                                component_library: dict):
        bool_list = []
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        building_info_folder = r2d_system_creator.file['Content']['Locality 1']['ComponentsInLocality'][
            'BuildingsInfoFolder']
        building_ids = [8000, 8001, 8002, 8004]
        target_housing_capacities = [105, 11, 11, 24]
        locality = 'Locality 1'
        r2d_system_creator.set_building_area_per_person()
        for target_housing_capacity, building_id in zip(target_housing_capacities, building_ids):
            building_data = r2d_system_creator.load_building_data(building_id, building_info_folder)
            building_DS = r2d_system_creator.get_building_damage_state(building_data)
            component = copy.deepcopy(r2d_system_creator.component_library[f'DS{building_DS}_ResidentialBuilding'])
            r2d_system_creator.set_building_housing_supply(component, locality, building_data)
            r2d_system_creator.set_building_housing_demand(component, locality, building_data)
            bool_list.append(component.supply['Supply']['Housing'].initial_amount == target_housing_capacity)
            bool_list.append(component.demand['OperationDemand']['Housing'].initial_amount == target_housing_capacity)

    def test_set_building_repair_cost(self, r2d_system_creator: SystemCreator.SystemCreator, component_library: dict):
        bool_list = []
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        building_info_folder = r2d_system_creator.file['Content']['Locality 1']['ComponentsInLocality'][
            'BuildingsInfoFolder']
        building_id = 8000
        building_data = r2d_system_creator.load_building_data(building_id, building_info_folder)
        scenario_ids = list(range(5))
        target_repair_costs = [813408.82, 3538328.367, 813408.82, 0, 8134088.2]  # veci repair cost za DS3 nego za DS4?
        for target_repair_cost, scenario_id in zip(target_repair_costs, scenario_ids):
            r2d_system_creator.scenario_id = scenario_id
            building_DS = r2d_system_creator.get_building_damage_state(building_data)
            component = copy.deepcopy(r2d_system_creator.component_library[f'DS{building_DS}_ResidentialBuilding'])
            r2d_system_creator.set_building_repair_cost(component, building_data)
            if building_DS != 0:
                bool_list.append(math.isclose(
                    component.recovery_model.recovery_activities['Financing'].demand['Money'].initial_amount,
                    target_repair_cost))
        assert all(bool_list)

    def test_set_repair_duration(self, r2d_system_creator: SystemCreator.SystemCreator, component_library: dict):
        bool_list = []
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        r2d_system_creator.DEFAULT_REPAIR_DURATION_DICT['Lognormal']['Dispersion'] = 0
        building_info_folder = r2d_system_creator.file['Content']['Locality 1']['ComponentsInLocality'][
            'BuildingsInfoFolder']
        building_id = 8000
        building_data = r2d_system_creator.load_building_data(building_id, building_info_folder)
        scenario_ids = list(range(5))
        target_repair_durations = [30, 120, 30, 0, 240]
        for target_repair_duration, scenario_id in zip(target_repair_durations, scenario_ids):
            r2d_system_creator.scenario_id = scenario_id
            building_DS = r2d_system_creator.get_building_damage_state(building_data)
            component = copy.deepcopy(r2d_system_creator.component_library[f'DS{building_DS}_ResidentialBuilding'])
            r2d_system_creator.set_repair_duration(component, building_data)
            if building_DS != 0:
                bool_list.append(math.isclose(component.recovery_model.recovery_activities['Repair'].duration,
                                              target_repair_duration))
        assert all(bool_list)

    def test_get_repair_crew_demand(self, r2d_system_creator: SystemCreator.SystemCreator):
        building_DSs = [1, 2, 3, 4]
        building_areas = [1000, 10000, 10000, 20000]
        bool_list = []
        target_repair_crew_demands = [1, 2, 4, 8]
        for i, building_area in enumerate(building_areas):
            repair_crew_demand = r2d_system_creator.get_repair_crew_demand(building_DSs[i], building_area)
            bool_list.append(repair_crew_demand == target_repair_crew_demands[i])
        assert all(bool_list)

    def test_create_residential_building(self, r2d_system_creator: SystemCreator.SystemCreator,
                                         component_library: dict):
        bool_list = []
        r2d_system_creator.setup(component_library, self.system_configuration_file)
        r2d_system_creator.DEFAULT_REPAIR_DURATION_DICT['Lognormal']['Dispersion'] = 0
        building_info_folder = r2d_system_creator.file['Content']['Locality 1']['ComponentsInLocality'][
            'BuildingsInfoFolder']
        building_ids = [8001, 8005, 8020]
        scenario_ids = [2, 4]
        locality = 'Locality 1'
        target_repair_durations = [[30, 120, 240], [0, 5, 5]]
        target_repair_costs = [[40300, 3276525.175, 2014177.5], [0, 158669.5, 40283.55]]
        target_repair_demands = [[2, 22, 12], [0, 11, 6]]
        target_housing_capacities = [[11, 106, 53], [11, 106, 53]]
        target_DSs = [[2, 3, 4], [0, 1, 1]]
        r2d_system_creator.set_building_area_per_person()
        for i, scenario_id in enumerate(scenario_ids):
            r2d_system_creator.scenario_id = scenario_id
            for ii, building_id in enumerate(building_ids):
                building_data = r2d_system_creator.load_building_data(building_id, building_info_folder)
                component = r2d_system_creator.create_residential_building(locality, building_data)
                bool_list.append(component.name == f'DS{target_DSs[i][ii]}_ResidentialBuilding')
                bool_list.append(
                    component.supply['Supply']['Housing'].initial_amount == target_housing_capacities[i][ii])
                bool_list.append(
                    component.demand['OperationDemand']['Housing'].initial_amount == target_housing_capacities[i][ii])
                if target_DSs[i][ii] != 0:
                    bool_list.append(math.isclose(component.recovery_model.recovery_activities['Repair'].duration,
                                                  target_repair_durations[i][ii]))
                    bool_list.append(
                        component.recovery_model.recovery_activities['Repair'].demand['RepairCrew'].initial_amount ==
                        target_repair_demands[i][ii])
                if target_DSs[i][ii] > 1:
                    bool_list.append(math.isclose(
                        component.recovery_model.recovery_activities['Financing'].demand['Money'].initial_amount,
                        target_repair_costs[i][ii]))
        assert all(bool_list)
