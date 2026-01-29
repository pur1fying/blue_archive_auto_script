from pythonforandroid.recipe import PyProjectRecipe


class DecoratorPyRecipe(PyProjectRecipe):
    version = '4.2.1'
    url = 'https://pypi.python.org/packages/source/d/decorator/decorator-{version}.tar.gz'
    url = 'https://github.com/micheles/decorator/archive/{version}.tar.gz'
    depends = ['setuptools']
    site_packages_name = 'decorator'
    call_hostpython_via_targetpython = False


recipe = DecoratorPyRecipe()
