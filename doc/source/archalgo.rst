.. image:: _static/epa_logo_1.jpg


Model Architecture and Algorithms
=================================

Modules
^^^^^^^
[add footnote about terminology, that in the implementation, these are called packages]
Policy Module
----------------------
As primarily a tool for regulatory analyses, OMEGA is designed to have the flexibility to model a range of policy structures. Policy inputs define the alternatives being evaluated, as well as any policies that are not being evaluated directly, but are nevertheless important to include in the analysis context, such as any significant state-level policies which might influence producer and/or consumer decisions. Policy alternatives that can be defined within OMEGA fall into two categories: those that involve fleet average emissions standards and rules for the accounting of compliance credits, and those that specify a required share of a specific technology. Other policies that are not applied directly to the producer as a regulated entity would be reflected in the analysis context. 
•	Policy Alternatives Involving Fleet Average Emissions Standards
The modeling of producer decisions to meet fleet average emissions standards requires the determination of an emissions target and the achieved compliance emissions for each vehicle produced. The difference between the target and achieved compliance emissions in absolute terms (e.g. Mg CO2) is referred to as a ‘credit’, and might be a positive or negative value that can be transferred across years, depending on the credit accounting rules defined in the policy. OMEGA is designed so that within an analysis year, credits from all the producer’s vehicles are counted without limitations towards the total achieved compliance value. When emissions values are presented on a per-vehicle basis, this is known as ‘averaging.’ The transfer of credits between producers can be simulated in OMEGA by representing multiple regulated entities as a single producer, under an assumption that there is no cost or limitation to the transfer of compliance credits among entities. OMEGA is not designed to explicitly model any strategic considerations involved with the transfer of credits between producers. 

Emissions standards are defined in OMEGA using a range of policy elements, including:
	* rules for the accounting of upstream emissions
	* definition of compliance incentives, like multipliers
	* definition of regulatory classes
	* definition of attribute-based target function
	* definition of the vehicles’ assumed lifetime miles

* Policy Alternatives Requiring Specific Technologies 
This type of policy requires all, or a portion, of producer’s vehicles to have particular technologies. OMEGA treats these policy requirements as constraints on the producer’s design options. This type of policy alternative input can be defined either separately, or together with an fleet averaging emissions standard; for example, a minimum ZEV share requirement could be combined with an emissions standard where the certification emissions associated with ZEVs are counted towards the producer’s achieved compliance value.
* Policy Representation in the Analysis Context
Some policies are not modeled in OMEGA as policy alternatives, either because the policy is not aimed directly at the producer as a regulated entity, or because the particular OMEGA analysis is not attempting to evaluate the impact of that policy relative to other alternatives. Still, it is important that the Analysis Context inputs are able to reflect any policies that might significantly influence the producer or consumer decisions. Some examples include:
	* Fuel tax policy
	* State and local ZEV policies
	* Vehicle purchase incentives
	* Investment in refueling and charging infrastructure
	* Accelerated vehicle retirement incentives



Producer Module
------------------------
The modeling of producer decisions is a core function of OMEGA, and is based on minimizing their generalized costs, subject to the constraints of regulatory compliance and consumer demand. The ‘producer’ defined in the OMEGA encompasses both the broader meaning as a supplier of a transportation good or service to the market, and in the narrower sense as the regulated entity subject to EPA policies.

* Inputs and Outputs of the Producer Module
    * Policy Alternative inputs are used to calculate a compliance target for the producer, in Mg CO2 for a given analysis year, using the provided attribute-based standards curve, vehicle regulatory class definitions, and assumed VMT for compliance. Other policy inputs may define, for example, the credit lifetime for carry-forward and carry-back, or a floor on the minimum share of ZEV vehicles produced.
    * Context inputs and assumptions that the Producer Module uses define all factors, apart from the policies under evaluation, that influence the modeled producer decisions. Key factors include the vehicle costs and emissions for the technologies and vehicle attributes considered, and the producer constraints on pricing strategy and cross-subsidization.

* Inside the Producer Module
    * OMEGA incorporates our assumption that producers make strategic decisions, looking beyond the immediate present to minimize generalized costs over a longer time horizon. The efficient management of compliance credits from year-to-year, in particular, involves a degree of look-ahead, both in terms of expected changes in regulatory stringency and other policies, and expected changes in generalized costs over time.
    * The producer’s generalized cost is made up of both the monetary expenses of bringing a product to the consumer, and also the value that the producer expects can be recovered from consumers at the time of purchase. The assumption in OMEGA that producers will attempt to minimize their generalized costs is consistent with a producer goal of profit maximization, subject to any modeling constraints defined in the Consumer Module, such as limiting changes in sales volumes, sales mixes, or select vehicle attributes.


