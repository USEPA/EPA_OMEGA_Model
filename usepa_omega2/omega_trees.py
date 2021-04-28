"""

omega_tree.py
=============

Routines and data structures for compliance-tree algorithms

"""
import math

from omega2 import *


class OMEGATree(OMEGABase):
    """
        data stucture to hold tree top-level info
    """

    def __init__(self, root_omeganode):
        self.root = root_omeganode
        self.best_path_cost = None


class OMEGANode(OMEGABase):
    """
        data structure to hold OMEGATree node info
    """

    def __init__(self, parent_name, name, ghg_credit_bank, vehicle_list, path_cost):
        self.parent_name = parent_name
        self.name = name
        self.ghg_credit_bank = ghg_credit_bank
        self.vehicle_list = vehicle_list
        self.path_cost = path_cost
        # self.stock = None     # do we need to track the entire stock as well?  Or only if PMT affects sales?


class WeightedNode(OMEGABase):
    import math

    def __init__(self, weight):
        self.weight = weight
        self.value = None

    @property
    def weighted_value(self):
        return self.weight * self.value

    @property
    def identifier(self):
        id_str = ''
        try:
            wv = self.weighted_value
            id_str = '%s * %s = %s' % (self.weight, self.value, wv)
        except:
            id_str = '%s' % self.weight
        finally:
            return id_str


class WeightedTree(OMEGABase):
    def __init__(self, tree_df, verbose=False):
        from treelib import Node, Tree
        self.tree = Tree()

        for i, c in enumerate(tree_df.columns):
            if '->' in c:
                parent_name, child_name = c.split('->')
                if not self.tree:  # if tree is empty, create root
                    self.tree.create_node(identifier=parent_name, data=WeightedNode(1.0))
                self.tree.create_node(identifier=child_name, parent=parent_name, data=WeightedNode(tree_df[c].item()))

        if verbose:
            self.tree.show(idhidden=False, data_property='weight')

    def leaves(self):
        return self.tree.leaves()

    def validate_weights(self):
        tree_errors = []

        # validate note weights
        for node_id in self.tree.expand_tree(mode=self.tree.DEPTH):
            child_node_weights = [c.data.weight for c in self.tree.children(node_id)]
            if child_node_weights:
                if sum(child_node_weights) != 1.0:
                    tree_errors.append('weight error at %s' % node_id)

        return tree_errors

    @staticmethod
    def calculate_node_weighted_value(tree, node_id):
        if not tree.children(node_id):
            try:
                return tree.get_node(node_id).data.weighted_value
            except:
                raise Exception(
                    '*** Missing drive cycle "%s" in input to WeightedTree.calculate_node_weighted_value() ***' %
                    node_id)
        else:
            n = tree.get_node(node_id)
            n.data.value = 0
            for child in tree.children(node_id):
                n.data.value += WeightedTree.calculate_node_weighted_value(tree, child.identifier)
            return n.data.weighted_value

    def calculate_weighted_value(self, values_dict, node_id=None, weighted=False):
        # clear all values
        for n in self.tree.nodes:
            self.tree.get_node(n).data.value = None

        # assign values to leaves
        for key, value in values_dict.items():
            if key in self.tree:
                self.tree.get_node(key).data.value = value

        # traverse tree and calculate node values
        if node_id is None:
            node_id = self.tree.root

        WeightedTree.calculate_node_weighted_value(self.tree, node_id)

        if weighted:
            return self.tree.get_node(node_id).data.weighted_value
        else:
            return self.tree.get_node(node_id).data.value

    def show(self):
        self.tree.show(idhidden=False, data_property='identifier')
