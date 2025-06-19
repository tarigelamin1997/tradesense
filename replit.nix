
{ pkgs }: {
  deps = [
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.gcc
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
    pkgs.libffi
  ];
  
  env = {
    PYTHONPATH = "$PWD";
    LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib";
    PYTHONUNBUFFERED = "1";
  };
}
