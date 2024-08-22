import pytest
from pyrecodes_hospitals import Resource
from pyrecodes_hospitals import Relation

class TestConcreteResource():

    NAME = 'Resource 1'

    PARAMETERS = {"Amount": 5,
                "ResourceClassName": "ConcreteResource",
                "FunctionalityToAmountRelation": "Linear"}
    
    UNMET_DEMAND_PARAMETERS = {
                    "Resource 2": "Binary",
                    "Resource 3": "ReverseBinary"
                }

    @pytest.fixture
    def resource(self):
        return Resource.ConcreteResource(self.NAME, self.PARAMETERS)

    def test_init_(self, resource: Resource.ConcreteResource):
        assert resource.name == 'Resource 1' and resource.initial_amount == 5.0 and resource.current_amount == 5.0

    def test_set_INITIAL_AMOUNT(self, resource: Resource.ConcreteResource):
        bool_list = []
        assert resource.initial_amount == 5.0
        assert resource.current_amount == 5.0
        resource.set_initial_amount(50.0)
        assert resource.initial_amount == 50.0
        assert resource.current_amount == 50.0
        resource.set_initial_amount(50.0)
        assert resource.initial_amount == 50
        assert resource.current_amount == 50
        resource.set_initial_amount(0)
        assert resource.initial_amount == 0
        assert resource.current_amount == 0

    def test_set_current_amount(self, resource: Resource.ConcreteResource):
        assert resource.initial_amount == 5.0
        assert resource.current_amount == 5.0

        resource.set_current_amount(50.0)
        assert resource.initial_amount == 5.0
        assert resource.current_amount == 50.0

        resource.set_current_amount(50.0)
        assert resource.initial_amount == 5
        assert resource.current_amount == 50

        resource.set_current_amount(0)
        assert resource.initial_amount == 5
        assert resource.current_amount == 0     

    def test_set_current_amount_with_negative_value(self, resource: Resource.ConcreteResource):
        with pytest.raises(ValueError):
            resource.set_current_amount(-1)

    def test_set_relation(self, resource: Resource.ConcreteResource):
        resource.set_relation('Constant', 'component_functionality_to_amount')
        assert type(resource.component_functionality_to_amount) == Relation.Constant
        resource.set_relation('Linear', 'component_functionality_to_amount')
        assert type(resource.component_functionality_to_amount) == Relation.Linear
        resource.set_relation('Linear', 'something')
        assert type(resource.something) == Relation.Linear

    def test_set_relation_wrong(self, resource: Resource.ConcreteResource):
        with pytest.raises(ValueError):
            resource.set_relation('NoRelation', 'component_functionality_to_amount')

    def test_set_functionality_to_amount_relation(self, resource: Resource.ConcreteResource):
        resource.set_functionality_to_amount_relation('ReverseLinear')
        assert type(resource.component_functionality_to_amount) == Relation.ReverseLinear

    def test_set_unmet_demand_to_amount_relations(self, resource: Resource.ConcreteResource):
        resource.set_unmet_demand_to_amount_relations(self.UNMET_DEMAND_PARAMETERS)
        assert type(resource.unmet_demand_to_amount['Resource 2']) == Relation.Binary
        assert type(resource.unmet_demand_to_amount['Resource 3']) == Relation.ReverseBinary

    def test_update_based_on_component_functionality(self, resource: Resource.ConcreteResource):
        resource.set_functionality_to_amount_relation('Constant')
        resource.update_based_on_component_functionality(0.0)
        assert resource.current_amount == 5.0
        assert resource.initial_amount == 5.0

        resource.set_functionality_to_amount_relation('Linear')
        resource.update_based_on_component_functionality(0.5)
        assert resource.current_amount == 2.5
        assert resource.initial_amount == 5.0

        resource.set_functionality_to_amount_relation('Binary')
        resource.update_based_on_component_functionality(0.5)
        assert resource.current_amount == 0.0
        assert resource.initial_amount == 5.0

    def test_update_based_on_component_functionality_wrong_input(self, resource: Resource.ConcreteResource):
        resource.set_functionality_to_amount_relation('Binary')
        with pytest.raises(ValueError):
            resource.update_based_on_component_functionality(-5)

    def test_update_based_on_unmet_demand(self, resource: Resource.ConcreteResource):
        resource.set_unmet_demand_to_amount_relations(self.UNMET_DEMAND_PARAMETERS)

        resource.update_based_on_unmet_demand('Resource 3', 0.0)
        assert resource.current_amount == 5.0
        assert resource.initial_amount == 5.0

        resource.update_based_on_unmet_demand('Resource 2', 0.0)
        assert resource.current_amount == 0.0
        assert resource.initial_amount == 5.0      

        resource.set_unmet_demand_to_amount_relations({
                    "Resource 2": 'ReverseLinear',
                    "Resource 3": "Linear"
                })
        resource.set_current_amount(5.0)
        resource.update_based_on_unmet_demand('Resource 2', 0.1)
        assert resource.current_amount == 4.5
        assert resource.initial_amount == 5.0

        resource.update_based_on_unmet_demand('Resource 3', 0.9)
        assert resource.current_amount == 4.5
        assert resource.initial_amount == 5.0
   
        resource.update_based_on_unmet_demand('Resource 3', 0.1)
        assert resource.current_amount == 0.5
        assert resource.initial_amount == 5.0

