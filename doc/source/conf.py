# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import importlib

path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(path, '..', '..', 'omega_effects'))  # picks up omega_effects sub-packages
sys.path.insert(0, os.path.join(path, '..', '..', 'omega_model'))  # picks up omega_model sub-packages
sys.path.insert(0, os.path.join(path, '..', '..', 'omega_gui'))  # picks up omega_model sub-packages
sys.path.insert(0, os.path.join(path, '..', '..'))  # picks up the top-level packages
print('path = %s' % path)

# -- Project information -----------------------------------------------------

import datetime

project = 'OMEGA'
copyright = '%s, US EPA' % datetime.datetime.now().strftime('%Y')
author = 'US EPA'

# The full version, including alpha/beta/rc tags
release = '2.1.0'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo'
]

autodoc_default_options = {
    'member-order': 'bysource',  # other option is 'alphabetical'
    'special-members': '__init__',
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['*setup*', '*exe_entry*']

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_css_files = [path + '/_static/omega_rtd_theme.css']
html_style = path + '/_static/omega_rtd_theme.css'
print('html_css_files = %s' % html_css_files)
html_logo = path + '/_static/OMEGA_logo_transparent.png'
print('html_logo = %s' % html_logo)
numfig = True
todo_include_todos = True

theme = importlib.import_module('sphinx_rtd_theme')
if 'html_theme_path' in globals():
    html_theme_path.append(theme.get_html_theme_path())
else:
    html_theme_path = [theme.get_html_theme_path()]
print('html_theme_path = %s' % html_theme_path)

html_title = '%s %s Documentation (rev. % s)' % (project, release, datetime.datetime.now().strftime('%-m/%-d/%Y'))

html_last_updated_fmt = '%-m/%-d/%Y'

html_theme_options = {
    'navigation_depth': 5,
    'style_nav_header_background': '#0071BC',
    'collapse_navigation': False,
}

# EPA Palette
# html_theme_options = {
#     "stickysidebar": "true",
#     "sidebarwidth": "30em",
#     "sidebarbgcolor": "#0071BC",
#     "sidebartextcolor": "#FFFFFF",
#     "sidebarlinkcolor": "#FFFFFF",
#     "relbarbgcolor": "#205493",
#     "textcolor": "#205493",
#     "linkcolor": "#205493",
#     "visitedlinkcolor": "#205493",
#     "headtextcolor": "#205493",
#     "headlinkcolor": "#205493",
#     "footerbgcolor": "#112E51"
# }

# html_sidebars = {
#    '**': ['globaltoc.html', 'sourcelink.html', 'searchbox.html'],
#    'using/windows': ['windowssidebar.html', 'searchbox.html'],
# }

# -- Options for  LaTeX output -------------------------------------------------

latex_elements = {
  'extraclassoptions': 'openany,oneside'
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

# set top level document to index.rst:
master_doc = 'index'

add_module_names = False

# ###########################################################################
# #          auto-created readthedocs.org specific configuration            #
# ###########################################################################
#
#
# #
# # The following code was added during an automated build on readthedocs.org
# # It is auto created and injected for every build. The result is based on the
# # conf.py.tmpl file found in the readthedocs.org codebase:
# # https://github.com/rtfd/readthedocs.org/blob/main/readthedocs/doc_builder/templates/doc_builder/conf.py.tmpl
# #
# # Note: this file shouldn't rely on extra dependencies.
#
# import importlib
# import sys
# import os.path
#
# # Borrowed from six.
# PY3 = sys.version_info[0] == 3
# string_types = str if PY3 else basestring
#
# from sphinx import version_info
#
# # Get suffix for proper linking to GitHub
# # This is deprecated in Sphinx 1.3+,
# # as each page can have its own suffix
# if globals().get('source_suffix', False):
#     if isinstance(source_suffix, string_types):
#         SUFFIX = source_suffix
#     elif isinstance(source_suffix, (list, tuple)):
#         # Sphinx >= 1.3 supports list/tuple to define multiple suffixes
#         SUFFIX = source_suffix[0]
#     elif isinstance(source_suffix, dict):
#         # Sphinx >= 1.8 supports a mapping dictionary for multiple suffixes
#         SUFFIX = list(source_suffix.keys())[0]  # make a ``list()`` for py2/py3 compatibility
#     else:
#         # default to .rst
#         SUFFIX = '.rst'
# else:
#     SUFFIX = '.rst'
#
# # Add RTD Static Path. Add to the end because it overwrites previous files.
# if not 'html_static_path' in globals():
#     html_static_path = []
# if os.path.exists('_static'):
#     html_static_path.append('_static')
#
# # Add RTD Theme only if they aren't overriding it already
# using_rtd_theme = (
#         (
#                 'html_theme' in globals() and
#                 html_theme in ['default'] and
#                 # Allow people to bail with a hack of having an html_style
#                 'html_style' not in globals()
#         ) or 'html_theme' not in globals()
# )
# if using_rtd_theme:
#     html_theme = 'sphinx_rtd_theme'
#     html_style = None
#     html_theme_options = {}
#
# # This following legacy behavior will gradually be sliced out until its deprecated and removed.
# # Skipped for Sphinx 6+
# # Skipped by internal Feature flag SKIP_SPHINX_HTML_THEME_PATH
# # Skipped by all new projects since SKIP_SPHINX_HTML_THEME_PATH's introduction (jan 2023)
# if (
#         using_rtd_theme
#         and version_info < (6, 0)
#         and not False
# ):
#     theme = importlib.import_module('sphinx_rtd_theme')
#     if 'html_theme_path' in globals():
#         html_theme_path.append(theme.get_html_theme_path())
#     else:
#         html_theme_path = [theme.get_html_theme_path()]
#
# # Define websupport2_base_url and websupport2_static_url
# if globals().get('websupport2_base_url', False):
#     websupport2_base_url = 'https://readthedocs.org/websupport'
#     websupport2_static_url = 'https://assets.readthedocs.org/static/'
#
# # Add project information to the template context.
# context = {
#     'using_theme': using_rtd_theme,
#     'html_theme': html_theme,
#     'current_version': "latest",
#     'version_slug': "latest",
#     'MEDIA_URL': "https://media.readthedocs.org/",
#     'STATIC_URL': "https://assets.readthedocs.org/static/",
#     'PRODUCTION_DOMAIN': "readthedocs.org",
#     'proxied_static_path': "/_/static/",
#     'versions': [
#         ("latest", "/en/latest/"),
#         ("2.1.0", "/en/2.1.0/"),
#         ("2.0.1", "/en/2.0.1/"),
#     ],
#     'downloads': [
#         ("html", "//omega2.readthedocs.io/_/downloads/en/latest/htmlzip/"),
#     ],
#     'subprojects': [
#     ],
#     'slug': 'omega2',
#     'name': u'OMEGA',
#     'rtd_language': u'en',
#     'programming_language': u'words',
#     'canonical_url': 'https://omega2.readthedocs.io/en/latest/',
#     'analytics_code': 'None',
#     'single_version': False,
#     'conf_py_path': '/doc/source/',
#     'api_host': 'https://readthedocs.org',
#     'github_user': 'USEPA',
#     'proxied_api_host': '/_',
#     'github_repo': 'EPA_OMEGA_Model',
#     'github_version': 'developer',
#     'display_github': True,
#     'bitbucket_user': 'None',
#     'bitbucket_repo': 'None',
#     'bitbucket_version': 'developer',
#     'display_bitbucket': False,
#     'gitlab_user': 'None',
#     'gitlab_repo': 'None',
#     'gitlab_version': 'developer',
#     'display_gitlab': False,
#     'READTHEDOCS': True,
#     'using_theme': (html_theme == "default"),
#     'new_theme': (html_theme == "sphinx_rtd_theme"),
#     'source_suffix': SUFFIX,
#     'ad_free': False,
#     'docsearch_disabled': False,
#     'user_analytics_code': '',
#     'global_analytics_code': 'UA-17997319-1',
#     'commit': 'b0e0d4cd',
# }
#
# # For sphinx >=1.8 we can use html_baseurl to set the canonical URL.
# # https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_baseurl
# if version_info >= (1, 8):
#     if not globals().get('html_baseurl'):
#         html_baseurl = context['canonical_url']
#     context['canonical_url'] = None
#
# if 'html_context' in globals():
#
#     html_context.update(context)
#
# else:
#     html_context = context
#
# # Add custom RTD extension
# if 'extensions' in globals():
#     # Insert at the beginning because it can interfere
#     # with other extensions.
#     # See https://github.com/rtfd/readthedocs.org/pull/4054
#     extensions.insert(0, "readthedocs_ext.readthedocs")
# else:
#     extensions = ["readthedocs_ext.readthedocs"]
#
# # Add External version warning banner to the external version documentation
# if 'branch' == 'external':
#     extensions.insert(1, "readthedocs_ext.external_version_warning")
#     readthedocs_vcs_url = 'None'
#     readthedocs_build_url = 'https://readthedocs.org/projects/omega2/builds/20371843/'
#
# project_language = 'en'
#
# # User's Sphinx configurations
# language_user = globals().get('language', None)
# latex_engine_user = globals().get('latex_engine', None)
# latex_elements_user = globals().get('latex_elements', None)
#
# # Remove this once xindy gets installed in Docker image and XINDYOPS
# # env variable is supported
# # https://github.com/rtfd/readthedocs-docker-images/pull/98
# latex_use_xindy = False
#
# chinese = any([
#     language_user in ('zh_CN', 'zh_TW'),
#     project_language in ('zh_CN', 'zh_TW'),
# ])
#
# japanese = any([
#     language_user == 'ja',
#     project_language == 'ja',
# ])
#
# if chinese:
#     latex_engine = latex_engine_user or 'xelatex'
#
#     latex_elements_rtd = {
#         'preamble': '\\usepackage[UTF8]{ctex}\n',
#     }
#     latex_elements = latex_elements_user or latex_elements_rtd
# elif japanese:
#     latex_engine = latex_engine_user or 'platex'
#
# # Make sure our build directory is always excluded
# exclude_patterns = globals().get('exclude_patterns', [])
# exclude_patterns.extend(['_build'])
