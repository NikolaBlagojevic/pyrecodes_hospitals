import pytest
from pyrecodes_hospitals import ComponentLibraryCreator


class TestJSONComponentLibraryCreator_ThreeLocalitiesCommunity():
    COMPONENT_LIBRARY_FILE = './tests/test_inputs/test_inputs_ThreeLocalitiesCommunity_ComponentLibrary.json'

    @pytest.fixture
    def component_library_creator(self):
        return ComponentLibraryCreator.JSONComponentLibraryCreator(self.COMPONENT_LIBRARY_FILE)

    def test_init(self, component_library_creator: ComponentLibraryCreator.ComponentLibraryCreator):
        bool_list = []
        for component_name, component_parameters in component_library_creator.file.items():
            bool_list.append('ComponentClass' in component_parameters)
            bool_list.append('RecoveryModel' in component_parameters)
            bool_list.append('Type' in component_parameters['RecoveryModel'])
            bool_list.append('Parameters' in component_parameters['RecoveryModel'])
            bool_list.append('DamageFunctionalityRelation' in component_parameters['RecoveryModel'])
            if component_name != 'BuildingStockUnit' and component_name != 'SuperLink':
                bool_list.append('Supply' in component_parameters)
                bool_list.append('OperationDemand' in component_parameters)
        print(bool_list)
        assert all(bool_list)

    def test_form_component_BTS1(self, component_library_creator: ComponentLibraryCreator.ComponentLibraryCreator):
        bool_list = []
        component_name = 'BaseTransceiverStation_1'
        component_parameters = component_library_creator.file[component_name]
        component = component_library_creator.form_component(component_name, component_parameters)
        bool_list.append(type(component).__name__ == 'StandardiReCoDeSComponent')
        bool_list.append(type(component.recovery_model).__name__ == 'SingleRecoveryActivity')
        bool_list.append(component.recovery_model.recovery_activity.duration == 10)
        bool_list.append(type(component.recovery_model.damage_to_functionality_relation).__name__ == 'ReverseBinary')
        bool_list.append(component.supply['Supply']['Communication'].initial_amount == 1)
        bool_list.append(component.supply['Supply']['Communication'].current_amount == 1)
        bool_list.append(
            type(component.supply['Supply']['Communication'].component_functionality_to_amount).__name__ == 'Linear')
        bool_list.append(type(component.supply['Supply']['Communication'].unmet_demand_to_amount['ElectricPower']).__name__ == 'Binary')
        bool_list.append(component.demand['OperationDemand']['ElectricPower'].initial_amount == 1)
        bool_list.append(component.demand['OperationDemand']['ElectricPower'].current_amount == 1)
        bool_list.append(type(component.demand['OperationDemand'][
                                  'ElectricPower'].component_functionality_to_amount).__name__ == 'Linear')
        assert all(bool_list)

    def test_form_library(self, component_library_creator: ComponentLibraryCreator.ComponentLibraryCreator):
        component_library = component_library_creator.form_library()
        component_type_names = ['BaseTransceiverStation_1', 'BaseTransceiverStation_2', 'ElectricPowerPlant',
                                'CoolingWaterFacility', 'BuildingStockUnit', 'SuperLink']
        components_in_library = [component_type_name in component_library for component_type_name in
                                 component_type_names]
        assert len(component_library) == 6 and all(components_in_library)
