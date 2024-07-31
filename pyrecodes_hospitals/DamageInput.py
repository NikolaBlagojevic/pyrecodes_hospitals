
from abc import ABC, abstractmethod
import json
from pyrecodes_hospitals import Component


class DamageInput(ABC):
    """
    Different methods for providing initial component damage information to the system class
    """

    @abstractmethod
    def get_initial_damage(self) -> None:
        pass

    @abstractmethod
    def set_initial_damage(self, components: list) -> None:
        pass

class ConcreteDamageInput(DamageInput):

    def __init__(self, parameters):
        self.parameters = parameters

    def get_initial_damage(self):
        pass

    def set_initial_damage(self, components: list([Component.Component])):
        self.get_initial_damage() 
        for damage_level, component in zip(self.damage_levels, components):
            component.set_initial_damage_level(damage_level)

class ListDamageInput(ConcreteDamageInput):

    # where are the parameters set?
    def get_initial_damage(self):
        self.damage_levels = self.parameters

class R2DDamageInput(ConcreteDamageInput):
    DAMAGE_STATE_ID_POSITION_IN_COMPONENT_NAME = 2

    def get_initial_damage(self):
        pass

    def set_initial_damage(self, components: list([Component.Component])) -> None:
        for component in components:
            if self.component_is_damaged(component) or self.component_is_interface(component):
                component.set_initial_damage_level(1.0)

    def component_is_damaged(self, component: Component.Component) -> bool:
        damage_state = component.name[self.DAMAGE_STATE_ID_POSITION_IN_COMPONENT_NAME]
        if ('ResidentialBuilding' in component.name) and int(damage_state) > 0:
            return True
        else:
            return False
    
    def component_is_interface(self, component: Component.Component) -> bool:
        if isinstance(component, Component.InfrastructureInterface):
            return True
        else:
            return False

class FileDamageInput(ConcreteDamageInput):

    def get_initial_damage(self):
        with open(self.parameters, 'r') as file:
            damage_input_str = file.read()
        damage_input = list(map(float, damage_input_str.replace('\n', '').split(',')))
        self.damage_levels = damage_input

class HospitalStressScenarioInput(ConcreteDamageInput):

    def __init__(self, parameters):
        self.parameters = parameters

    def get_initial_damage(self) -> None:
        with open(self.parameters, 'r') as file:
            stress_scenario_json = json.load(file)
        self.stress_scenario = stress_scenario_json

    def set_initial_damage(self, components: list) -> None:
        """
        Stress scenario increases the demand for hospital services or decreases the supply of services.
        This is simulated by changing the supply/demand of PatientSource and Departments
        """
        self.get_initial_damage()
        print(f'Stress Scenario: {self.stress_scenario["StressScenarioName"]}')  
        for component_to_change_parameters in self.stress_scenario['ComponentsToChange']:      
            for component in components:
                if component.name == component_to_change_parameters['ComponentName']:
                    component.set_predefined_resource_dynamics(component_to_change_parameters['ResourcesToChange'])

