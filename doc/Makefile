# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.

SOURCEDIR   = source
BUILDDIR    = build
DOCOPTS    	= --force --append-syspath --doc-project "Code Details" --doc-version 0.9.1 --module-first --tocfile code_details
BUILDOPTS   = -v

SPHINXBUILD   ?= sphinx-build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

%: Makefile
	sphinx-apidoc -o "$(SOURCEDIR)" ".." $(DOCOPTS)
	$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(BUILDOPTS)
