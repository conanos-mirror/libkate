from conans import ConanFile, tools, MSBuild
from conanos.build import config_scheme
import os, shutil

class LibkateConan(ConanFile):
    name = "libkate"
    version = "0.4.1"
    description = "This is libkate, the reference implementation of a codec for the Kate bitstream format"
    url = "https://github.com/conanos/libkate"
    homepage = "https://wiki.xiph.org/index.php/OggKate"
    license = "BSD"
    patch = "msvc-PRId64-define.patch"
    msvc_defs = ["libkate.def", "liboggkate.def"]
    msvc_projs = ["libkate.vcproj", "liboggkate.vcproj","example_dec.vcproj","example_enc.vcproj","katalyzer.vcproj","katedec.vcproj","kateenc.vcproj" ]
    exports = ["COPYING", patch, "shared/*"] + msvc_defs
    generators = "visual_studio", "gcc"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = { 'shared': True, 'fPIC': True }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

        config_scheme(self)

    def requirements(self):
        self.requires.add("libogg/1.3.3@conanos/stable")
        self.requires.add("libpng/1.6.34@conanos/stable")

    def source(self):
        url_ = 'http://downloads.xiph.org/releases/kate/libkate-{version}.tar.gz'
        tools.get( url_.format(version=self.version) )
        if self.settings.os == 'Windows':
            tools.patch(patch_file=self.patch)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)
        if self.settings.os == 'Windows':
            for lib_def in self.msvc_defs:
                shutil.copy2(os.path.join(self.source_folder,lib_def),
                             os.path.join(self.source_folder,self._source_subfolder,"contrib","build","win32","vc2008",lib_def))
            self._replace_include_and_dependency()

    def _replace_include_and_dependency(self):
        replacements = {
            "..\..\..\..\..\libogg\include":os.path.join(self.deps_cpp_info["libogg"].rootpath,"include"),
            "libogg.lib" : os.path.join(self.deps_cpp_info["libogg"].rootpath,"lib","ogg.lib"),
            "libpng.lib" : os.path.join(self.deps_cpp_info["libpng"].rootpath,"lib","libpng16d.lib"),
            "..\..\..\..\..\libpng" : os.path.join(self.deps_cpp_info["libpng"].rootpath,"include")
        }
        for proj in self.msvc_projs:
            for s, r in replacements.items():
                tools.replace_in_file(os.path.join(self.source_folder, "shared",proj),s,r,strict=False)
            shutil.copy2(os.path.join(self.source_folder,"shared",proj),
                             os.path.join(self.source_folder,self._source_subfolder,"contrib","build","win32","vc2008",proj))
        
        shutil.copy2(os.path.join(self.source_folder,"shared","vc2008.sln"),
                     os.path.join(self.source_folder,self._source_subfolder,"contrib","build","win32","vc2008","vc2008.sln"))

    def build(self):
        if self.settings.os == 'Windows':
            with tools.chdir(os.path.join(self._source_subfolder,"contrib","build","win32","vc2008")):
                msbuild = MSBuild(self)
                msbuild.build("vc2008.sln",upgrade_project=True,platforms={'x86': 'Win32', 'x86_64': 'x64'})
        #with tools.chdir(self.source_subfold er):
        #    with tools.environment_append({
        #        'PKG_CONFIG_PATH' : "%s/lib/pkgconfig:%s/lib/pkgconfig"
        #        %(self.deps_cpp_info["libogg"].rootpath,self.deps_cpp_info["libpng"].rootpath)
        #        }):
        #        _args = ["--prefix=%s/builddir"%(os.getcwd())]
        #        if self.options.shared:
        #            _args.extend(['--enable-shared=yes','--enable-static=no'])
        #        else:
        #            _args.extend(['--enable-shared=no','--enable-static=yes'])
        #        self.run('./configure %s'%(' '.join(_args)))
        #        self.run('make -j4')
        #        self.run('make install')

    def package(self):
        if self.settings.os == 'Windows':
            platforms={'x86': 'Win32', 'x86_64': 'x64'}
            output_rpath = os.path.join("contrib","build","win32","vc2008",platforms.get(str(self.settings.arch)), str(self.settings.build_type))
            for lib in ["libkate","liboggkate"]:
                self.copy("%s.*"%(lib), dst=os.path.join(self.package_folder,"lib"),
                          src=os.path.join(self.source_folder,self._source_subfolder,output_rpath),
                          excludes=["%s.dll"%(lib),"%s.tlog"%(lib)])
                self.copy("%s.dll"%(lib), dst=os.path.join(self.package_folder,"bin"),
                          src=os.path.join(self.source_folder,self._source_subfolder,output_rpath))
            for exe in ["kateenc","katedec","katalyzer","example_dec","example_enc"]:
                self.copy("%s.*"%(exe), dst=os.path.join(self.package_folder,"bin"),
                          src=os.path.join(self.source_folder,self._source_subfolder,output_rpath),
                          excludes=["%s.tlog"%(exe)])
            
            tools.mkdir(os.path.join(self.package_folder,"lib","pkgconfig"))

            replacements = {
                "@prefix@"          : self.package_folder,
                "@exec_prefix@"     : "${prefix}/lib",
                "@libdir@"          : "${prefix}/lib",
                "@includedir@"      : "${prefix}/include",
                "@VERSION@"         : self.version,
            }
            for pc in ["kate.pc.in","oggkate.pc.in"]:
                shutil.copy(os.path.join(self.build_folder,self._source_subfolder,"misc","pkgconfig",pc),
                            os.path.join(self.package_folder,"lib","pkgconfig",pc))
                for s, r in replacements.items():
                    tools.replace_in_file(os.path.join(self.package_folder,"lib","pkgconfig",pc),s,r)
            

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

