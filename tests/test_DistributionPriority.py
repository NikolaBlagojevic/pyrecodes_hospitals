import pytest
from pyrecodes_hospitals import main
from pyrecodes_hospitals import DistributionPriority
from pyrecodes_hospitals import System

class TestDistributionPriority():

    @pytest.fixture
    def system(self):
        input_dict = main.read_file(self.FILENAME)
        system = main.create_system(input_dict)
        return system


class TestComponentBasedDistributionPriority_ThreeLocalitiesCommunity(TestDistributionPriority):

    FILENAME = './tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_Main.json'

    def test_get_locality_id_from_string(self):
        example_strings = [['Locality 1'], ['Locality 123'], ['Locality 435'], ['Locality 1', 'Locality 100']]
        target_ids = [[1], [123], [435], [1, 100]]
        bool_list = []
        for example_string, target_id in zip(example_strings, target_ids):
            locality_id = DistributionPriority.ComponentBasedPriority.get_locality_id_from_string(example_string)
            bool_list.append(locality_id == target_id)

        assert all(bool_list)

    def test_component_not_already_in_priority_list(self, system: System.System):
        # component = list(component_library.values())[0]
        component = system.components[0]
        bool_list = []
        bool_list.append(not (DistributionPriority.ComponentBasedPriority.component_not_already_in_priority_list(None)))
        bool_list.append(DistributionPriority.ComponentBasedPriority.component_not_already_in_priority_list(component))
        assert all(bool_list)

    def test_find_component_position(self, system: System.System):
        components = system.components
        distribution_priority = system.resources['ElectricPower']['DistributionModel'].priority
        target_components = [['BaseTransceiverStation_1', ['Locality 1']], ['ElectricPowerPlant', ['Locality 1']],
                             ['BuildingStockUnit', ['Locality 3']], ['SuperLink', ['Locality 1', 'Locality 2']]]
        target_positions = [0, 1, 7, 2]
        bool_list = []
        for target_component, target_position in zip(target_components, target_positions):
            component_position, temp_components = distribution_priority.find_component_position(target_component[0],
                                                                                                target_component[1],
                                                                                                components)
            bool_list.append(component_position == target_position)
        assert all(bool_list)

    def test_find_component_position_error(self, system: System.System):
        distribution_priority = system.resources['ElectricPower']['DistributionModel'].priority
        with pytest.raises(ValueError):
            distribution_priority.find_component_position('ElectricPowerPlant', ['Locality 3'], system.components)

    def test_set_distribution_priority(self, system: System.System):
        target_priorities = [[1, 0, 4, 8, 7], [4, 1, 0, 8, 7], [0, 8, 1, 4, 7]]
        bool_list = []
        for target_priority, resource_parameters in zip(target_priorities, system.resources.values()):
            component_positions, demand_types = resource_parameters[
                'DistributionModel'].priority.get_component_priorities()
            bool_list.append(target_priority == component_positions)
            bool_list.append(all([demand_type == 'OperationDemand' for demand_type in demand_types]))
        assert all(bool_list)

class TestComponentTypeBasedPriority(TestDistributionPriority):

    FILENAME = './tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_Main.json'

    @pytest.fixture
    def distribution_priority(self, system: System.System):
        distribution_priority = DistributionPriority.ComponentTypeBasedPriority(resource_name='Resource 1', 
                                                                                parameters=[['ElectricPowerPlant', 'OperationDemand'], 
                                                                                            ['CoolingWaterFacility', 'OperationDemand'], 
                                                                                            ['BuildingStockUnit', 'OperationDemand']],
                                                                                components=system.components)
        return distribution_priority

    def test_categorize_components_based_on_type(self, distribution_priority: DistributionPriority.DistributionPriority):
        categorized_components_dict = distribution_priority.categorize_components_based_on_type()
        bool_list = []
        bool_list.append(categorized_components_dict['BaseTransceiverStation_1'] == [0])
        bool_list.append(categorized_components_dict['ElectricPowerPlant'] == [1])
        bool_list.append(categorized_components_dict['SuperLink'] == [2, 3, 5, 6, 9, 10])
        bool_list.append(categorized_components_dict['CoolingWaterFacility'] == [4])
        bool_list.append(categorized_components_dict['BuildingStockUnit'] == [7])
        bool_list.append(categorized_components_dict['BaseTransceiverStation_2'] == [8])
        assert all(bool_list)

    def test_set_distribution_priority(self, distribution_priority: DistributionPriority.DistributionPriority):
        assert distribution_priority.get_component_priorities() == ([1, 4, 7], ['OperationDemand', 'OperationDemand', 'OperationDemand'])
        