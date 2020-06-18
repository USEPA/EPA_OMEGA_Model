

class FleetMetrics:
    def __init__(self, fleet):
        self.fleet = fleet

    def fleet_class(self, class_name, class_value):
        return_df = self.fleet.loc[(self.fleet[class_name] == class_value) & (self.fleet['Volume'] > 0), :]
        return return_df

    def fleet_metric_weighted(self, metric_to_weight, metric_to_weightby):
        if self.fleet[metric_to_weightby].sum(axis=0) == 0:
            weighted_value = 0
        else:
            weighted_value = self.fleet[[metric_to_weightby, metric_to_weight]].product(axis=1).sum(axis=0) \
                             / self.fleet[metric_to_weightby].sum(axis=0)
        return weighted_value

    def fleet_metric_sum(self, metric_to_sum):
        summed_value = self.fleet[metric_to_sum].sum(axis=0)
        return summed_value

    def fleet_age0(self):
        return_df = self.fleet.loc[(self.fleet['Age'] == 1)]
        return return_df

