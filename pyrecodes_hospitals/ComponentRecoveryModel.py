import math
from abc import ABC, abstractmethod
from pyrecodes_hospitals import ProbabilityDistribution
from pyrecodes_hospitals import Relation
from pyrecodes_hospitals import Resource


class RecoveryActivity(ABC):
    level: float
    duration: float
    rate: float
    preceding_activities: list([str])
    preceding_activities_finished: bool
    demand_met: float
    name: str
    time_steps: list([int])

    @abstractmethod
    def __init__(self, name: str) -> None:
        pass

    @abstractmethod
    def set_name(self, name: str) -> None:
        pass

    @abstractmethod
    def set_level(self, level: float) -> None:
        pass

    @abstractmethod
    def set_duration(self, distribution: dict) -> None:
        pass

    @abstractmethod
    def sample_duration(self, distribution: dict) -> float:
        pass

    @abstractmethod
    def set_preceding_activities(self, preceding_activities: list([str])) -> None:
        pass    

    @abstractmethod
    def set_preceding_activities_finished(self, finished: bool) -> None:
        pass

    @abstractmethod
    def set_demand(self, resources: list) -> None:
        pass

    @abstractmethod
    def set_demand_met(self) -> None:
        pass

    @abstractmethod
    def get_demand(self) -> dict:
        pass

    @abstractmethod
    def recover(self, time_step: int) -> None:
        pass

    @abstractmethod
    def record_progress(self, time_step: int) -> None:
        pass

    @abstractmethod
    def activity_finished(self) -> bool:
        pass


class ConcreteRecoveryActivity(RecoveryActivity):

    def __init__(self, name: str, initial_level=0.0) -> None:
        self.set_name(name)
        self.set_level(initial_level)
        self.time_steps = []
        self.demand_met = 1.0
        self.demand = {}
        self.preceding_activities_finished = False

    def set_name(self, name: str) -> None:
        self.name = name

    def set_level(self, level: float) -> None:
        if 0 <= level <= 1:
            self.level = level
        else:
            raise ValueError(f'Level must be between 0 and 1. Recovery activity: {self.name}.')

    def set_duration(self, distribution: dict) -> None:
        duration = self.sample_duration(distribution)
        self.duration = duration
        if duration > 0:            
            self.rate = 1 / duration
        elif duration == 0: 
            self.rate = math.inf    
        else:       
            raise ValueError(f'Recovery Activity Duration must be higher than 0. Recovery activity: {self.name}.')

    def sample_duration(self, distribution: dict) -> float:
        distribution_name, distribution_parameters = list(distribution.items())[0]
        target_distribution = getattr(ProbabilityDistribution, distribution_name)
        distribution = target_distribution(distribution_parameters)
        return distribution.sample()

    def set_preceding_activities(self, preceding_activities: list([str])) -> None:
        self.preceding_activities = preceding_activities

    def set_preceding_activities_finished(self, finished: bool) -> None:
        self.preceding_activities_finished = finished

    def set_demand(self, resources: list) -> None:
        for resource in resources:
            resource_name = resource['Resource']
            resource_parameters = {'Amount': resource['Amount']}          
            self.demand[resource_name] = Resource.ConcreteResource(resource_name, resource_parameters)

    # single demand met but multiple resources possible in set_demand? This should be fixed later.
    def set_demand_met(self, demand_met: float) -> None:
        if 0 <= demand_met <= 1:
            self.demand_met = demand_met
        else:
            raise ValueError(f'Demand Met must be between 0 and 1. Recovery activity: {self.name}.')

    def get_demand(self) -> dict:
        return self.demand

    def recover(self, time_step: int) -> None:
        if self.demand_met > 0 and not (self.activity_finished()):
            self.record_progress(time_step)
            self.level = min(self.level + self.rate * self.demand_met,
                             1.0) 

    def record_progress(self, time_step: int) -> None:
        if time_step >= 0:
            self.time_steps.append(time_step)
        else:
            raise ValueError('Time step must be a positive number.')

    def activity_finished(self) -> bool:
        return math.isclose(self.level, 1.0)


class RecoveryModel(ABC):
    recovery_activities: dict

    @abstractmethod
    def set_parameters(self, parameters: dict) -> None:
        pass

    @abstractmethod
    def set_initial_damage_level(self, damage_level: float) -> None:
        pass

    @abstractmethod
    def set_damage_functionality(self, damage_functionality_relation: dict) -> None:
        pass

    @abstractmethod
    def set_activities_demand_to_met(self) -> None:
        pass

    @abstractmethod
    def recover(self, time_step: int) -> None:
        pass

    @abstractmethod
    def get_functionality_level(self) -> float:
        pass

    @abstractmethod
    def get_demand(self) -> dict:
        pass

    @abstractmethod
    def set_unmet_demand_for_recovery_activities(self, resource_name: str, percent_of_met_demand: float) -> None:
        pass


