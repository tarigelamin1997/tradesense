{ pkgs }: {
  deps = [
    pkgs.python312Full
    pkgs.replitPackages.prybar-python312
    pkgs.replitPackages.stderred
    pkgs.gcc-unwrapped.lib
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
  ];
  env = {
    LD_LIBRARY_PATH = "${pkgs.lib.makeLibraryPath [
      pkgs.gcc-unwrapped.lib
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib
    ]}";
  };
}