.. image:: _static/epa_logo_1.jpg


Model Architecture and Algorithms
=================================

Overview of Model Inputs
^^^^^^^^^^^^^^^^^^^^^^^^
.. todo: [this section should just focus on what type of information is provided by the input files, and not about where the data comes from]

As described in the overview, OMEGA model inputs are grouped into two categories:  1) assumptions about the structure and the stringency of the policies being evaluated within the model (these are the policy alternatives) and 2) external assumptions that apply to all policies under analysis (collectively referred to as the analysis context).  The policy alternatives define the policy being evaluated in each OMEGA run and are described in the Policy Module section.  The analysis context inputs (which include more traditional inputs like fuel prices, technology assumptions, etc) are discussed within the descriptions of the associated modules that use them.

The lists of policy alternatives and analysis context inputs are provided below.  Each input is described in more detail in each of the module descriptions listed later in this section.

Policy Alternatives Inputs:
	* Emissions targets
	* Rules on banking/trading of credits
	* Technology multipliers
	* Reg class definitions
	* VMT assumption
	

Analysis Context Inputs:
	* Vehicle costs
	* Vehicle prices
	* Vehicle energy consumption
	* Off-cycle credit tech values
	* Starting credit balances
	* Fuel Costs (gas and electricity)
	* Vehicle Fleet
	* Vehicle VMT distribution


.. todo: [[add footnote about terminology, that in the implementation, these are called packages]]

Policy Module
^^^^^^^
OMEGA's primary function is to help evaluate and compare policy alternatives. Because the alternatives to be considered may vary widely, and we cannot anticipate all possible policy elements in advance, OMEGA is designed to have the flexibility to model regulatory programs over a range of stringencies and program structures. To the extent possible, the code within the module has been made generic, and the complete definition of a policy must be provided by the user as an input the model. Much like the definitions recorded in the Code of Federal Regulations (CFR), these inputs must unambiguously describe the methodologies for determining vehicle-level emissions targets and certification values, as well as the accounting rules for determining how individual vehicles contribute to a manufacturer's overall compliance determination. 

In this documentation, *policy alternatives* refer only to what is being evaluated in a particular model run. There will also be relevant inputs and assumptions which are technically policies but are assumed to be fixed (i.e. exogenous) for a given comparison of alternatives. Such assumptions are defined by the user in the *analysis context*, and may reflect a combination of local, state, and federal programs that influence the transportation sector through regulatory and market-based mechanisms. .. todo: [[add examples, and links]] A comparison of policy alternatives requires the user to specify a no-action, or baseline policy, and one or more action alternatives. 

Policy alternatives that can be defined within OMEGA fall into two categories: those that involve fleet average emissions standards and rules for the accounting of compliance credits, and those that specify a required share of a specific technology. OMEGA can model either one of these types as an independent alternative, or both together; for example, in the case of a policy which requires a minimum share of a technology while still satisfying fleet averaging requirements.

**Policy Alternatives Involving Fleet Average Emissions Standards:**
In this type of policy, the key principal is that the compliance status of a manufacturer is a result of the combined performance of all of the vehicles, and not the result of every vehicle achieving compliance individually. The policy module's fleet averaging is based on CO2 *credits* as the fungible accounting currency. Each vehicle has an emissions target and an achieved certification emissions value. The difference between the target and certification emissions in absolute terms (Mg CO2) is referred to as a *credit*, and might be a positive or negative value that can be transferred across years, depending on the credit accounting rules defined in the policy. The user-defined policy inputs can be sued to specify restrictions on credit averaging and banking, including limits on credit lifetime or the ability to carry a negative balance into the future. The analogy of a financial bank is useful here, and OMEGA has adopted data structures and names that mirror the familiar bank account balance and transaction logs.
.. todo: [[insert example transaction and balance tables]]

  
OMEGA is designed so that within an analysis year, credits from all the producer’s vehicles are counted without limitations towards the producer's credit bank. This program feature is known as *fleet averaging*, where vehicles with positive credits may contribute to offset other vehicles with negative credits. The OMEGA model calculates overall credits earned in an analysis year as the difference between the aggregate certification emissions minus the aggregate target emissions. An alternative approach of calculating overall credits as the sum of individual vehicle credits might seem more straightforward, and while technically possible, it is not used for several reasons. First, some credits, such as those generated by advanced technology incentive multipliers, are not easily accounted for on a per-vehicle basis. The transfer of credits between producers can be simulated in OMEGA by representing multiple regulated entities as a single producer, under an assumption that there is no cost or limitation to the transfer of compliance credits among entities. OMEGA is not designed to explicitly model any strategic considerations involved with the transfer of credits between producers. Emissions standards are defined in OMEGA using a range of policy elements, including:

* rules for the accounting of upstream emissions
* definition of compliance incentives, like multipliers
* definition of regulatory classes
* definition of attribute-based target function
* definition of the vehicles’ assumed lifetime miles


