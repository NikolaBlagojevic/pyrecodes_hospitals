from abc import ABC, abstractmethod
from pyrecodes_hospitals import Relation

class Resource(ABC):
    name: str
    initial_amount: float
    current_amount: float
    component_functionality_to_amount: Relation
    unmet_demand_to_amount: Relation

    @abstractmethod
    def __init__(self, name: str, parameters: dict) -> None:
        pass

    @abstractmethod
    def set_current_amount(self, amount: float) -> None:
        pass

    @abstractmethod
    def update_based_on_component_functionality(self, functionality_level: float) -> None:
        pass

    @abstractmethod
    def update_based_on_unmet_demand(self, percent_of_met_demand: float) -> None:
        pass

class ConcreteResource(Resource):

    def __init__(self, name: str, parameters: dict) -> None:
        self.name = name
        self.set_initial_amount(parameters.get('Amount', 0.0))
        self.set_functionality_to_amount_relation(parameters.get('FunctionalityToAmountRelation', ''))
        self.set_unmet_demand_to_amount_relations(parameters.get('UnmetDemandToAmountRelation', {})) 

    def set_initial_amount(self, amount: float) -> None:
        if self.amount_is_a_positive_number(amount):
            self.initial_amount = amount
            self.current_amount = amount

    def set_current_amount(self, amount: float) -> None:
        if self.amount_is_a_positive_number(amount):
            self.current_amount = amount

    @staticmethod
    def amount_is_a_positive_number(amount) -> bool:
        if amount >= 0:
            return True
        else:
            raise ValueError('Resource amount must be a positive number.')

    def set_relation(self, relation_class_name: str, attribute_name: str) -> None:
        if len(relation_class_name) > 0:
            # default to Constant?
            try:
                target_relation = getattr(Relation, relation_class_name)
                setattr(self, attribute_name, target_relation())
            except:
                raise ValueError(f'Relation {relation_class_name} not defined.')

    def set_functionality_to_amount_relation(self, relation_class_name: str) -> None:
        self.set_relation(relation_class_name, 'component_functionality_to_amount')

    def set_unmet_demand_to_amount_relations(self, relation_class_name: dict) -> None:
        self.unmet_demand_to_amount = dict()
        for resource_name, relation_class_name in relation_class_name.items():
            target_relation = getattr(Relation, relation_class_name)
            self.unmet_demand_to_amount[resource_name] = target_relation()
            
    def update_based_on_component_functionality(self, component_functionality_level: float) -> None:
        self.current_amount = self.initial_amount * self.component_functionality_to_amount.get_output(
            component_functionality_level)

    def update_based_on_unmet_demand(self, resource_name: str, percent_of_met_demand: float) -> None:
        if resource_name in self.unmet_demand_to_amount:
            reduced_amount = self.initial_amount * self.unmet_demand_to_amount[resource_name].get_output(percent_of_met_demand)
            if reduced_amount < self.current_amount:
                self.current_amount = reduced_amount    

class ConsumableResource(ConcreteResource):
    """
    Class to simulate a resource whose supply decreases when it is consumed.
    """

    def update_supply_based_on_consumption(self, consumption: float) -> None:
        self.current_amount = max(0, self.current_amount - consumption)
    
    def update_based_on_component_functionality(self, component_functionality_level: float) -> None:
        # Not sure what should happen with consumable resources when the functionality of the component changes
        # Just keep the current amount as it is for now
        pass

class TimeStepsOfAutonomyResource(ConsumableResource):
    """
    Class to simulate a resource whose supply depends on time steps, not the amount.
    Used to capture the concept of "days of autonomy" - supply available for a certain number of time steps (days/hours), not a certain amount.
    """
    
    def update_based_on_component_functionality(self, component_functionality_level: float) -> None:
        pass

    def update_based_on_unmet_demand(self, resource_name: str, percent_of_met_demand: float) -> None:
        pass

    def update_supply_based_on_consumption(self, consumption: float) -> None:
        """
        Method is assumed to be called at each time step, so it reduces the current amount (time steps of autonomy) by 1.
        """
        self.current_amount = max(0, self.current_amount - 1)

class MinMaxConstrainedResource(ConcreteResource):
    """
    Class to simulate a resource whose demand is constrained by minimum and maximum values.
    Used to capture the demand for nurses in a hospital department.
    """

    def __init__(self, name: str, parameters: dict) -> None:
        super().__init__(name, parameters)
        self.set_min_max_constraints(parameters.get('MinMaxConstraints', {}))

    def set_min_max_constraints(self, min_max_constraints: dict) -> None:
        self.min_constraint = min_max_constraints.get('Min', 0)
        self.max_constraint = min_max_constraints.get('Max', float('inf'))

    def update_based_on_unmet_demand(self, resource_name: str, percent_of_met_demand: float) -> None:
        pass

    def update_based_on_component_functionality(self, component_functionality_level: float) -> None:
        pass

    def update_supply_based_on_consumption(self, consumption: float) -> None:
        pass

    def set_current_amount(self, amount: float) -> None:
        if self.amount_is_a_positive_number(amount):
            self.current_amount = max(self.min_constraint, min(self.max_constraint, amount))
        