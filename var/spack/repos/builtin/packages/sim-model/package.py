# Copyright 2013-2018 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *
from contextlib import contextmanager
import os, shutil


class SimModel(Package):
    """The abstract base package for simulation models.

    Simulation models are groups of nmodl mechanisms. These packages are
    deployed as neuron/coreneuron modules (dynamic loadable libraries)
    which are loadable using load_dll() or linked into a "special"

    """
    variant('coreneuron',  default=False, description="Enable CoreNEURON Support")
    variant('profile',     default=False, description="Enable profiling using Tau")

    depends_on('neuron~binary+mpi')
    depends_on('coreneuron', when='+coreneuron')
    depends_on('coreneuron+profile', when='+coreneuron+profile')
    depends_on('neuron+profile', when='+profile')
    depends_on('tau', when='+profile')

    conflicts('^neuron~python', when='+coreneuron')

    # -
    phases = ('build', 'install')

    # The name of the mechanism, which cen be overriden
    mech_name = ''

    # -
    def build(self, spec, prefix):
        link_flag = '-Wl,-rpath,' + prefix.lib
        self._build_mods('mod', link_flag)

    # -
    def _build_mods(self, mods_location, link_flag='', include_flag='', corenrn_mods=None):
        profile_flag = ' -DENABLE_TAU_PROFILER' if '+profile' in self.spec else ''
        include_flag += profile_flag

        if self.spec.satisfies('+coreneuron'):
            mechlib = self.__build_mods_coreneuron(
                corenrn_mods or mods_location, link_flag, include_flag)
            # Link neuron special with this mechs lib
            link_flag += ' ' + mechlib.ld_flags + self._get_lib_flags('coreneuron')
            include_flag += ' -DENABLE_CORENEURON'  # only now, otherwise mods assume neuron

        with profiling_wrapper_on():
            which('nrnivmodl')('-incflags', include_flag, '-loadflags', link_flag, 'mod')
        special = os.path.join(os.path.basename(self.neuron_archdir), 'special')
        assert os.path.isfile(special)
        return special

    # -
    def __build_mods_coreneuron(self, mods_location, link_flag, include_flag):
        spec = self.spec
        assert os.path.isdir(mods_location), mods_location
        include_flag += ' -I%s' % (spec['coreneuron'].prefix.include)
        which('nrnivmodl-core')(
            '-i', include_flag, '-l', link_flag, '-n', self.mech_name,
            '-v', str(spec.version), '-c', mods_location)
        output_dir = spec.architecture.target
        mechlib = find_libraries("libcorenrnmech*", output_dir)
        assert len(mechlib), "Error creating corenrnmech lib"
        return mechlib

    # -
    def _get_lib_flags(self, lib_name):
        """ Helper method to get linking flags similar to spack build, for solid deployments:
              1. static libs passed via full path
              2. shared libs passed with -L -l and RPATH flags
            Attention: This func doesnt handle recursive deps of static libs.
        """
        spec = self.spec[lib_name]
        if spec.satisfies('+shared'):  # Prefer shared if both exist
            return " %s %s" % (spec.libs.rpath_flags, spec.libs.ld_flags)
        return ' ' + spec.libs.joined()

    # -
    def install(self, spec, prefix, install_src=True):
        """ Install:
              bin/ <- special and special-core
              lib/ <- hoc, mod and lib*mech*.so
              share/ <- neuron & coreneuron mod.c's (modc and modc_core)
        """
        mkdirp(prefix.bin)
        mkdirp(prefix.lib)
        mkdirp(prefix.share.modc)

        arch = spec.architecture.target
        shutil.move(join_path(arch, 'special'), prefix.bin)
        shutil.move(arch + "/.libs/libnrnmech.so", prefix.lib)
        self._patch_special(prefix)

        if spec.satisfies('+coreneuron'):
            install = which('nrnivmech_install.sh', path=".")
            install(prefix)

        if install_src:
            self._install_src(prefix)

    @staticmethod
    def _patch_special(prefix, libname='libnrnmech.so'):
        which('sed')('-i',
                     's#-dll .*#-dll %s#' % prefix.lib.join(libname),
                     prefix.bin.special)

    def _install_src(self, prefix):
        """Copy original and translated c mods
        """
        arch = self.spec.architecture.target
        shutil.move('mod', prefix.lib.mod)
        shutil.move('hoc', prefix.lib.hoc)
        shutil.move('common', prefix.lib.common)

        for cmod in find(arch, "*.c", recursive=False):
            shutil.move(cmod, prefix.share.modc)

        if self.spec.satisfies('+coreneuron'):
            shutil.move(join_path(arch, 'core/mod2c'), prefix.share.modc_core)

    # -
    def setup_environment(self, spack_env, run_env):
        run_env.set('BGLIBPY_MOD_LIBRARY_PATH',
                    self.spec.prefix.lib.join('libnrnmech.so'))


@contextmanager
def profiling_wrapper_on():
    os.environ["USE_PROFILER_WRAPPER"] = "1"
    yield
    del os.environ["USE_PROFILER_WRAPPER"]