class TestConsumableResource():

    NAME = 'Resource 1'

    PARAMETERS = {"Amount": 5,
                "ResourceClassName": "ConsumableResource",
                "FunctionalityToAmountRelation": "Linear"}

    @pytest.fixture
    def resource(self):
        return Resource.ConsumableResource(self.NAME, self.PARAMETERS)

    def test_update_supply_based_on_consumption(self, resource: Resource.ConsumableResource):
        resource.update_supply_based_on_consumption(0)
        assert resource.current_amount == 5.0
        assert resource.initial_amount == 5.0

        resource.update_supply_based_on_consumption(0.5)
        assert resource.current_amount == 4.5
        assert resource.initial_amount == 5.0

        resource.update_supply_based_on_consumption(5.0)
        assert resource.current_amount == 0.0
        assert resource.initial_amount == 5.0

    def test_update_based_on_component_functionality(self, resource: Resource.ConsumableResource):
        resource.update_based_on_component_functionality(0.0)
        assert resource.current_amount == 5.0
        assert resource.initial_amount == 5.0

        resource.update_based_on_component_functionality(0.5)
        assert resource.current_amount == 5.0
        assert resource.initial_amount == 5.0

class TestTimeStepsOfAutonomyResource():

    NAME = 'Resource 1'

    PARAMETERS = {"Amount": 5,
                "ResourceClassName": "ConsumableResource",
                "FunctionalityToAmountRelation": "Linear"}
    
    UNMET_DEMAND_PARAMETERS = {
                    "Resource 2": "Binary",
                    "Resource 3": "ReverseBinary"
                }
    
    @pytest.fixture
    def resource(self):
        return Resource.TimeStepsOfAutonomyResource(self.NAME, self.PARAMETERS)
    
    def test_update_based_on_component_functionality(self, resource: Resource.TimeStepsOfAutonomyResource):
        resource.update_based_on_component_functionality(0.0)
        assert resource.current_amount == 5.0
        assert resource.initial_amount == 5.0

        resource.update_based_on_component_functionality(0.5)
        assert resource.current_amount == 5.0
        assert resource.initial_amount == 5.0

    def test_update_based_on_unmet_demand(self, resource: Resource.TimeStepsOfAutonomyResource):
        resource.set_unmet_demand_to_amount_relations(self.UNMET_DEMAND_PARAMETERS)
        resource.update_based_on_unmet_demand('Resource 2', 0.0)
        assert resource.current_amount == 5.0
        assert resource.initial_amount == 5.0

        resource.update_based_on_unmet_demand('Resource 2', 0.5)
        assert resource.current_amount == 5.0
        assert resource.initial_amount == 5.0

    def test_update_supply_based_on_consumption(self, resource: Resource.TimeStepsOfAutonomyResource):
        resource.update_supply_based_on_consumption(0)
        assert resource.current_amount == 4.0
        assert resource.initial_amount == 5.0

        resource.update_supply_based_on_consumption(0.5)
        assert resource.current_amount == 3.0
        assert resource.initial_amount == 5.0

        resource.update_supply_based_on_consumption(-5)
        assert resource.current_amount == 2.0
        assert resource.initial_amount == 5.0

        resource.update_supply_based_on_consumption(5)
        assert resource.current_amount == 1.0
        assert resource.initial_amount == 5.0

        resource.update_supply_based_on_consumption(0)
        assert resource.current_amount == 0.0
        assert resource.initial_amount == 5.0

        resource.update_supply_based_on_consumption(10)
        assert resource.current_amount == 0.0
        assert resource.initial_amount == 5.0

