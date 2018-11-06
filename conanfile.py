from conans import ConanFile, CMake, tools
from shutil import copyfile
import os

class LibkateConan(ConanFile):
    name = "libkate"
    version = "0.4.1"
    description = "This is libkate, the reference implementation of a codec for the Kate bitstream format"
    url = "https://github.com/conan-multimedia/libkate"
    wiki = "https://wiki.xiph.org/index.php/OggKate"
    license = "BSD_like"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=True"
    generators = "cmake"
    requires = "libogg/1.3.3@conanos/dev", "libpng/1.6.34@conanos/dev"
    source_subfolder = "source_subfolder"

    def source(self):
        tools.get('http://downloads.xiph.org/releases/kate/{name}-{version}.tar.gz'.format(name=self.name, version=self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_subfolder)

    def build(self):
        with tools.chdir(self.source_subfolder):
            with tools.environment_append({
                'PKG_CONFIG_PATH' : "%s/lib/pkgconfig:%s/lib/pkgconfig"
                %(self.deps_cpp_info["libogg"].rootpath,self.deps_cpp_info["libpng"].rootpath)
                }):
                _args = ["--prefix=%s/builddir"%(os.getcwd())]
                if self.options.shared:
                    _args.extend(['--enable-shared=yes','--enable-static=no'])
                else:
                    _args.extend(['--enable-shared=no','--enable-static=yes'])
                self.run('./configure %s'%(' '.join(_args)))
                self.run('make -j4')
                self.run('make install')

    def package(self):
        if tools.os_info.is_linux:
            with tools.chdir(self.source_subfolder):
                self.copy("*", src="%s/builddir"%(os.getcwd()))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

