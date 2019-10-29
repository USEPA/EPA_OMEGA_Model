"""
__main__.py
===========

OMEGA2 top level code

cd usepa_omega2                     # otherwise some relationships don't show up...
pyreverse -o jpg -p usepa_omega2 . -f ALL # makes classes_usepa_omega2.jpg, etc
pyreverse -o jpg .                  # makes classes.jpb, etc

dot -O -Tjpg classes.dot

"""

import os
import usepa_omega2 as o2
from manufacturer import *
import file_eye_oh as fileio
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import itertools
import cProfile

pd.set_option('chained_assignment', 'raise')

output_folder = 'output/'

node_count = 0


def plot_graph(mfr_graph, with_labels=False):
    options = {
        'node_color': 'red',
        'edge_color': 'blue',
        'node_size': 30,
        'width': .5,
    }

    nx.draw(mfr_graph, with_labels=with_labels)

class ComplianceModel:
    def __init__(self, manufacturers_filename, initial_fleet_filename, verbose=False):
        self.initial_year = 2019
        self.compliance_start_year = 2020
        self.compliance_mid_year = 2028
        self.compliance_long_year = 2035
        self.compliance_end_year = 2050

        self.manufacturer = nx.DiGraph()  # WAS manufacturer('')  # so pyreverse can tell what kind of dict
        self.manufacturer = dict()  # dict of manufacturer compliance graphs

        # initialize manufacturers
        self.init_manufacturers(manufacturers_filename, initial_fleet_filename, verbose)

    def init_manufacturers(self, manufacturers_filename, initial_fleet_filename, verbose=False):
        """

        :param manufacturers_filename:
        :param verbose:
        :return:
        """

        # read manufacturer file
        mfr_df = pd.read_csv(manufacturers_filename, index_col='Manufacturer')

        # determine initial year
        self.initial_year = mfr_df['Calendar Year'][0]

        if verbose:
            print('%d manufacturers \n%s\n' % (initial_year, mfr_df.index.values))

        # initialize manufacturers
        for mfr_name in mfr_df.index:
            # instantiate manufacturer graph and create root node
            mfr = Manufacturer(name= mfr_name, calendar_year= self.initial_year)

            mfr_graph = self.manufacturer[mfr_name] = nx.DiGraph()
            mfr_graph.add_node('root')
            mfr_graph.nodes['root']['mfr'] = mfr
            mfr_graph.nodes['root']['year'] = self.initial_year
            mfr_graph.nodes['root']['new_mfr_node_ids_by_year'] = {}
            mfr_graph.nodes['root']['new_mfr_node_ids_by_year'][self.initial_year] = ['root']
            mfr_graph.nodes['root']['node_path'] = ['root']

            # initialize credit history
            for calendar_year in range(self.initial_year-3, self.initial_year+1):
                mfr.credit.add_history(calendar_year, mfr_df.at[mfr_name, '%d credits Mg' % calendar_year])
            # import initial fleet
            mfr.init_fleet(initial_fleet_filename)

    def find_nodes_ids_by_year(self, graph, calendar_year):
        return [node_id for node_id, node_data in graph.nodes(data=True) if node_data['year'] == calendar_year]

    def create_compliance_scenarios(self, mfr_name, mfr_graph, compliance_year, compliance_end_year, mfr_node_ids= [], quickrun= False, target_cost= None, target_emissions_Mg= None):
        if compliance_year < compliance_end_year:

            while mfr_node_ids:
                mfr_node_id = mfr_node_ids.pop()
                mfr = mfr_graph.nodes[mfr_node_id]['mfr']
                production_scenarios_list = []

                for v in mfr.production:
                    base_new_v = copy.copy(v)    # copy last year's vehicle
                    base_new_v.update_vehicle_emissions_targets(compliance_year)   # calculate this year's emissions targets
                    vehicle_powertrain_efficiency_scenarios_set = set() # create a set of powertrain efficiency options for this vehicle

                    if quickrun:
                        vehicle_powertrain_efficiency_scenarios_set.add(base_new_v.powertrain_target_efficiency_norm)  # the comply scenario
                    else:
                        vehicle_powertrain_efficiency_scenarios_set.add(base_new_v.powertrain_efficiency_norm)   # the do-nothing scenario
                        vehicle_powertrain_efficiency_scenarios_set.add(max(base_new_v.powertrain_target_efficiency_norm, base_new_v.powertrain_efficiency_norm))  # the comply or over-comply scenario
                        vehicle_powertrain_efficiency_scenarios_set.add(max(base_new_v.powertrain_target_efficiency_norm, base_new_v.powertrain_efficiency_norm) * 1.15) # the over-comply or more-over-comply scenario

                    unique_powertrain_efficiency_options = list(vehicle_powertrain_efficiency_scenarios_set)
                    new_vehicles = []
                    for o in unique_powertrain_efficiency_options:
                        new_v = copy.copy(base_new_v)
                        new_v.update_powertrain_efficiency_costs_emissions(o)
                        new_vehicles.append(new_v)
                    production_scenarios_list.append(new_vehicles)

                new_mfr_scenarios = []
                # create iterator
                production_iterator = itertools.product(*production_scenarios_list)
                scenario_number = 1
                for production_scenario in production_iterator:
                    # print(production_scenario)
                    # create manufacturer node with new production vehicle combination
                    new_mfr = copy.copy(mfr)
                    new_mfr.calendar_year = compliance_year
                    new_mfr.production = production_scenario
                    # update manufacturer emissions/compliance status
                    new_mfr.calc_manufacturer_emissions_costs_sales()

                    if (not target_cost and not target_emissions_Mg) or ((new_mfr.tech_production_running_cost_delta_dollars <= target_cost * 1.01) and (new_mfr.emissions_achieved_running_tailpipe_co2_Mg <= target_emissions_Mg * 1.015) and (new_mfr.emissions_achieved_tailpipe_co2_Mg <= new_mfr.emissions_target_net_co2_Mg * 1.175)):
                        # and add to graph
                        new_mfr_node_id = '%s_%d_%d' % (mfr_node_id, compliance_year, scenario_number)
                        # print(new_mfr_node_id)
                        mfr_graph.add_node(new_mfr_node_id)
                        mfr_graph.nodes[new_mfr_node_id]['node_path'] = mfr_graph.nodes[mfr_node_id]['node_path'] + [new_mfr_node_id]
                        mfr_graph.nodes[new_mfr_node_id]['year'] = compliance_year
                        mfr_graph.nodes[new_mfr_node_id]['mfr'] = new_mfr
                        mfr_graph.add_edge(mfr_node_id, new_mfr_node_id)
                        if compliance_year in mfr_graph.nodes['root']['new_mfr_node_ids_by_year']:
                            mfr_graph.nodes['root']['new_mfr_node_ids_by_year'][compliance_year].append(new_mfr_node_id)
                        else:
                            mfr_graph.nodes['root']['new_mfr_node_ids_by_year'][compliance_year] = [new_mfr_node_id]
                        # global node_count
                        # node_count = node_count + 1
                        # print(node_count)
                    # else:
                        # print('Dropping Expensive Node')
                        # new_mfr = None

                    scenario_number = scenario_number + 1

                # plt.close('all')
                # layout = nx.nx_agraph.graphviz_layout(mfr_graph, prog='dot')
                # nx.draw(mfr_graph, pos=layout) # with_labels=True
                # plt.savefig(output_folder + 'mfr_graph_' + mfr_name + '_' + str(compliance_year) + '.png')

                if mfr_graph.nodes['root']['new_mfr_node_ids_by_year'][compliance_year]:
                    self.create_compliance_scenarios(mfr_name, mfr_graph, compliance_year + 1, compliance_end_year, mfr_node_ids = mfr_graph.nodes['root']['new_mfr_node_ids_by_year'][compliance_year], quickrun=quickrun, target_cost= target_cost, target_emissions_Mg= target_emissions_Mg)
        else:
            return

    def run_compliance(self):
        """

        :return:
        """
        print('\nStarting Near Term Compliance...')
        for mfr_name in self.manufacturer:
            print(mfr_name + ' Starting Pass 1...')
            self.create_compliance_scenarios(mfr_name, self.manufacturer[mfr_name], self.compliance_start_year, self.compliance_mid_year, mfr_node_ids=['root'], quickrun=True)
            target_year_node = cm.find_nodes_ids_by_year(cm.manufacturer[mfr_name], self.compliance_mid_year - 1)[0]
            target_cost = cm.manufacturer[mfr_name].nodes[target_year_node]['mfr'].tech_production_running_cost_delta_dollars
            target_emissions_Mg = cm.manufacturer[mfr_name].nodes[target_year_node]['mfr'].emissions_achieved_running_tailpipe_co2_Mg
            print('Target Cost to %d = %f' % (self.compliance_mid_year - 1, target_cost))

            print(mfr_name + ' Starting Pass 2...')
            self.create_compliance_scenarios(mfr_name, self.manufacturer[mfr_name], self.compliance_start_year, self.compliance_mid_year, mfr_node_ids=['root'], quickrun=False, target_cost= target_cost, target_emissions_Mg= target_emissions_Mg)
            print(mfr_name + ' Complete...\n')

        print('Aggregating Manufacturer Production...')
        # aggregate manufacturer fleets into subcategories
        # for mfr_name in self.manufacturer:
        #    mfr_name.midterm_aggregate()

        print('Starting Mid Term Compliance...')
        for mfr_name in self.manufacturer:
            for compliance_year in range(self.compliance_mid_year, self.compliance_long_year):
                print('%s %d' % (mfr_name, compliance_year))
            print('')

        print('Aggregating Manufacturers...')
        # aggregate manufacturers into single fleet
        # self.longterm_aggregate()
        print('Starting Long Term Compliance...')
        for compliance_year in range(self.compliance_long_year, self.compliance_end_year + 1):
            print('%s %d' % ('USAMOTORS', compliance_year))


