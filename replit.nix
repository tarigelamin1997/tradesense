
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
    pkgs.sqlite
  ];
  
  env = {
    LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc.lib
      pkgs.glibc
      pkgs.zlib
      pkgs.libffi
      pkgs.openssl
    ];
    PYTHONPATH = "$PYTHONPATH";
  };
}
