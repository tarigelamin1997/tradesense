
{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.python311Packages.pip
    pkgs.python311Packages.setuptools
    pkgs.python311Packages.wheel
    pkgs.gcc
    pkgs.glibc
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
    pkgs.libffi
    pkgs.openssl
    pkgs.pkg-config
    pkgs.glibcLocales
  ];
  
  env = {
    PYTHONPATH = "$PWD";
    PYTHONUNBUFFERED = "1";
    PIP_DISABLE_PIP_VERSION_CHECK = "1";
    PYTHONDONTWRITEBYTECODE = "1";
    LC_ALL = "C.UTF-8";
    LANG = "C.UTF-8";
    LD_LIBRARY_PATH = "${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.glibc}/lib:${pkgs.zlib}/lib:${pkgs.libffi}/lib";
  };
  
  shellHook = ''
    echo "🐍 Setting up Python environment..."
    export PATH="${pkgs.python311Full}/bin:$PATH"
    mkdir -p "$HOME/.local/bin"
    ln -sf ${pkgs.python311Full}/bin/python3 "$HOME/.local/bin/python"
    ln -sf ${pkgs.python311Full}/bin/python3 "$HOME/.local/bin/python3"
    export PATH="$HOME/.local/bin:$PATH"
    echo "✅ Python available at: $(which python3)"
    python3 --version
  '';
}