**Policy Alternatives Requiring Specific Technologies:**

This type of policy requires all, or a portion, of producer’s vehicles to have particular technologies. OMEGA treats these policy requirements as constraints on the producer’s design options. This type of policy alternative input can be defined either separately, or together with an fleet averaging emissions standard; for example, a minimum ZEV share requirement could be combined with an emissions standard where the certification emissions associated with ZEVs are counted towards the producer’s achieved compliance value.

**Policy Representation in the Analysis Context:**

Some policies are not modeled in OMEGA as policy alternatives, either because the policy is not aimed directly at the producer as a regulated entity, or because the particular OMEGA analysis is not attempting to evaluate the impact of that policy relative to other alternatives. Still, it is important that the Analysis Context inputs are able to reflect any policies that might significantly influence the producer or consumer decisions.  Some examples include:

* Fuel tax policy
* State and local ZEV policies
* Vehicle purchase incentives
* Investment in refueling and charging infrastructure
* Accelerated vehicle retirement incentives


Producer Module
^^^^^^^

The modeling of producer decisions is a core function of OMEGA, and is based on minimizing their generalized costs, subject to the constraints of regulatory compliance and consumer demand. The ‘producer’ defined in the OMEGA encompasses both the broader meaning as a supplier of a transportation good or service to the market, and in the narrower sense as the regulated entity subject to EPA policies.

The Producer Module uses exogenous inputs from the analysis context (including xyz) to meet the compliance targets defined in the policy module.   Its outputs of xyz must ultimately reconcile with the outputs from the Consumer module through a series of iterations, described in the Consumer Module section. 

Inputs and Outputs of the Producer Module
------------------------
Policy Alternative inputs are used to calculate a compliance target for the producer, in Mg CO2 for a given analysis year, using the provided attribute-based standards curve, vehicle regulatory class definitions, and assumed VMT for compliance. Other policy inputs may define, for example, the credit lifetime for carry-forward and carry-back, or a floor on the minimum share of ZEV vehicles produced.

Context inputs and assumptions that the Producer Module uses define all factors, apart from the policies under evaluation, that influence the modeled producer decisions. Key factors include the vehicle costs and emissions for the technologies and vehicle attributes considered, and the producer constraints on pricing strategy and cross-subsidization.

Inside the Producer Module
------------------------
OMEGA incorporates our assumption that producers make strategic decisions, looking beyond the immediate present to minimize generalized costs over a longer time horizon. The efficient management of compliance credits from year-to-year, in particular, involves a degree of look-ahead, both in terms of expected changes in regulatory stringency and other policies, and expected changes in generalized costs over time.

The producer’s generalized cost is made up of both the monetary expenses of bringing a product to the consumer, and also the value that the producer expects can be recovered from consumers at the time of purchase. The assumption in OMEGA that producers will attempt to minimize their generalized costs is consistent with a producer goal of profit maximization, subject to any modeling constraints defined in the Consumer Module, such as limiting changes in sales volumes, sales mixes, or select vehicle attributes.


Consumer Module
^^^^^^^
The Consumer Module’s purpose is to estimate how light duty vehicle ownership and use respond to key vehicle characteristics within a given analysis context. An important part of the model is that it allows different endogenous consumer responses to EVs and ICEs. The module estimates total new sales volumes, the EV share of new vehicle demand, used vehicle market responses (including reregistration/scrappage), and the use of both new and used vehicles in the market measured using vehicle miles traveled (VMT).

Then, the Consumer and Producer Modules iterate to achieve convergence on the estimates of new vehicles produced and demanded. Once that convergence is achieved, the Consumer Module outputs total vehicle stock (new and used vehicles and their attributes) and use (VMT) to the Effects Module.

**Inputs to the Consumer Module**
The Consumer Module uses exogenous inputs from the analysis context, and endogenous inputs from the Producer Module. Exogenous inputs include fuel prices, on-road stock assumptions, and demographics, among others. Endogenous inputs include vehicle prices, average vehicle cost, and vehicle attributes, such as fuel consumption rate. The choice of vehicle attributes used in the Consumer Module is led by the method used to estimate the shares of vehicles demanded. The Consumer Module can handle other vehicle characteristics fed in from the Producer Module (PM), such as vehicle class, or EV range if those are needed in new sales or vehicle shares estimates.

**Outputs of the Consumer Module**
The Consumer Module produces two levels of outputs, interim outputs used in iteration with the Producer Module, and final outputs that are sent to the Effects Module. Interim outputs of the Consumer Module, including new vehicle sales and the share of EVs, are fed back to the Producer Module for iteration and convergence. Once that convergence is achieved, the Consumer Module estimates the final outputs that go th effects module, including new vehicle sales broken down by market class, the total stock, and VMT.

