.. image:: _static/epa_logo_1.jpg


Model Architecture and Algorithms
=================================

Modules
^^^^^^^

Consumer Decision Module
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

Producer Decision Module
------------------------
Algorithm descriptions, code snippets, equations, etc

Policy Decision Module
----------------------
Algorithm descriptions, code snippets, equations, etc

Effects Module
--------------
Algorithm descriptions, code snippets, equations, etc

Module Integration and Iteration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Algorithm descriptions, code snippets, equations, etc

