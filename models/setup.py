# Building an extension module from C source
from distutils.core import setup, Extension
import numpy

simulation_mod = Extension('simulations',
                              sources = ['simulation_main.cpp'],
                              language="c++",
                              include_dirs=[numpy.get_include(),
                              "C:\\Users\\shahi\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\numpy\\core\\include",
                              "C:\\cpp_libs\\include",
                              "C:\\cpp_libs\\include\\bayesopt\\include",
                              "C:\\src\\vcpkg\\installed\\x64-windows\\include",
                              "C:\\src\\vcpkg\\installed\\x86-windows\\include"
                              ]
                            )

# The main setup command
setup(name = 'DissertationModels',
      version="1.0",
      description="Simulation models and temporal integration for different model",
      ext_modules=[simulation_mod],
      # py_modules=['simulation_interface'],
)                            