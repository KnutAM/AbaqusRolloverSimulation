[//]: # "To preview markdown file in Emacs type C-c C-c p"

# Documentation of Abaqus Rollover Simulation
Code documentation using [Sphinx](http://www.sphinx-doc.org/en/stable/).

## How to use
1. `cd path/to/doc`
1. If there is no *build* directory yet: `mkdir build`
1. If you are building documentation on cluster, run `source module_load_list.txt` to get Sphinx
1. `make` **builder**, where "**builder**" is one of the supported builders, e.g. **html**, 
**latex** or **linkcheck**.
1. Open the documentation. E.g. if you chose html, open `build/html/index.html` with your favourite browser.

## Dependencies
- [Python 2](https://www.python.org) or [Python 3](https://www.python.org)
- [Sphinx](http://www.sphinx-doc.org/en/stable/)
  Install using ``pip install sphinx`` or ``conda install sphinx``
- **``sphinx_rtd_theme``**
  Install using ``pip install sphinx_rtd_theme`` or ``conda install sphinx_rtd_theme``