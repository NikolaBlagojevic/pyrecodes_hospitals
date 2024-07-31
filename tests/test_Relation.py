import pytest
from pyrecodes_hospitals import Relation
import math


class TestRelation():
    test_values = [0.0, 0.3, 0.5, 0.8, 1.0]

    def construct_relation_object(self, relation_name: str):
        target_relation = getattr(Relation, relation_name)
        self.relation = target_relation()

    def test_linear_relation(self):
        self.construct_relation_object('Linear')
        output = []
        correct_output = [0.0, 0.3, 0.5, 0.8, 1.0]
        for value in self.test_values:
            output.append(self.relation.get_output(value))
        assert output == correct_output

    def test_reverse_linear_relation(self):
        self.construct_relation_object('ReverseLinear')
        output = []
        correct_output = [1.0, 0.7, 0.5, 0.2, 0.0]
        for value in self.test_values:
            output.append(self.relation.get_output(value))
        assert all([math.isclose(a, b) for a, b in zip(output, correct_output)])

    def test_binary_relation(self):
        self.construct_relation_object('Binary')
        output = []
        correct_output = [0.0, 0.0, 0.0, 0.0, 1.0]
        for value in self.test_values:
            output.append(self.relation.get_output(value))
        assert all([math.isclose(a, b) for a, b in zip(output, correct_output)])

    def test_reverse_binary_relation(self):
        self.construct_relation_object('ReverseBinary')
        output = []
        correct_output = [1.0, 0.0, 0.0, 0.0, 0.0]
        for value in self.test_values:
            output.append(self.relation.get_output(value))
        assert all([math.isclose(a, b) for a, b in zip(output, correct_output)])

    def test_constant_relation(self):
        self.construct_relation_object('Constant')
        output = []
        correct_output = [1.0, 1.0, 1.0, 1.0, 1.0]
        for value in self.test_values:
            output.append(self.relation.get_output(value))
        assert all([math.isclose(a, b) for a, b in zip(output, correct_output)])

    def test_invalid_negative_input(self):
        self.construct_relation_object('Linear')
        with pytest.raises(ValueError):
            self.relation.get_output(-0.5)

    def test_invalid_high_input(self):
        self.construct_relation_object('Linear')
        with pytest.raises(ValueError):
            self.relation.get_output(50)
