import matplotlib.pyplot as plt
import matplotlib.ticker
from pyrecodes_hospitals import Component


class Plotter():
    GANTT_BAR_DISTANCE = 10
    GANTT_BAR_WIDTH = 5
    LOR_ALPHA = 0.2
    ALL_RECOVERY_ACTIVITIES_COLORS = {'RapidInspection': 'lightblue',
                                      'Financing': 'orange',
                                      'ContractorMobilization': 'springgreen',
                                      'SitePreparation': 'purple',
                                      'CleanUp': 'yellow',
                                      'DetailedInspection': 'tomato',
                                      'ArchAndEngDesign': 'pink',
                                      'Permitting': 'darkblue',
                                      'Demolition': 'gray',
                                      'Repair': 'red',
                                      'Functional': 'green'}

    def setup_lor_plot_fig(self, x_axis_label: str, y_axis_label: str) -> plt.axis:
        plt.figure()
        plt.xlabel(x_axis_label)
        plt.ylabel(y_axis_label)
        plt.grid(True)
        return plt.gca()

    def plot_single_resource(self, time_steps: list, supply: list, demand: list, consumption: list,
                             axis_object: plt.axis, warmup=0, show=False, supply_label='Supply', demand_label='Demand',
                             consumption_label='Consumption'):
        [supply, demand, consumption] = self.add_warmup(warmup, [supply, demand, consumption])
        axis_object.plot(time_steps, supply, label=supply_label)
        axis_object.plot(time_steps, demand, label=demand_label)
        axis_object.fill_between(time_steps, demand, consumption,
                         label='Unmet Demand', alpha=self.LOR_ALPHA)
        axis_object.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=3)
        axis_object.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
        if show:
            plt.show()

    def save_current_figure(self, savename='Figure.png', dpi=300):        
        plt.gca()
        plt.savefig(savename, dpi=dpi)
    
    def add_warmup(self, warmup: int, lists_to_extend: list([list])):
        extended_lists = []
        for list_to_extend in lists_to_extend:
            extended_lists.append([list_to_extend[0]] * warmup + list_to_extend)
        return extended_lists       

    def setup_gantt_chart_fig(self, x_axis_label: str, components: list) -> plt.axis:
        plt.figure()
        plt.xlabel(x_axis_label)
        axis_object = plt.gca()
        axis_object.set_yticks([i * self.GANTT_BAR_DISTANCE for i in range(len(components))])
        axis_object.set_yticklabels([component.__str__() for component in components])
        plt.grid(True)
        return axis_object

    def plot_gantt_chart(self, components: list([Component.Component]), axis_object: plt.axis):

        for component_row, component in enumerate(components):
            self.plot_component_gantt_bar(component_row, component, axis_object)

        plt.show()

    def plot_component_gantt_bar(self, component_row: int, component: Component.Component, axis_object: plt.axis):

        Y_position = component_row * self.GANTT_BAR_DISTANCE - self.GANTT_BAR_WIDTH
        for recovery_activity_name, recovery_activity_object in component.recovery_model.recovery_activities.items():
            duration = len(recovery_activity_object.time_steps)
            if duration > 0:
                start = recovery_activity_object.time_steps[0]
                axis_object.broken_barh([(start, duration)], (Y_position, self.GANTT_BAR_WIDTH),
                                        facecolors=self.ALL_RECOVERY_ACTIVITIES_COLORS[recovery_activity_name],
                                        edgecolor="none")
    
    def plot_dead_patients_over_time(self, time_steps: list, dead_patients: dict, patient_type: str, axis_object: plt.axis, warmup=0):
        patients_to_plot = dead_patients[patient_type]
        [dead_patients] = self.add_warmup(warmup, [patients_to_plot])
        axis_object.plot(time_steps, dead_patients, label=f'Dead {patient_type}')
        axis_object.legend(loc='lower right')
        plt.show()
