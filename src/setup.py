import sys

from Cython.Build import cythonize
from setuptools import Extension, setup

if sys.platform == "win32":
  cc, ld = ["/O2", "/openmp"], []
else:
  cc, ld = ["-O3", "-fopenmp", "-ffast-math"], ["-fopenmp"]
  if sys.platform == "darwin":
    cc, ld = ["O3", "-ffast-math"], []

setup(
  ext_modules=cythonize(
    Extension("rpc", ["rpc_inverter.pyx"], extra_compile_args=cc, extra_link_args=ld),
    compiler_directives={"language_level": 3},
  )
)
