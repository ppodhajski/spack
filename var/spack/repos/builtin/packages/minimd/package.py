# Copyright 2013-2018 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


import glob
import tarfile

from spack import *


class Minimd(MakefilePackage):
    """Proxy Application. A simple proxy for the force computations
       in a typical molecular dynamics applications.
    """

    homepage = "http://mantevo.org"
    url      = "http://mantevo.org/downloads/releaseTarballs/miniapps/MiniMD/miniMD_1.2.tgz"

    tags = ['proxy-app']

    version('1.2', '893ef1ca5062e32b43a8d11bcfe1a056')

    depends_on('mpi')

    build_directory = 'miniMD_ref'

    @property
    def build_targets(self):
        targets = [
            'LINK={0}'.format(self.spec['mpi'].mpicxx),
            'CC={0}'.format(self.spec['mpi'].mpicxx),
            'CCFLAGS={0} -DMPICH_IGNORE_CXX_SEEK -DNOCHUNK'.format(
                self.compiler.openmp_flag),
            'EXE=miniMD_mpi',
            'openmpi'
        ]

        return targets

    def edit(self, spec, prefix):
        inner_tar = tarfile.open(name='miniMD_{0}_ref.tgz'.format(
                                 self.version.up_to(2)))
        inner_tar.extractall()

    def install(self, spec, prefix):
        # Manual Installation
        mkdirp(prefix.bin)
        mkdirp(prefix.doc)

        install('miniMD_ref/miniMD_mpi', prefix.bin)
        install('miniMD_ref/in.lj.miniMD', prefix.bin)
        install('miniMD_ref/README', prefix.doc)

        for f in glob.glob('miniMD_ref/in.*'):
            install(f, prefix.doc)
