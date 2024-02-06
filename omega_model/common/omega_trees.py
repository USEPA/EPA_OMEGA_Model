"""

**Routines and data structures for tree-based algorithms and functions.**

----

**CODE**

"""

from omega_model import *


class _OMEGATree(OMEGABase):
    """
    Data stucture to hold tree top-level info

    """
    def __init__(self, root_omeganode):
        self.root = root_omeganode
        self.best_path_cost = None


class _OMEGANode(OMEGABase):
    """
    Data structure to hold OMEGATree node info

    """

    def __init__(self, parent_name, name, ghg_credit_bank, vehicle_list, path_cost):
        self.parent_name = parent_name
        self.name = name
        self.ghg_credit_bank = ghg_credit_bank
        self.vehicle_list = vehicle_list
        self.path_cost = path_cost
        # self.stock = None     # do we need to track the entire stock as well?  Or only if PMT affects sales?


class WeightedNode(OMEGABase):
    """
    Implements nodes in a tree where nodes have weights and values.
    Used for drive cycle weighting, but could also be used for weighting in general, if needed.
    ``WeightedNodes`` are stored as node *data* in a ``WeightedTree.tree`` (see below), which is a ``treelib.Tree``.

    """
    def __init__(self, weight):
        """
        Create WeightedNode

        Args:
            weight (numeric): node weight

        """
        self.weight = weight
        self.value = None

    @property
    def weighted_value(self):
        """
        Calculate node weighted value.

        Returns:
            Node weight times node value if weight is not ``None``, else returns 0.

        """
        value = 0

        if self.weight:
            value = self.weight * self.value

        return value

    @property
    def identifier(self):
        """
        Generate a node ID string.

        Returns:
            Node ID string.

        """
        id_str = ''
        try:
            wv = self.weighted_value
            id_str = '%s * %s = %s' % (self.weight, self.value, wv)
        except:
            id_str = '%s' % self.weight
        finally:
            return id_str


class WeightedTree(OMEGABase):
    """
    Implements a tree data structure of ``WeightedNodes`` and methods of querying node values.

    """
    def __init__(self, tree_df, verbose=False):
        """
        Create WeightedTree from a dataframe containing node connections as column headers and weights as row
        values.

        Args:
            tree_df (DataFrame): a dataframe with column headers such as ``'A->B', 'A->C', 'B->D'`` etc.
            verbose (bool): prints the tree to the console if True

        Note:
            The first element of the first column containing an arrow  (``->``) is taken as the root node.
            Parent nodes must be referenced before child nodes, otherwise there is no particular pre-defined order.
            In the above example, B is a child of A before D can be a child of B.

        """
        from treelib import Tree
        self.tree = Tree()

        for i, c in enumerate(tree_df.columns):
            if '->' in c:
                parent_name, child_name = c.split('->')
                if not self.tree:  # if tree is empty, create root
                    self.tree.create_node(identifier=parent_name, data=WeightedNode(1.0))
                node_weight = tree_df[c].item()
                if type(node_weight) is str:
                    node_weight = Eval.eval(node_weight, {'__builtins__': None}, {})
                self.tree.create_node(identifier=child_name, parent=parent_name, data=WeightedNode(node_weight))

        if verbose:
            self.tree.show(idhidden=False, data_property='weight')

    def leaves(self):
        """
        Get list of tree leaves.

        Returns:
            List of tree nodes (type ``treelib.node.Node``) that have no children.

        """
        return self.tree.leaves()

    def validate_weights(self):
        """
        Validated node weights.
        The sum of a parent node's child node weights must equal 1.0.
        Nodes with a weight of ``None`` are ignored during summation.

        Returns:
            List of node weight errors, or empty list on success.

        """
        import sys

        tree_errors = []

        # validate note weights
        for node_id in self.tree.expand_tree(mode=self.tree.DEPTH):
            child_node_weights = [c.data.weight for c in self.tree.children(node_id)]
            if None in child_node_weights:
                child_node_weights.remove(None)
            if any(child_node_weights):
                child_node_weights = [cnw for cnw in child_node_weights if cnw]  # only validate non-None weights
                if abs(1-sum(child_node_weights)) > sys.float_info.epsilon:
                    tree_errors.append('weight error at %s' % node_id)

        return tree_errors

    @staticmethod
    def calc_node_weighted_value(tree, node_id, weighted=True):
        """
        Calculate node weighted value.
        If the node has no children then the weighted value is the node's weighted value, see ``WeightedNode`` above.
        If the node has children then the weighted value is the sum of the weighted values of the children,
        recursively if necessary.

        Args:
            tree (treelib.Tree): the tree to query
            node_id (str): the id of the node to query
            weighted (bool): if ``True`` then return weighted value string, else return node value string

        Returns:
            tuple: (node weighted value, equation string)

        """
        if not tree.children(node_id):
            try:
                if tree.get_node(node_id).data.weight:
                    wv = tree.get_node(node_id).data.weighted_value
                    eq_str = "%.20f * results['%s']" % (tree.get_node(node_id).data.weight, node_id)
                    return wv, eq_str
                else:
                    return 0, '0'
            except:
                raise Exception(
                    '*** Missing drive cycle "%s" in input to WeightedTree.calc_node_weighted_value() ***' %
                    node_id)
        else:
            n = tree.get_node(node_id)
            n.data.value = 0
            if n.data.weight != 1 and n.data.weight is not None and weighted:
                eq_str = '%.20f * (' % n.data.weight
            else:
                eq_str = '('
            for child in tree.children(node_id):
                wv, child_eq_str = WeightedTree.calc_node_weighted_value(tree, child.identifier)
                n.data.value += wv
                eq_str += '%s + ' % child_eq_str
            eq_str = '%s)' % eq_str[0:max(eq_str.rfind(']',), eq_str.rfind(')',))+1]
            return n.data.weighted_value, eq_str

    def calc_value(self, values_dict, node_id=None, weighted=False):
        """
        Assign values to tree leaves then calculate the value or weighted value at the given ``node_id`` or at the root
        if no ``node_id`` is provided.  Previously calculated values are cleared first.

        Args:
            values_dict (dict-like): values to assign to leaves
            node_id (str): node id to calculate weighted value of, or tree root if not provided
            weighted (bool): if True then return weighted value, else return node value

        Returns:
            Node (or tree) value (or weighted value)

        """
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

        eq_str = WeightedTree.calc_node_weighted_value(self.tree, node_id, weighted)[1]

        try:
            return Eval.eval(eq_str, {'results': values_dict}), eq_str
        except:
            print('omega trees exception !!!')

    def show(self):
        """
        Print the tree to the console.

        """
        self.tree.show(idhidden=False, data_property='identifier')


if __name__ == "__main__":
    try:
        pass  # TODO: write module test here
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
