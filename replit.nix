{ pkgs }: {
  deps = [
    pkgs.python310Full
    pkgs.python310Packages.pip
    pkgs.python310Packages.setuptools
    pkgs.python310Packages.wheel
    pkgs.gcc
    pkgs.glibc
    pkgs.libstdcxx5
    pkgs.zlib
    pkgs.openssl
    pkgs.pkg-config
  ];
}
