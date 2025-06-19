
{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.python311Packages.pip
    pkgs.python311Packages.setuptools
    pkgs.python311Packages.wheel
    pkgs.python311Packages.distutils
    pkgs.gcc
    pkgs.glibc
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
    pkgs.libffi
    pkgs.openssl
    pkgs.pkg-config
    pkgs.cairo
    pkgs.pango
    pkgs.gdk-pixbuf
    pkgs.atk
    pkgs.gtk3
    pkgs.gobject-introspection
    pkgs.glibcLocales
  ];
  
  env = {
    PYTHONPATH = "$PWD";
    LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.glibc}/lib:${pkgs.zlib}/lib:${pkgs.libffi}/lib";
    PYTHONUNBUFFERED = "1";
    PIP_DISABLE_PIP_VERSION_CHECK = "1";
    PYTHONDONTWRITEBYTECODE = "1";
    LC_ALL = "C.UTF-8";
    LANG = "C.UTF-8";
  };
}
