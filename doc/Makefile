# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.

SOURCEDIR     = source
BUILDDIR      = build
SPHINXOPTS    ?= -v

SPHINXBUILD   ?= sphinx-build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
#     sphinx-apidoc -o "$(SOURCEDIR)" ".." -f -a -H "Code Details" -V 0.0.1 --tocfile code_details

%: Makefile
	sphinx-apidoc -o "$(SOURCEDIR)" ".." -f -a -H "Code Details" -V 0.0.1 --tocfile code_details
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
