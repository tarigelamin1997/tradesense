
{ pkgs }: {
  deps = [
    pkgs.psmisc
    pkgs.nano
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.python312Packages.setuptools
    pkgs.openssl
    pkgs.libxcrypt
    pkgs.zlib
  ];
}
