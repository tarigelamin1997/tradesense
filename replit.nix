{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.setuptools
    pkgs.python311Packages.wheel
    pkgs.bash
    pkgs.coreutils
    pkgs.findutils
    pkgs.gnugrep
    pkgs.gnused
  ];

  env = {
    PYTHONPATH = "$PWD";
    PYTHONUNBUFFERED = "1";
    PYTHONDONTWRITEBYTECODE = "1";
    PIP_DISABLE_PIP_VERSION_CHECK = "1";
    PIP_NO_CACHE_DIR = "1";
    LC_ALL = "C";
    LANG = "C";
  };
}