class NoRecoveryActivity(RecoveryModel):
    """
    Recovery model for components that did not experience damage.
    """
    damage_level: float
    recovery_activities: dict

    # is there a better way for this method than to have an input that is not used?
    def set_parameters(self, parameters: dict) -> None:
        self.recovery_activities = {}

    def set_initial_damage_level(self, damage_level: float) -> None:
        if damage_level != 0:
            raise ValueError('Initial damage level for NoRecoveryActivity model must be 0.')

    def set_damage_functionality(self, damage_functionality_relation: dict) -> None:
        pass   

    def set_activities_demand_to_met(self) -> None:
        pass

    def recover(self, time_step: int) -> None:
        pass

    def get_functionality_level(self) -> float:
        return 1.0

    def get_damage_level(self) -> float:
        return 0

    def get_demand(self) -> dict:
        return {}    

    def set_unmet_demand_for_recovery_activities(self, resource_name: str, percent_of_met_demand: float) -> None:
        pass


class SingleRecoveryActivity(RecoveryModel):
    """
    Component recovery model that only considers component repair as a single activity.
    Consider merging with multiple recovery activities - pretty much the same.
    """

    damage_level: float
    damage_to_functionality_relation: Relation.Relation
    recovery_activity: RecoveryActivity

    def __init__(self):
        self.recovery_activities = {}

    def set_parameters(self, parameters: dict) -> None:
        activity_name, activity_parameters = list(parameters.items())[0]
        self.recovery_activity = ConcreteRecoveryActivity(activity_name, initial_level=1.0)
        self.recovery_activity.set_duration(activity_parameters.get('Duration', ''))
        self.recovery_activity.set_demand(activity_parameters.get('Demand', ''))

    def set_initial_damage_level(self, damage_level: float) -> None:
        if 0 <= damage_level <= 1:
            self.recovery_activity.level = 1 - damage_level
            self.recovery_activity.rate = damage_level / self.recovery_activity.duration
        else:
            raise ValueError('Damage level must be between 0 and 1.')

    def set_damage_functionality(self, damage_functionality_relation) -> None:
        target_damage_functionality = getattr(Relation, damage_functionality_relation['Type'])
        self.damage_to_functionality_relation = target_damage_functionality()

    def set_activities_demand_to_met(self) -> None:
        self.recovery_activity.set_demand_met(1.0)

    def recover(self, time_step: int) -> None:
        self.recovery_activity.recover(time_step)

    def get_functionality_level(self) -> float:
        return self.damage_to_functionality_relation.get_output(self.get_damage_level())

    def get_demand(self) -> dict:
        if self.get_damage_level() > 0 and not (
                                self.recovery_activity.activity_finished()):
            return self.recovery_activity.get_demand()
        else:
            return {}

    def get_damage_level(self) -> float:
        return 1 - self.recovery_activity.level

    def set_unmet_demand_for_recovery_activities(self, resource_name: str, percent_of_met_demand: float):
        if resource_name in self.recovery_activity.demand:
            self.recovery_activity.set_demand_met(percent_of_met_demand)
        else:
            raise ValueError(f'Resource {resource_name} ')


