.. image:: _static/epa_logo_1.jpg

Model Overview
==============
The OMEGA model has been developed by EPA to evaluate policies for reducing greenhouse gas emissions (GHG) from light duty vehicles. Like the prior releases, this latest version is intended primarily to be used as a tool to support regulatory development by providing estimates of the effects and costs of policy alternatives under consideration. These include the costs associated with emissions-reducing technologies themselves and the items normally included in a societal benefit-cost analysis, as well as physical effects that include emissions quantities, and vehicle stock and usage.  In developing this version, we have attempted to emphasize modularity, transparency, and flexibility so that stakeholders can more easily review the model, conduct independent analyses, and potentially develop modules to meet their own needs.

What's New in This Version 2.0
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
EPA created the initial release version of the OMEGA model to analyze new GHG standards for light-duty vehicles proposed in 2011. The 'core' model performed the function of identifying manufacturers' cost-minimizing compliance pathways to meet a footprint-based fleet emissions standard specified by the user. A preprocessing step involved ranking the technology packages to be considered by the model based on cost-effectiveness. Postprocessing of outputs was performed separately using a spreadsheet tool, and later a scripted process which generated table summaries of modeled effects.

With the release of version 2.0, we aim to improve usability and flexibility while retaining the primary functions of the original version of OMEGA. :numref:`mo_label_compare` shows the overall model flow and highlights the main areas that have been revised and updated.

.. _mo_label_compare:
.. figure:: _static/mo_figures/model_overview_compare_ver1_ver2.png
    :align: center

    Comparison to prior version of OMEGA

**Update #1: expanded model boundaries.** In defining the scope of this model version, we have attempted to simplify the process of conducting a run by incorporating into the model some of the pre- and post-processing that had previously been performed manually. At the same time, we recognize that an overly-expansive model boundary can result in requirements for inputs that are difficult-to-specify. To avoid this, we have set the input boundary only so large as to capture the elements of the system we assume are responsive to policy. In general, model inputs can be quantified using data for observable, real-world characteristics and phenomena, and in that way enable transparency by allowing the user to maintain the connection to the underlying data. For the assumptions and algorithms within the model boundary, we aim for transparency through well-organized model code and complete documentation.

**Update #2: an independent Policy Module.** The previous version of OMEGA was designed to analyze a very specific GHG policy structure in which the vehicle attributes and regulatory classes used to determine emissions targets were incorporated into the code throughout the model. In order to make it easier to define and analyze other policy structures, the details regarding how targets are determined and how compliance credits are treated over time are now included in an independent Policy Module and associated policy inputs. This allows the developer to incorporate new policy structures without requiring revisions to other code modules. Specifically, the producer decision module no longer contains any details specific to a GHG program structure, and instead functions only on very general program features such as fleet averaging of absolute GHG credits and required technology shares.

**Update #3: the modeling of multi-year strategic producer decisions.** As a policy analysis tool, OMEGA is intended to model the effect of policies that may extend well into the future, beyond the timeframe of individual product cycles. This version of OMEGA is structured to consider a producer objective function to be optimized over the entire analysis period. This allows the explicit consideration of compliance decisions which account for year-over-year credit management in the context of projections for technology cost and market conditions which change over time.

**Update #4: the addition of a consumer response component.** The light-duty vehicle market has evolved significantly in the time since the initial release of OMEGA. In particular, as the range of available technologies and services has grown wider, so has the range of possible responses to policy alternatives. The model structure for this version includes a Consumer Module that can be used to define how the light-duty vehicle market responds to policy-driven changes in price, fuel operating costs, and other consumer-facing vehicle attributes. The Consumer Module outputs the estimated responses for overall sales and sales shares, as well as vehicle re-registration and use, which together determine the stock of new and used vehicles and the associated allocation of total VMT.

**Update #5: the addition of feedback loops for producer decisions.** This version of OMEGA is structured around modeling the interactions between vehicle producers responding to a policy and consumers who own and use those vehicles. These interactions are bi-directional, in that the producer's compliance planning and vehicle design decisions will both influence, and be influenced by, the sales and shares of vehicles sold and the GHG credits assigned under the policy. Iterative feedback loops have now been incorporated between the producer and consumer modules, and between the producer and policy modules.

