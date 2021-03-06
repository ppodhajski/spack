# Copyright 2013-2018 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *

class Ospray(CMakePackage):
    """A Ray Tracing Based Rendering Engine for High-Fidelity Visualization"""

    homepage = "https://www.ospray.org/"
    git = "https://github.com/ospray/ospray.git"
    generator = 'Ninja'

    version('1.8.3', tag='v1.8.3')
    version('1.7.3', tag='v1.7.3', preferred=True)

    depends_on('cmake@3.1:', type='build')
    depends_on('ispc', type='build')
    depends_on('ninja', type='build')
    depends_on('embree')
    depends_on('mpi')

    def cmake_args(self):
        return ['-DOSPRAY_ENABLE_TUTORIALS=OFF', '-DOSPRAY_MODULE_MPI=ON',
                '-DCMAKE_C_COMPILER={}'.format(self.spec['mpi'].mpicc),
                '-DCMAKE_CXX_COMPILER={}'.format(self.spec['mpi'].mpicxx)]