import time
if __name__ == "__main__":

    print('OMEGA2 greeets you, version %s' % o2.__version__)
    print('from %s with love' % o2.get_filenameext(os.path.abspath(__file__)))

    fileio.validate_folder(output_folder)

    cm = ComplianceModel('manufacturers_initial.csv', 'fleet_initial.csv')

    # mfr_Datsun = cm.manufacturer['Datsun'].nodes['root']['mfr']
    # mfr_Datsun_deepcopy = copy.deepcopy(mfr_Datsun)
    # mfr_Datsun_copy = copy.copy(mfr_Datsun)

    start = time.time()
    cm.run_compliance()
    # cProfile.run('cm.run_compliance()')
    end = time.time()
    # print('Run time %f, %f per node' % (end-start, (end-start)/node_count))
    print('Run time %f' % (end-start))

    # # M = cm.manufacturer['Datsun'].nodes['root']['mfr']
    # # print(M)
    # #
    # # v0_2019 = cm.manufacturer['Datsun'].nodes['root']['mfr'].production[0]
    # # v0_2020 = cm.manufacturer['Datsun'].nodes['root']['mfr'].production[0]
    # #
    # # v0_2020.update_powertrain_efficiency_costs_emissions(max(v0_2020.powertrain_efficiency_norm ,v0_2020.powertrain_target_efficiency_norm))
    # # # print(cm.manufacturer['Datsun'].nodes['root']['mfr'].production[2019][0])
    # # # print(cm.manufacturer['Datsun'].nodes['root']['mfr'].production[2019][1])
    # # # print(cm.manufacturer['Subaru'].nodes['root']['mfr'].production[2019][0])
    # # # print(cm.manufacturer['Subaru'].nodes['root']['mfr'].production[2019][1])
    # # # nx.draw(cm.manufacturer['Datsun'], with_labels=True)
    #
    target_year = cm.compliance_mid_year - 1
    do_plots = True

    for mfr_name in cm.manufacturer:
        target_year_nodes = cm.find_nodes_ids_by_year(cm.manufacturer[mfr_name], target_year)
        print(len(target_year_nodes))

        costs = [cm.manufacturer[mfr_name].nodes[n]['mfr'].tech_production_running_cost_delta_dollars for n in target_year_nodes]
        credits = [cm.manufacturer[mfr_name].nodes[n]['mfr'].emissions_credits_running_tailpipe_co2_Mg for n in target_year_nodes]
        winning_node_ids = [n for n in target_year_nodes]

        print('%d %s target year nodes' % (len(winning_node_ids), mfr_name))
        # print(winning_node_ids)
        if do_plots:
            plt.figure()
            plt.title(mfr_name + ' tech_production_cost_delta_dollars Versus emissions_credits_tailpipe_co2_Mg\n')
            plt.plot(credits, costs, '.')
            plt.xlabel('Credits (Mg)')
            plt.ylabel('Costs ($)')
            plt.grid()
            plt.savefig(output_folder + 'mfr ' + mfr_name + 'credits versus compliance costs.png')

    for mfr_name in cm.manufacturer:
        target_year_nodes = cm.find_nodes_ids_by_year(cm.manufacturer[mfr_name], target_year)
        print(len(target_year_nodes))

        costs = [cm.manufacturer[mfr_name].nodes[n]['mfr'].tech_production_running_cost_delta_dollars for n in target_year_nodes if cm.manufacturer[mfr_name].nodes[n]['mfr'].emissions_credits_running_tailpipe_co2_Mg > 0]
        credits = [cm.manufacturer[mfr_name].nodes[n]['mfr'].emissions_credits_running_tailpipe_co2_Mg for n in target_year_nodes if cm.manufacturer[mfr_name].nodes[n]['mfr'].emissions_credits_running_tailpipe_co2_Mg > 0]
        winning_node_ids = [n for n in target_year_nodes if cm.manufacturer[mfr_name].nodes[n]['mfr'].emissions_credits_running_tailpipe_co2_Mg > 0]

        print('%d %s compliant nodes' % (len(winning_node_ids), mfr_name))
        # print(winning_node_ids)
        if do_plots:
            plt.figure()
            plt.title(mfr_name + ' tech_production_cost_delta_dollars Versus emissions_credits_tailpipe_co2_Mg\n')
            plt.plot(credits, costs, '.')
            plt.xlabel('Credits (Mg)')
            plt.ylabel('Costs ($)')
            plt.grid()
            plt.savefig(output_folder + 'mfr ' + mfr_name + 'credits versus compliance costs.png')

        costs_copy = copy.copy(costs)

        min_cost = min(costs)
        print(mfr_name + ' min cost = %f' % min_cost)

        num_winners = 1
        # get indexes of 5 best scenarios
        pts = [costs.index(costs_copy.pop(costs_copy.index(min(costs_copy)))) for i in range(0,num_winners)]

        if do_plots:
            fig1 = plt.figure()
            ax1 = plt.gca()
            ax1.set_title(mfr_name + ' Target and Achieved Emissions v. Year\n' + winning_node_ids[pts[0]])
            ax1.grid()
            ax1.set_xlabel('Year')
            ax1.set_ylabel('Emissions (Mg)')

            fig2 = plt.figure()
            ax2 = plt.gca()
            ax2.set_xlabel('Year')
            ax2.set_ylabel('Cumulative Credits (Mg)')
            ax2.set_title(mfr_name + ' Cumulative Credits v. Year\n' + winning_node_ids[pts[0]])
            ax2.grid()

        for i in pts:
            # print(credits[i])
            # print(costs[i])
            # print(winning_node_ids[i])

            node_path = cm.manufacturer[mfr_name].nodes[winning_node_ids[i]]['node_path']

            print(node_path)

            # reconstruct history from node path:
            emissions_target_net_co2_Mg = {}
            emissions_achieved_tailpipe_co2_Mg = {}
            emissions_credits_running_tailpipe_co2_Mg = {}
            for node_id in node_path:
                year = cm.manufacturer[mfr_name].nodes[node_id]['mfr'].calendar_year
                emissions_target_net_co2_Mg[year] = cm.manufacturer[mfr_name].nodes[node_id]['mfr'].emissions_target_net_co2_Mg
                emissions_achieved_tailpipe_co2_Mg[year] = cm.manufacturer[mfr_name].nodes[node_id]['mfr'].emissions_achieved_tailpipe_co2_Mg
                emissions_credits_running_tailpipe_co2_Mg[year] = cm.manufacturer[mfr_name].nodes[node_id]['mfr'].emissions_credits_running_tailpipe_co2_Mg

            if do_plots:
                # best_final_scenario = cm.manufacturer[mfr_name].nodes[winning_node_ids[i]]['mfr']
                ax1.plot(list(emissions_target_net_co2_Mg.keys()),
                         list(emissions_target_net_co2_Mg.values()), 'b')
                ax1.plot(list(emissions_target_net_co2_Mg.keys()),
                         np.array(list(emissions_target_net_co2_Mg.values())) * 1.1, 'r--')
                ax1.plot(list(emissions_target_net_co2_Mg.keys()),
                         np.array(list(emissions_target_net_co2_Mg.values())) * 1.15, 'm--')
                ax1.plot(list(emissions_target_net_co2_Mg.keys()),
                         np.array(list(emissions_target_net_co2_Mg.values())) * 1.20, 'y--')
                # print(best_final_scenario)
                # print(best_final_scenario.production[target_year][0])
                # print(best_final_scenario.production[target_year][1])

                ax1.plot(list(emissions_achieved_tailpipe_co2_Mg.keys()), list(emissions_achieved_tailpipe_co2_Mg.values()))

                ax2.plot(list(emissions_credits_running_tailpipe_co2_Mg.keys()), list(emissions_credits_running_tailpipe_co2_Mg.values()))

        if do_plots:
            fig1.savefig(output_folder + 'mfr top ' + str(num_winners) + ' ' + mfr_name + ' ' + winning_node_ids[i] + ' target and achieved emissions.png')
            fig2.savefig(output_folder + 'mfr top ' + str(num_winners) + ' ' + mfr_name + ' ' + winning_node_ids[i] + ' cumulative credits.png')