from abc import ABC, abstractmethod
import math
from pyrecodes_hospitals import SystemCreator
from pyrecodes_hospitals import DamageInput
from pyrecodes_hospitals import Component
import pickle
from pyrecodes_hospitals import ResilienceCalculator

class System(ABC):
    components: list([Component.Component])
    resources: dict
    system_creator: SystemCreator.SystemCreator

    @abstractmethod
    def __init__(self, configuration_file: str, component_library: dict, system_creator: SystemCreator.SystemCreator):
        pass

    @abstractmethod
    def set_configuration_file(self, file_name: str):
        pass

    @abstractmethod
    def set_component_library(self, component_library: dict):
        pass

    @abstractmethod
    def create_system(self, system_creator: SystemCreator.SystemCreator):
        pass

    @abstractmethod
    def set_initial_damage(self):
        pass

    @abstractmethod
    def start_resilience_assessment(self):
        pass

    @abstractmethod
    def distribute_resources(self):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def recover(self):
        pass

    @abstractmethod
    def calculate_resilience(self):
        pass


class DistributionListCreator():
    """
    Creates a list specifying in which order the resources should be distributed to capture components' interdependencies and calculate consumption.
    Resource order is fixed: BridgeServices, Transfer Services, Independent Resources, Interdependent Resources.
    """

    components: list([Component.Component])
    resources: dict

    def __init__(self, components: list([Component.Component]), resources: dict):
        self.components = components
        self.resources = resources

    def get_resource_distribution_list(self):
        resource_distribution_list = []
        resource_distribution_list += self.get_resource_group('BridgeService')
        resource_distribution_list += self.get_resource_group('TransferService')
        independent_resources, interdependent_resources = self.get_independent_interdependent_resources(
            resource_distribution_list)
        resource_distribution_list += independent_resources
        resource_distribution_list += self.form_resource_distribution_vector(interdependent_resources)
        return resource_distribution_list

    def get_resource_group(self, group_name: str):
        resource_group = []
        for resource_name, resource_parameters in self.resources.items():
            if resource_parameters['Group'] == group_name:
                resource_group.append(resource_name)
        return resource_group

    def get_independent_interdependent_resources(self, resource_distribution_list: list([str])):
        interdependent_resources = []
        independent_resources = []
        for resource_name, resource_parameters in self.resources.items():
            if not (resource_name in resource_distribution_list):
                for component in self.components:
                    if component.has_resource_supply(resource_name) and component.has_operation_demand():
                        interdependent_resources.append(resource_name)
                        break
                else:
                    independent_resources.append(resource_name)

        return independent_resources, interdependent_resources

    def form_resource_distribution_vector(self, interdependent_resources):
        num_resources = len(interdependent_resources)
        return interdependent_resources * num_resources

class HospitalResourceDistributionListCreator(DistributionListCreator):

    def get_independent_interdependent_resources(self, resource_distribution_list: list([str])):
        interdependent_resources = []
        independent_resources = list(self.resources.keys())
        return independent_resources, interdependent_resources


class RecoveryTargetChecker(ABC):
    """
    Checks whether the system has recovered and the resilience assessment interval is finished.
    """

    @abstractmethod
    def recovery_target_met(self, system: System) -> bool:
        pass


class CompleteDamageRecoveryTargetChecker(RecoveryTargetChecker):
    """"
    The system has recovered once all components are damage-free.
    """

    def recovery_target_met(self, system: System) -> bool:
        if system.time_step <= system.DISASTER_TIME_STEP:
            return False
        else:
            for component in system.components:
                if not (math.isclose(component.get_damage_level(), 0, abs_tol=1e-10)):
                    return False
        return True


