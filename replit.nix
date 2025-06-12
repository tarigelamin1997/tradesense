
{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.python310Packages.pip
    pkgs.python310Packages.virtualenv
  ];
  env = {
    PIP_CACHE_DIR = "/home/runner/.cache/pip";
  };
}