class TestMinMaxConstrainedResource():

    NAME = 'Resource 1'

    PARAMETERS = {
                "Amount": 5,
                "MinMaxConstraints": {
                    "Min": 3,
                    "Max": 1000
                },
                "ResourceClassName": "MinMaxConstrainedResource",
                "FunctionalityToAmountRelation": "Linear"}
    
    UNMET_DEMAND_PARAMETERS = {
                    "Resource 2": "Binary",
                    "Resource 3": "ReverseBinary"
                }
    
    @pytest.fixture
    def resource(self):
        return Resource.MinMaxConstrainedResource(self.NAME, self.PARAMETERS)
    
    def test_set_min_max_constraints(self, resource: Resource.MinMaxConstrainedResource):
        assert resource.min_constraint == 3
        assert resource.max_constraint == 1000

        resource.set_min_max_constraints({"Min": 0, "Max": 10})
        assert resource.min_constraint == 0
        assert resource.max_constraint == 10

        resource.set_min_max_constraints({"Min": 5})
        assert resource.min_constraint == 5
        assert resource.max_constraint == float('inf')

        resource.set_min_max_constraints({"Max": 50})
        assert resource.min_constraint == 0
        assert resource.max_constraint == 50

        resource.set_min_max_constraints({})
        assert resource.min_constraint == 0
        assert resource.max_constraint == float('inf')
    
    def test_update_based_on_component_functionality(self, resource: Resource.MinMaxConstrainedResource):
        resource.update_based_on_component_functionality(0.0)
        assert resource.current_amount == 5.0
        assert resource.initial_amount == 5.0

        resource.update_based_on_component_functionality(0.5)
        assert resource.current_amount == 5.0
        assert resource.initial_amount == 5.0

    def test_update_based_on_unmet_demand(self, resource: Resource.MinMaxConstrainedResource):
        resource.set_unmet_demand_to_amount_relations(self.UNMET_DEMAND_PARAMETERS)
        resource.update_based_on_unmet_demand('Resource 2', 0.0)
        assert resource.current_amount == 5.0
        assert resource.initial_amount == 5.0

        resource.update_based_on_unmet_demand('Resource 2', 0.5)
        assert resource.current_amount == 5.0
        assert resource.initial_amount == 5.0

    def test_update_supply_based_on_consumption(self, resource: Resource.MinMaxConstrainedResource):
        resource.update_supply_based_on_consumption(0)
        assert resource.current_amount == 5.0
        assert resource.initial_amount == 5.0

        resource.update_supply_based_on_consumption(0.5)
        assert resource.current_amount == 5.0
        assert resource.initial_amount == 5.0

    def test_set_current_amount(self, resource: Resource.MinMaxConstrainedResource):
        assert resource.initial_amount == 5.0
        assert resource.current_amount == 5.0

        resource.set_current_amount(50.0)
        assert resource.initial_amount == 5.0
        assert resource.current_amount == 50.0

        resource.set_current_amount(1050.0)
        assert resource.initial_amount == 5
        assert resource.current_amount == 1000.0

        resource.set_current_amount(0)
        assert resource.initial_amount == 5
        assert resource.current_amount == 3  
