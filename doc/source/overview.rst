.. image:: _static/epa_logo_1.jpg

Model Overview
==============

Brief intro: Diagram + high level summary

Summarize inputs and outputs

Consumer Modeling for EPA’s OMEGA Model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Introduction
------------
EPA’s Office of Transportation and Air Quality is constantly looking for ways to improve the analyses performed in support of the regulations put forth. A current effort is focused on updating our ability to model producer and consumer responses to regulations that reduce greenhouse gasses emissions from light duty vehicles in the United States. The thrust of this effort has been focused on creating a new OMEGA model, which updates the useability and capabilities of the first OMEGA model. One major update is the introduction of endogenous consumer choice modeling. This document lays out the inputs, outputs, assumptions and equations that are used in the consumer modeling effort. It does not include documentation for other portions of the OMEGA model. It also does not include documentation of the OMEGA code. For documentation on the OMEGA model as whole, see `OMEGA Documentation <https://omega2.readthedocs.io/>`_ . To explore the OMEGA model code, see `OMEGA GitHub <https://github.com/USEPA/EPA_OMEGA_Model/>`_ .

History of OMEGA
++++++++++++++++
The EPA first created an OMEGA model over ten years ago to estimate producer responses to greenhouse gas emission reducing policies. This model evaluated relative costs and effectiveness of available technology packages, applied them to a defined fleet to meet a specified footprint-based fleet emissions standard. The model generated cost-minimizing compliance pathways for individual manufacturers in five year time steps assuming fleet averaging and unlimited car-truck transfers within each company. A high-level overview of the structure of the original OMEGA model can be seen in :numref:`mo_label1`. The existing stock and footprint-based policy alternatives were fed into the model, producers decided the level and types of vehicles to produce while meetings the requirements, and the societal costs and environmental effects were estimated for the resulting estimated stock.

.. _mo_label1:
.. figure:: _static/mo_figures/original_omega_model_overview.jpg
    :align: center

    Original OMEGA Model Overview

Though the model was used in multiple EPA regulatory analyses between 2010 and 2016, the state of the world has changed dramatically over the years and the model’s assumptions and capabilities have become out of date since it was first created. A major change in the state of the world is an expanded focus beyond the traditional internal combustion engine (ICE) vehicle. Electric vehicle (EV) technology and markets have evolved significantly, and will likely continue to evolve. In addition, there are potential changes in mobility demand and new mobility services, including the use of light duty vehicles (LDVs) for deliver services, shared and autonomous fleets, and the increased focus on micromobility. We are unable to incorporate these changes in the previous OMEGA model. In addition, our model design capabilities and the tools available to us have expanded. Taken together, this has led us to create a new OMEGA model. This new OMEGA model is an open source compliance and effects modeling tool that is transparent, user-friendly, and has the flexibility to evaluate a broad range of transportation policy, technology and market scenarios.

New OMEGA Model
+++++++++++++++
Creating a new OMEGA model has allowed us to improve upon previous efforts in a few ways, including building in pre- and post-processing steps, adding endogenous consumer responses, improving manufacturer decision modeling and adding feedback between consumer and producer decisions. In addition, the model is built to be modular, user friendly, and transparent. Stakeholders will more easily be able to inspect the model and assumptions, as well as revise assumptions and generate results without unusual computing capabilities, extensive training or restrictive licensing. The model itself is available to the public on GitHub.  The model takes context assumptions, existing stock and policy alternatives, iterates on producer choices and consumer responses, and estimates effects, outputting societal costs and environmental effects. A simplistic overview of the updated model is seen in :numref:`mo_label2`, below.

.. _mo_label2:
.. figure:: _static/mo_figures/new_omega_model_overview.jpg
    :align: center

    New OMEGA Model Overview

