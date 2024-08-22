
import pytest
from pyrecodes_hospitals import SystemCreator
from pyrecodes_hospitals import ComponentLibraryCreator
from pyrecodes_hospitals import Component

class TestThreeLocalitiesJSONSystemCreator():
    COMPONENT_LIBRARY_FILE = "./tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_ComponentLibrary.json"
    SYSTEM_CONFIGURATION_FILE = './tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_SystemConfiguration.json'

    @pytest.fixture()
    def json_system_creator(self) -> SystemCreator.SystemCreator:
        return SystemCreator.JSONSystemCreator()

    @pytest.fixture()
    def component_library(self) -> ComponentLibraryCreator.JSONComponentLibraryCreator:
        return ComponentLibraryCreator.JSONComponentLibraryCreator(self.COMPONENT_LIBRARY_FILE)

    def form_component_library_for_testing(self, json_system_creator: SystemCreator.SystemCreator,
                                           component_library: ComponentLibraryCreator.ComponentLibraryCreator):
        formed_component_library = component_library.form_library()
        json_system_creator.set_component_library(formed_component_library)
        return json_system_creator

    def test_read_file(self, json_system_creator: SystemCreator.SystemCreator):
        json_system_creator.read_file(self.SYSTEM_CONFIGURATION_FILE)
        assert ('Content' in json_system_creator.system_configuration_file, 'DamageInput' in json_system_creator.system_configuration_file,
                'Resources' in json_system_creator.system_configuration_file) == (True, True, True)

    def test_set_component_library(self, json_system_creator: SystemCreator.SystemCreator,
                                   component_library: ComponentLibraryCreator.ComponentLibraryCreator):
        json_system_creator.set_component_library(component_library)
        assert isinstance(json_system_creator.component_library, ComponentLibraryCreator.JSONComponentLibraryCreator)

    def test_get_damage_input_type(self, json_system_creator: SystemCreator.SystemCreator):
        json_system_creator.read_file(self.SYSTEM_CONFIGURATION_FILE)
        assert json_system_creator.get_damage_input_type() == "ListDamageInput"

    def test_get_damage_input_params(self, json_system_creator: SystemCreator.SystemCreator):
        json_system_creator.read_file(self.SYSTEM_CONFIGURATION_FILE)
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
        json_system_creator.read_file(self.SYSTEM_CONFIGURATION_FILE)
        json_system_creator.create_components_between_localities(locality=locality_string,
                                                   content=json_system_creator.system_configuration_file['Content'][locality_string][
                                                       'LinkTo'])
        return json_system_creator

    def construct_create_components_in_localities_test(self, json_system_creator: SystemCreator.SystemCreator,
                                                       component_library: ComponentLibraryCreator.ComponentLibraryCreator,
                                                       locality_string: str):
        json_system_creator = self.form_component_library_for_testing(json_system_creator, component_library)
        json_system_creator.read_file(self.SYSTEM_CONFIGURATION_FILE)
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
        json_system_creator.read_file(self.SYSTEM_CONFIGURATION_FILE)
        components = json_system_creator.create_components()
        assert all([len(components) == 11]) == True