Consumer Module
------------------------
Algorithm descriptions, code snippets, equations, etc

Module Overview
+++++++++++++++

The Consumer Module’s purpose is to estimate how light duty vehicle ownership and use respond to key vehicle characteristics within a given analysis context. An important part of the model is that it allows different endogenous consumer responses to EVs and ICEs. The module estimates total new sales volumes, the EV share of new vehicle demand, used vehicle market responses (including reregistration/scrappage), and the use of both new and used vehicles in the market measured using vehicle miles traveled (VMT).

Inputs from the analysis context are exogenous to the model and include fuel prices, on-road stock assumptions, and demographics. The Consumer Module also uses endogenous inputs from the Producer Module, including vehicle prices and attributes. After the Consumer Module estimates total new vehicle demand, including the EV share of new vehicle demand, the Consumer and Producer Modules iterate to achieve convergence on the vehicles produced and demanded. Once that convergence is achieved, the Consumer Module outputs total vehicle stock (new and used vehicles and their attributes) and use (VMT) to the Effects Module.

Inputs to the Consumer Module
+++++++++++++++++++++++++++++
*  Average vehicle cost, fuel consumption rate, vehicle prices.

*  In principle, the CM can handle other vehicle characteristics that are fed in from the Producer Module (PM), such as vehicle class.

   *  Other vehicle characteristics may be needed for EV/ICE shares calculation.

Outputs from the Consumer Module
+++++++++++++++++++++++++++++++++
*  New vehicle purchases

   *  Broken down by market class. Currently, those classes are EV/ICE/hauling/nonhauling
*  We also estimate the total on-road registered fleet (aka stock), which will go into the Effects Module
*  VMT

New Vehicle Sales
+++++++++++++++++
*  Total new vehicle sales are calculated at the aggregate level

   *  The ability of models to estimate effects on market classes is as yet unproven
*  Explain role of market classes and their relationship to vehicle classes
*  The full cost pass through assumption
*  Role of fuel consumption in the vehicle purchase decision
*  The share of light duty vehicles that are classifies as hauling and nonhauling is constant. The shares of hauling and non-hauling vehicles comes from the projections published in the Annual Energy Outlook from the U.S. Energy Information Administration.

   * Hauling vehicles are classified as body-on-frame, while nonhauling vehicles are classified as uni-body. The vehicles are assumed to be used differently, with hauling vehicles expected to to be used more for hauling goods (including for towing), which nonhauling vehicles are expected to be used for moving people from one place to another.

*  How the EV/ICE share is calculated

   *  Why do we use the logit equation (a diffusion curve)?

      *  We are currently using GCAM’s logit equation and parameters.
*  Documentation on the GCAM parameters used

   *  Can we get Michael Shell and/or Chris Ramig’s help here?
   *  Results from Margaret Taylor’s research

Re-registrations (scrappage)
++++++++++++++++++++++++++++
*  We are currently using static scrappage rates based on the age of the vehicle
*  Where do the current, static, scrappage rates come from
*  Explain the RTI work and how that may update our results

VMT estimations
++++++++++++++++
*  We are using static VMT schedules based on age
*  We currently hold total VMT constant except for rebound
*  The baseline projection for VMT is from AEO

   *  Explain a little about the AEO VMT projections
*  ICE rebound

   *  Can we get help from Michael Shelby for this?
*  EV rebound

   *  Does TCD, Lisa Snapp, CARB have info to help us here?
   *  Burlig et al. EV NBER paper
   *  Other papers?

Consumer Benefits Measures
+++++++++++++++++++++++++++
*  Previous estimates of effects on consumers were based on holding sales constant and the benefits were estimated as fuel savings minus tech costs
*  We know sales change (and we are allowing for that). We are working on a way to estimate not only the benefits consumers are considering in their purchase of a new vehicle, but also the ‘surprise’ or ‘bonus’ savings associated with the vehicle that are not considered.

Overall Model Equilibrium
++++++++++++++++++++++++++
*  Logic for convergence of producer & consumer module results

   *  Cross subsidization logic keeps total new vehicle sales constant
   *  Cross subsidization clears the market for EV and ICE hauling and non-hauling shares
   *  There are 2 ways of doing the cross subsidization

Effects Module
--------------
In its primary function as a regulatory support tool, OMEGA’s modeled outputs are intended to inform the type of benefit-cost analyses used in EPA rulemakings. We would likely use many of OMEGA’s outputs directly in the analysis for a regulatory action. In other cases, OMEGA produces values that might help inform other models like MOVES. The scope of OMEGA’s effects modeling includes estimating both monetized effects and physical effects.

* Key examples of monetized effects that OMEGA will estimate:
	* Vehicle production costs
	* Vehicle ownership and operation costs, including fuel and maintenance and other consumer impacts
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