The New Consumer Module
+++++++++++++++++++++++
In comparing :numref:`mo_label1` and :numref:`mo_label2`, it is readily apparent that a major update is the addition of the Consumer Module. This document is to inform the reader of the input choices and assumptions we have made with respect to the consumer modeling for the new OMEGA model. The Consumer Module’s purpose is to estimate how vehicle ownership and use respond to key vehicle characteristics with a given analysis context. An important part of the model is that it allows different endogenous consumer responses to EVs and ICEs. Additionally, the share of vehicles that are classified as hauling and non-hauling are estimated using exogenous assumptions. This means that new vehicles sales are separated into four distinct market classes: non-hauling EVs, hauling EVs, non-hauling ICE and hauling ICE. The module estimates total new sales volumes, the EV share of new vehicle demand, used vehicle market responses (including reregistration/scrappage), and the use of both new and used vehicles in the market measured using vehicle miles traveled (VMT).

The analysis context is made up of the inputs that are exogenous to the model, including fuel prices, on-road stock assumptions, and demographics. The module also uses endogenous inputs from the Producer Module, including vehicle prices and attributes. After the Consumer Module estimates total new vehicle demand, including the EV share of new vehicle demand, the Consumer and Producer Modules iterate to achieve convergence on the vehicles produced and demanded. Once that convergence is achieved, the Consumer Module outputs total vehicle stock (new and used vehicles and their attributes) and use (VMT) to the Effect Module.
The rest of this document will go into more detail on inputs, outputs and methods used in the Consumer Module. Included in this are our explanations why we aggregate vehicles into the four market classes, how we estimate EV shares, how we estimate used vehicle responses to regulation, our VMT estimate assumption, rebound assumptions, how we are estimating consumer benefits, and the logic behind the consumer-producer iteration.

Inputs to the Consumer Module
-----------------------------
*  Average vehicle cost, fuel consumption rate, vehicle prices.
*  In principle, the CM can handle other vehicle characteristics that are fed in from the Producer Module (PM), such as vehicle class.

   *  Other vehicle characteristics may be needed for EV/ICE shares calculation.

Outputs from the Consumer Module
--------------------------------
*  New vehicle purchases

   *  Broken down by EV/ICE/hauling/nonhauling
*  We also estimate the total on-road registered fleet (aka stock), which will go into the Effects Module
*  VMT

How are New Vehicle Sales Calculated
------------------------------------
*  Total new vehicle sales are calculated at the aggregate level

   *  The ability of models to estimate effects on market classes is as yet unproven
*  Explain role of market classes and their relationship to vehicle classes
*  The full cost pass through assumption
*  Role of fuel consumption in the vehicle purchase decision
*  Hauling/nonhauling shares

   *  Why we keep it constant
   *  Why we think this is ok
   *  We get the shares from AEO
*  How the EV/ICE share is calculated

   *  Why do we use the logit equation (a diffusion curve)?

      *  We are currently using GCAM’s logit equation and parameters.
*  Documentation on the GCAM parameters used

   *  Can we get Michael Shell and/or Chris Ramig’s help here?
   *  Results from Margaret Taylor’s research

Re-registrations (scrappage)
----------------------------
*  We are currently using static scrappage rates based on the age of the vehicle
*  Where do the current, static, scrappage rates come from
*  Explain the RTI work and how that may update our results

VMT estimations
---------------
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
--------------------------
*  Previous estimates of effects on consumers were based on holding sales constant and the benefits were estimated as fuel savings minus tech costs
*  We know sales change (and we are allowing for that). We are working on a way to estimate not only the benefits consumers are considering in their purchase of a new vehicle, but also the ‘surprise’ or ‘bonus’ savings associated with the vehicle that are not considered.

Overall Model Equilibrium
-------------------------
*  Logic for convergence of producer & consumer module results

   *  Cross subsidization logic keeps total new vehicle sales constant
   *  Cross subsidization clears the market for EV and ICE hauling and non-hauling shares
   *  There are 2 ways of doing the cross subsidization




Text2
^^^^^

Text3
^^^^^

Text4
^^^^^

Text5
^^^^^