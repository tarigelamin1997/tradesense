
{ pkgs }: {
  deps = [
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.gcc
    pkgs.glibc
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
    pkgs.libffi
    pkgs.openssl
    pkgs.git
  ];
  
  env = {
    PYTHONPATH = "$PWD";
    LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.glibc}/lib";
    PYTHONUNBUFFERED = "1";
  };
}