class BuiltEnvironmentSystem(System):
    """
    iRe-CoDeS model of the Built Environment viewed as an assembly of components that exchange resources.
    """

    components: list([Component.Component])
    resources: dict
    system_creator: SystemCreator.SystemCreator
    FINISH = False

    def __init__(self, configuration_file: str, component_library: dict, system_creator: SystemCreator.SystemCreator):
        self.set_configuration_file(configuration_file)
        self.set_component_library(component_library)
        self.set_system_creator(system_creator)
        self.create_system()

    def __str__(self):
        system_state = ''
        for component in self.components:
            system_state += f'{component.__str__()} | Damage Level: {component.get_damage_level()} \n'
        return system_state

    def set_configuration_file(self, file_name: str):
        self.configuration_file = file_name

    def set_component_library(self, component_library: dict):
        self.component_library = component_library

    def set_system_creator(self, system_creator: SystemCreator.SystemCreator):
        self.system_creator = system_creator

    def create_system(self):
        self.system_creator.setup(self.component_library, self.configuration_file)
        self.components = self.system_creator.create_components()
        self.resources = self.system_creator.get_resource_parameters(self.components)
        self.resilience_calculators = self.system_creator.get_resilience_calculators()
        self.START_TIME_STEP = self.system_creator.START_TIME_STEP
        self.MAX_TIME_STEP = self.system_creator.MAX_TIME_STEP
        self.DISASTER_TIME_STEP = self.system_creator.DISASTER_TIME_STEP
        self.recovery_target_checker = CompleteDamageRecoveryTargetChecker()
        self.set_resource_distribution_list()
        self.set_damage_input()

    def set_resource_distribution_list(self):
        distribution_list_creator = DistributionListCreator(self.components, self.resources)
        self.resource_distribution_list = distribution_list_creator.get_resource_distribution_list()
    
    def set_damage_input(self):
        target_damage_input_class = getattr(DamageInput, self.system_creator.get_damage_input_type())
        self.damage_input = target_damage_input_class(self.system_creator.get_damage_input_parameters())        

    def start_resilience_assessment(self):

        for self.time_step in range(self.START_TIME_STEP, self.MAX_TIME_STEP):

            if self.recovery_target_met():
                self.FINISH = True

            if self.time_step == self.DISASTER_TIME_STEP:
                self.set_initial_damage()

            self.update()

            self.distribute_resources()

            self.update_resilience_calculators()

            if self.time_step > self.DISASTER_TIME_STEP:
                self.recover()

            if self.FINISH:
                print('Resilience assessment finished.')
                break

    def recovery_target_met(self) -> bool:
        return self.recovery_target_checker.recovery_target_met(self)

    def set_initial_damage(self) -> None:        
        self.damage_input.set_initial_damage(self.components)

    def update(self) -> None:
        for component in self.components:
            component.update(self.time_step)

    def distribute_resources(self) -> None:
        for resource_name in self.resource_distribution_list:
            self.resources[resource_name]['DistributionModel'].distribute()

    def recover(self) -> None:
        for component in self.components:
            component.recover(self.time_step)

    def update_resilience_calculators(self) -> None:
        for resilience_calculator in self.resilience_calculators:
            resilience_calculator.update(self.resources)

    def calculate_resilience(self) -> dict:
        resilience_metrics = []
        for resilience_calculator in self.resilience_calculators:
            resilience_metrics.append(resilience_calculator.calculate_resilience())
        return resilience_metrics
    
    def save_as_pickle(self, savename='./system_object.pickle') -> None:
        with open(savename, 'wb') as file:
            pickle.dump(self, file) 
    
    def load_as_pickle(self, loadname='./system_object.pickle') -> None:
        with open(loadname, 'rb') as file:
            system = pickle.load(file) 
        return system

class HospitalSystem(BuiltEnvironmentSystem):
    """
    Class to assess resilience of a hospital.
    """

    def set_resource_distribution_list(self):
        distribution_list_creator = HospitalResourceDistributionListCreator(self.components, self.resources)
        self.resource_distribution_list = distribution_list_creator.get_resource_distribution_list()

    def start_resilience_assessment(self, progressBar=None, app=None):
        """
        Override parent method by removing the recovery_target_checker and not recovering components.
        Component's change their supply and demand based on predefined resource dynamics, not change in damage.
        """
        for self.time_step in range(self.START_TIME_STEP, self.MAX_TIME_STEP+1):

            self.update_progress_bar(progressBar, app)
            
            if self.time_step == self.DISASTER_TIME_STEP:
                self.set_initial_damage()

            self.receive_patients()

            self.update()

            self.distribute_resources()

            self.update_patients()           

            self.update_resilience_calculators()

        print('Resilience assessment finished.')

    def update(self) -> None:
        """
        Override parent method by adding consumption as an argument when updating components.
        NOTE: this method requires that the Re-CoDeS resilience calculator is used and that its scope is "All".
        """
        for component in self.components:
            component.update(self.time_step, self.resilience_calculators[0].system_consumption)

    def receive_patients(self) -> None:
        """
        Method to distribute the patients to departments based on their length of stay and met demand.
        """
        for component in self.components:
            if isinstance(component, Component.PatientSource):
                component.create_patients(self.time_step)
        
        patients_to_move = []
        for component in self.components:
            patients_to_move += component.get_patients_that_move()

        for component in self.components:
            component.set_new_patients(patients_to_move)
            
    def update_patients(self) -> None:
        for component in self.components:
            component.update_patient_status(self.time_step)
    
    def update_resilience_calculators(self) -> None:
        # TODO: Refactor - input for all resilience calculators should be the same!
        for resilience_calculator in self.resilience_calculators:
            if isinstance(resilience_calculator, ResilienceCalculator.PatientFlowCalculator) or isinstance(resilience_calculator, ResilienceCalculator.DeadPatientsCalculator) or isinstance(resilience_calculator, ResilienceCalculator.HospitalMeasureOfServiceCalculator):
                resilience_calculator.update(self.components)
            else:
                resilience_calculator.update(self.resources)
    
    def update_progress_bar(self, progressBar, app):
        if progressBar is not None:
            progressBar.setProperty("value", (self.time_step/self.MAX_TIME_STEP)*100)
            app.processEvents()