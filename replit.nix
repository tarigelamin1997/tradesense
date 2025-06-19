{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.python311Packages.pip
  ];

  env = {
    PYTHONPATH = "$PWD";
    PYTHONUNBUFFERED = "1";
  };
}