class MultipleRecoveryActivities(RecoveryModel):
    """"
    Component recovery model that considers multiple recovery activities:
    several impeding factors and a single repair activity.
    """

    damage_level: float
    damage_to_functionality_relation: Relation.Relation
    recovery_activities: dict

    def __init__(self, REPAIR_ACTIVITY_NAME = 'Repair') -> None:
        self.recovery_activities = {}
        self.REPAIR_ACTIVITY_NAME = REPAIR_ACTIVITY_NAME     

    def set_parameters(self, parameters: dict) -> None:
        for recovery_activity, recovery_activity_parameters in parameters.items():
            self.recovery_activities[recovery_activity] = ConcreteRecoveryActivity(recovery_activity, initial_level=1.0)
            self.recovery_activities[recovery_activity].set_preceding_activities(
                recovery_activity_parameters['PrecedingActivities'])
            self.recovery_activities[recovery_activity].set_duration(recovery_activity_parameters.get('Duration', ''))
            self.recovery_activities[recovery_activity].set_demand(recovery_activity_parameters.get('Demand', ''))

    def set_initial_damage_level(self, damage_level: float) -> None:
        if 0 <= damage_level <= 1:
            for recovery_activity_object in self.recovery_activities.values():
                recovery_activity_object.set_level(0.0)
            self.set_initial_repair_activity_state(damage_level)
        else:
            raise ValueError('Damage level must be between 0 and 1.')

    def set_initial_repair_activity_state(self, damage_level: float) -> None:
        self.recovery_activities[self.REPAIR_ACTIVITY_NAME].set_level(1 - damage_level)
        self.recovery_activities[self.REPAIR_ACTIVITY_NAME].rate = damage_level / self.recovery_activities[
            self.REPAIR_ACTIVITY_NAME].duration

    def set_damage_functionality(self, damage_functionality_relation: dict) -> None:
        target_damage_functionality = getattr(Relation, damage_functionality_relation['Type'])
        self.damage_to_functionality_relation = target_damage_functionality()

    def recover(self, time_step: int) -> None:
        self.check_preceding_activities()
        for recovery_activity_object in self.recovery_activities.values():
            if recovery_activity_object.preceding_activities_finished and self.get_damage_level() > 0:
                recovery_activity_object.recover(time_step)

    def check_preceding_activities(self) -> None:
        for recovery_activity_object in self.recovery_activities.values():
            if self.preceding_activities_finished(recovery_activity_object):
                recovery_activity_object.set_preceding_activities_finished(True)
            else:
                recovery_activity_object.set_preceding_activities_finished(False)

    def preceding_activities_finished(self, recovery_activity_object: RecoveryActivity) -> bool:
        for preceding_activity in recovery_activity_object.preceding_activities:
            if not (self.recovery_activities[preceding_activity].activity_finished()):
                return False
        return True

    def get_functionality_level(self) -> float:
        return self.damage_to_functionality_relation.get_output(self.get_damage_level())

    def get_damage_level(self) -> float:
        return 1 - self.recovery_activities[self.REPAIR_ACTIVITY_NAME].level

    def get_demand(self) -> dict:
        resource_dict = {}
        for recovery_activity in self.recovery_activities.values():
            if self.preceding_activities_finished(recovery_activity) and self.get_damage_level() > 0 and not (
                    recovery_activity.activity_finished()):
                recovery_activity_demand = recovery_activity.get_demand()
                if len(recovery_activity_demand) > 0:
                    resource_dict = {**resource_dict, **recovery_activity_demand}
        return resource_dict

    def set_activities_demand_to_met(self):
        for recovery_activity in self.recovery_activities.values():
            recovery_activity.set_demand_met(1.0)

    def set_unmet_demand_for_recovery_activities(self, resource_name: str, percent_of_met_demand: float):
        recovery_activity_to_update = self.find_recovery_activity_that_demands_the_resource(resource_name)
        recovery_activity_to_update.set_demand_met(percent_of_met_demand)

    def find_recovery_activity_that_demands_the_resource(self, resource_name: str):
        for recovery_activity in self.recovery_activities.values():
            if resource_name in recovery_activity.demand:
                return recovery_activity

class InfrastructureInterfaceRecoveryModel(RecoveryModel):
    """"
    Component recovery model for infrastructure interfaces
    to simulate the post-disaster supply/demand dynamics.
    """    
    
    def __init__(self) -> None:        
        self.recovery_activity = ConcreteRecoveryActivity('Recovery', initial_level=1.0)
        self.recovery_activity.set_duration({"Deterministic": {"Value": 1}})
        self.recovery_activity.set_demand('')     
        self.set_damage_functionality()
    
    def set_parameters(self, parameters: dict) -> None:
        self.damage_to_functionality_relation.set_steps(parameters['StepLimits'], parameters['StepValues'])        
        self.recovery_activity.set_duration(parameters['RestoredIn'][-1])

    def set_initial_damage_level(self, damage_level: float) -> None:
        self.damage_level = 1.0
        self.recovery_activity.level = 0.0

    def set_damage_functionality(self) -> None:
        target_damage_functionality = getattr(Relation, 'MultipleStep')
        self.damage_to_functionality_relation = target_damage_functionality()

    def set_activities_demand_to_met(self) -> None:
        pass

    def recover(self, time_step: int) -> None:
        self.recovery_activity.recover(time_step)

    def get_functionality_level(self) -> float:
        return self.damage_to_functionality_relation.get_output(1 - self.get_damage_level())
    
    def get_damage_level(self) -> float:
        return 1 - self.recovery_activity.level
    
    def get_demand(self) -> dict:
        return {}
    
    def set_unmet_demand_for_recovery_activities(self, resource_name: str, percent_of_met_demand: float) -> None:
        pass
