"""
sales_effect.py

"""

class SalesEffect:
    def __init__(self, wtp_factor, fuel_price, context_vehicle_price, new_vehicle_price, context_mpg, new_mpg, elasticity):
        """

        :param wtp_factor: The consumer willingness to pay for fuel economy expressed in dollars per cents/mile of operating costs.
        :param fuel_price: The consumer-in-the-showroom fuel price, not necessarily the actual fuel price for a given year.
        :param context_vehicle_price: The context vehicle price for the given year.
        :param new_vehicle_price: The new vehicle price (due to the action) for the given year.
        :param context_mpg: The context vehicle fuel economy.
        :param new_mpg: The new vehicle fuel economy.
        :param elasticity: Elasticity of sales in response to price changes.
        """
        self.wtp_factor = wtp_factor
        self.fuel_price = fuel_price
        self.context_vehicle_price = context_vehicle_price
        self.new_vehicle_price = new_vehicle_price
        self.context_mpg = context_mpg
        self.new_mpg = new_mpg
        self.elasticity = elasticity

    def cost_per_mile(self, mpg):
        """

        :param mpg: The vehicle fuel economy.
        :return: The consumer-in-the-showroom cost per mile.
        """
        return self.fuel_price / mpg

    def wtp(self, mpg):
        """

        :param mpg: The vehicle fuel economy.
        :return: The consumer willingness to pay for the fuel economy of the given vehicle.
        """
        return self.wtp_factor * self.cost_per_mile(mpg)

    def value_of_vehicle_attributes(self, veh_price, mpg):
        """

        :param veh_price: Vehicle price.
        :param mpg: Vehicle fuel economy.
        :return: The value of vehicle attributes other than fuel economy.
        """
        return veh_price - self.wtp(mpg)

    def cost_of_meeting_standards(self):
        """

        :return: The marginal cost of the standards in the given action.
        """
        return self.new_vehicle_price - self.context_vehicle_price

    def generalized_cost_of_new_vehicle(self):
        """

        :return:
        """
        return self.value_of_vehicle_attributes(self.context_vehicle_price, self.context_mpg) \
               + self.wtp(self.new_mpg) \
               + self.cost_of_meeting_standards()

    def change_in_sales(self):
        """

        :return:
        """
        return self.elasticity * (self.generalized_cost_of_new_vehicle() - self.context_vehicle_price) / self.context_vehicle_price

    def percent_change_in_sales(self):
        """

        :return:
        """
        return 100 * self.change_in_sales()


if __name__ == '__main__':
    wtp_factor = 1057
    fuel_price = 3
    context_veh_price = 30000
    new_veh_price = 32000
    context_mpg = 30
    new_mpg = 40
    elasticity = -.01

    percent_change_obj = SalesEffect(wtp_factor, fuel_price, context_veh_price, new_veh_price, context_mpg, new_mpg, elasticity)
    print('\ncost per mile, context:  ', percent_change_obj.cost_per_mile(context_mpg))
    print('cost per mile, new:  ', percent_change_obj.cost_per_mile(new_mpg))
    print('\nWTP, context:  ', percent_change_obj.wtp(context_mpg))
    print('WTP, new:  ', percent_change_obj.wtp(new_mpg))
    print('\nValue of vehicle attributes, context:  ', percent_change_obj.value_of_vehicle_attributes(context_veh_price, context_mpg))
    print('Value of vehicle attributes, new:  ', percent_change_obj.value_of_vehicle_attributes(new_veh_price, new_mpg))
    print('\nCost of meeting standards, new:  ', percent_change_obj.cost_of_meeting_standards())
    print('Generalized cost of vehicle, new:  ', percent_change_obj.generalized_cost_of_new_vehicle())
    print('\nChange in sales:  ', percent_change_obj.change_in_sales())
    print('Percent change in sales:  ', f'{percent_change_obj.percent_change_in_sales()}%')