Market Classes
------------------------
The Consumer Module estimates new vehicle shares at an aggregate level, with vehicles separated into high level market classes. The choice of the set of market classes is tied to the model used to estimate the shares of new vehicles sold, and are dependant on the attributes available in the input data files. For example, vehicles can be identified by their fuel type (EV vs. ICE) and by their expected use (for example whether the vehicles are expected to primarily haul goods or tow, as a body-on-frame vehicle might, or whether they are expected to primarily be used for passenger transport, as a uni-body vehicle might.
Classes are nonresponsive or responsive and user can define what those are.
Add examples of how you might add additional classes (urban v rural)
What is seen within the demo inputs and demo user defined submodule - hauling/non-hauling/EV/ICE - nonresponsive, responsive
These projected shares can remain unresponsive to policy, or may be estimated within the Consumer Module.
Though the addition of the Consumer Module as a whole is significant update in OMEGA 2.0, the ability to model both EV and ICE vehicle demand and supply separately is a major part as well. Within the Consumer Module
Stock and use have to be defined consistently with market classes
User definaable built submodule is where market classes are determined - user can determine which classes are responsive and not responsive. In the demo, hauling.non-hauling are nonresponsive
1-user definable submodules, here is example, define classes, and designate category is responsive/nonresponsive to account for things like x,y,z... market heterogeneity, etc.

*  The share of light duty vehicles that are classified as hauling and nonhauling is constant. The shares of hauling and non-hauling vehicles comes from the projections published in the Annual Energy Outlook from the U.S. Energy Information Administration.

New Vehicle Sales
------------------------
*  The full cost pass through assumption
*  Role of fuel consumption in the vehicle purchase decision

*  How the EV/ICE share is calculated
    * user defined submodule is where the logit curve is
    *  Our share estimation is informed by GCAM’s logit equation and parameters.
    * EQUATION
       *  What are these parameters

Vehicle Stock and Use
------------------------
*  We are working to keep internal consistency within the number of vehicles demanded, and the use of those vehicles
*  Vehicle Stock
*  Vehicle Reregistration - user defined submodule
*  VMT - user defined submodule
*  We use the overall VMT demand from Analysis context, the stock of vehicles (new and used), and relationship of the proportion of VMT at each age and market class to allocate VMT across the stock vehicles. This maintains an overall  demand for mobility. By holding total VMT constant, outside of rebound driving, we maintain a logical relationship between mobility and available vehicles.
*  Rebound driving is the additional miles someone might drive due to increased fuel efficiency leading to a lower cost per mile of driving. As fuel efficiency increases, the cost per mile of driving decreases. Economic theory, and results from literature, indicate that as the cost per mile of driving decreasing, VMT increases. This increase is called “VMT rebound.”
*  The total on-road registered fleet (aka stock) includes new vehicle sales and re-registered vehicles for each calendar year. Re-registered vehicles are estimated using fixed re-registration schedules based on vehicle age. Other modules may include feedback between sales and reregistration
*  VMT is estimated using fixed VMT schedules based on vehicle age and market class.

Effects Module
^^^^^^^
In its primary function as a regulatory support tool, OMEGA’s modeled outputs are intended to inform the type of benefit-cost analyses used in EPA rulemakings. We would likely use many of OMEGA’s outputs directly in the analysis for a regulatory action. In other cases, OMEGA produces values that might help inform other models like MOVES. The scope of OMEGA’s effects modeling includes estimating both monetized effects and physical effects.

* Key examples of monetized effects that OMEGA will estimate:
    * Vehicle production costs
    * Vehicle ownership and operation costs, including fuel and maintenance and other consumer impacts
    * Consumer Benefits Measures: Previous estimates of effects on consumers were based on holding sales constant and the benefits were estimated as fuel savings minus tech costs. We know sales change (and we are allowing for that). We are working on a way to estimate not only the benefits consumers are considering in their purchase of a new vehicle, but also the ‘surprise’ or ‘bonus’ savings associated with the vehicle that are not considered.
    * Impacts of criteria air pollutants
    * Impacts of greenhouse gas pollutants
    * Congestion, noise, and safety costs
* Key examples of physical effects that OMEGA will estimate:
    * Stock of registered vehicles, along with key attributes
    * VMT of registered vehicles
    * Tailpipe GHG and criteria pollutant emissions
    * Upstream (refinery, power sector) GHG and criteria pollutant emissions

Note that the calculation of criteria and GHG emission impacts is done using the $/ton estimates included in the cost_factors-criteria.csv and cost_factors-scc.csv input files. The $/ton estimates
provided in those files are best understood to be the marginal costs associated with the reduction of the individual pollutants as opposed to the absolute costs associated with a ton of each pollutant.
As such, the criteria and climate "costs" calculated by the model should not be seen as true costs associated with pollution, but rather the first step in estimating the benefits associated with reductions
of those pollutants. For that reason, the user must be careful not to consider those as absolute costs, but once compared to the "costs" of another scenario (presumably via calculation of a difference
in "costs" between two scenarios) the result can be interpreted as a benefit.

Module Integration and Iteration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Algorithm descriptions, code snippets, equations, etc

