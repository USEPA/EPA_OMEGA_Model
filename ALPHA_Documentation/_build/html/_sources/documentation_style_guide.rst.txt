
Documentation Style Guide
=========================
This document defines the style guide and reference for creating ALPHA documentation using  reStructuredText and Sphinx tools.

Reference Guide
^^^^^^^^^^^^^^^

Defining Document Chapters and Sub-Chapters
-------------------------------------------
For ease of access and organization, a separate RST file is created for each chapter.  These chapter file names need to be listed in the index.rst file in the order desired for the final document.

The section numbers in the document are created automatically by Sphinx provided the     ":numbered:" option is present in the index.rst file.  The levels are determined by the characters below the section names:

* ``Chapter numbers (example "6") are underlined by "========" (equals) characters.``
* ``Next sub levels (example 6.1) are underlined by "^^^^^^^^" (caret) characters.``
* ``Next sub levels (example 6.1.1) are underlined by "--------" (dash) characters.``
* ``Next sub levels (example 6.1.1.1) are underlined by "++++++++" (plus) characters.``

::

    Examples:

        Define Chapter Number (example 6):
        Chapter Name
        ============

        Define Next level (example 6.1):
        Name for Sub Level 1
        ^^^^^^^^^^^^^^^^^^^^

        Define Next level (example 6.1.1):
        Name for Sub Level 2
        --------------------

        Define Next level (example 6.1.1.1):
        Name for Sub Level 3
        ++++++++++++++++++++

Here is a typical index.rst file including chapter and other required entries (Do not include the comments on the right side of the example):

::

    EPA ALPHA Model Documentation       <--- Main title of document
    =============================

    .. toctree::                        <--- Compiler directive to make a TOC
        :maxdepth: 4                    <--- Maximum levels in TOC
        :caption: Contents:             <--- Title for TOC
        :numbered:                      <--- Auto number sections

        introduction                    <--- Chapter name list
        overview
        common_use_cases
        model_inputs
        model_outputs
        alpha_development
        contact_information
        company_information
        documentation_style_guide

Creating a Highlighted Section of Text
--------------------------------------
To create a highlighted section of text that also ignores all RST formatting, a double colon is used to start the highlighted and unformatted section.  A blank line, followed by a double colon (::), followed by a blank line defines the section.

::

    This is a highlighted section of text created by inserting a blank line, followed by a
    double colon (::), followed by a blank line and then entering the desired text.  The RST
    formatting is ignored so desired spacing is maintained.

Cross References
----------------
To reference a section, place a marker (crossref1 in this case) above a section followed by a blank line.  Start the marker name with an underscore:

::

 .. _crossref1:

 Section Name
 ------------

To refer to the section, use the following syntax.  The section name will automatically be substituted when compiled.  Be sure to use the back quotes as shown:

::

 :ref:`crossref1`

``"Refer to :ref:`crossref1`" becomes "Refer to Section Name" when compiled.``

Tables
------
First task is to enable automatic numbering in the conf.py file:

::

 numfig = True

The simplest way to insert a table is to create the table in Excel and save it as a CSV file.  Use the following syntax to insert it into the document:

::

 .. _mylabel:

 .. csv-table:: Table Name
    :file: tables/table1.csv
    :widths: 25 25 25 70
    :header-rows: 1

A width value is required for each column or remove the line for auto format.  Number of header rows is optional and provides column labels if needed.

If the optional user defined marker ("mylabel" in this case) is included, the table can be cross referenced using the following syntax (the marker must be preceded by an underscore as shown above):

::

 :numref:`Table %s <mylabel>

``"Please refer to :numref:`Table %s <mylabel>`" becomes "Please refer to Table 1" when compiled.``

Literal Text
------------
At times, text is needed exactly as typed ignoring all markup symbols and compiler directives.  Simply place a double back quote (``) at the beginning and end of the desired text.  This process also switches to a fixed space system font for clarity:

::

``.. #$%^ This text is output exactly as typed.``

Outputs as:

``.. #$%^ This text is output exactly as typed.``

Notice all special characters are shown and ignored by the compiler.










