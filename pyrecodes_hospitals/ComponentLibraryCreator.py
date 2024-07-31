import json
from abc import ABC, abstractmethod
from pyrecodes_hospitals import Component


class ComponentLibraryCreator(ABC):
    """
    Abstract class for creating component library used to construct the System components.
    """

    library: dict

    @abstractmethod
    def form_library(self) -> dict:
        pass


class JSONComponentLibraryCreator(ComponentLibraryCreator):
    """
    Creating a component library from a single JSON file containing blueprints for each component type. 
    """

    library: dict

    def __init__(self, file_name: str) -> None:
        self.file = None
        self.read_library_file(file_name)

    def read_library_file(self, file_name: str) -> None:
        with open(file_name, 'r') as file:
            self.file = json.load(file)

    def form_library(self) -> dict:
        component_library = dict()
        for component_name, component_params in self.file.items():
            component_library[component_name] = self.form_component(component_name, component_params)
        return component_library

    def form_component(self, component_name: str, component_parameters: dict) -> Component.Component:
        target_object = getattr(Component, component_parameters['ComponentClass'])
        component = target_object()
        component.form(component_name, component_parameters)     
        return component