Inputs and Outputs
^^^^^^^^^^^^^^^^^^
Like any other model, OMEGA relies on the user to specify appropriate inputs and assumptions. Some of these may be provided by direct empirical observations, for example the number of currently registered vehicles. Others might be generated by modeling tools outside of OMEGA, such as physics-based vehicle simulation results produced by EPA's ALPHA model, or transportation demand forecasts from DOE's NEMS model. OMEGA has adopted data elements and structures that are generic, wherever possible, so that inputs can be provided from whichever sources the user deems most appropriate.

The inputs and assumptions are categorized according to whether they fall inside or outside the policy alternatives under evaluation in a given analysis.

* *Policy Alternative* inputs describe the standards themselves, including the program elements and methodologies for determining compliance as would be defined for an EPA rule in the Federal Register and Code of Federal Regulations.

* *Analysis Context* inputs and assumptions cover the range of factors that the user assumes, for the purpose of analyses, are independent of the policy alternatives. The user may project changes in the context inputs over the analysis timeframe based on other sources, but for a given analysis year the context definition requires that these inputs are common across the policy alternatives being compared. The context inputs may include fuel costs, costs and emissions rates for a particular vehicle technology package, consumer demand parameters, and many more.

A full description of the input files can be found in [Chapter 7].

The primary outputs are the environmental effects and societal costs and benefits for a given policy alternative and analysis context pair. These outputs are expressed in absolute values, so that incremental effects, costs, and benefits can be evaluated by comparing two policy alternatives (for a given context) or the sensitivity to assumptions for two different analysis contexts (for a given policy alternative.)

Model Structure and Key Modules
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
OMEGA has been set up so that primary components of the model are clearly delineated in such a way that changing one component of the model will not require code changes throughout the model. Four main modules are defined along the lines of their real-world analogs representing consumers, producers, policy, and effects. This structure allows a user to analyze a policy in a strictly-defined way and provides users the option of interchanging any of OMEGA’s default modules with their own, while preserving the consistency and functionality of the larger model.

OMEGA is structured around two key modules; a Producer Module and a Consumer Module, which each contain a decision-model for the respective entities. The Producer Module's purpose is to estimate how producers will respond to a policy within the given analysis context. The Consumer Module’s purpose is to estimate how vehicle ownership and use respond to key vehicle characteristics, including vehicle cost, within a given analysis context.

The two additional Modules are the Policy Module and Effects Module. The Policy Module is used to identify the policy alternative assumptions producers are required to meet in the Producer Module. The Effects Module estimates the final model outputs, including costs and benefits.

Iteration and Convergence
^^^^^^^^^^^^^^^^^^^^^^^^^
OMEGA is intended to find a solution which simultaneously satisfies producer, consumer, and policy requirements while minimizing the producer’s generalized costs. OMEGA’s Producer and Consumer modules represent distinct decision-making entities, with behaviors defined separately by the user. Without some type of interaction between these modules, the model would likely not arrive at an equilibrium of vehicles supplied and demanded. For example, a compliance solution which only minimizes producer generalized costs without consideration of consumer demand may not satisfy the market requirements at the fleet mix and level of sales preferred by the producer. Since there is no general analytical solution to this problem which also allows model users to independently define producer and consumer behavior, OMEGA uses an iterative search approach.

Analysis Resolution
^^^^^^^^^^^^^^^^^^^
The outcomes of consumer and producer decision-making in OMEGA are expressed via the vehicles modeled in the analysis period, the volumes of vehicles produced, the applied technologies and relevant vehicle attributes, and the re-registration and use over all vehicles’ lifetimes. Because there can be nearly 20 million light-duty vehicles produced for sale each year in the US, and hundreds of millions of vehicles registered for use at any given time, OMEGA must aggregate, as appropriate, while still distinguishing between vehicles when needed. The approach for aggregating vehicles varies based on the different functions and modules within OMEGA, with the general principles applied throughout OMEGA to 1) use the amount of vehicle detail required, but no more than is required, to perform any particular modeling sub-task, and 2) to retain vehicle details that will be needed for subsequent modeling tasks.

* The modeling of producer decisions requires that the model retains sufficient detail to calculate the target and achieved compliance emissions, as well as any details needed to calculate the generalized producer cost.
* The modeling of consumer decisions requires that the model retains sufficient detail to distinguish between market classes for representing both the purchase choices among different classes, and the reregistration and use of vehicles within a given class. Because the way that consumer decisions are modeled is a replaceable module, the definition of market classes depends on the requirements of the approach used.

How to Navigate this Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
x