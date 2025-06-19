
modules = ["python-3.12"]
run = "streamlit run app.py"

[nix]
channel = "stable-24_05"
packages = [
  "glibcLocales",
  "gcc-unwrapped.lib",
  "stdenv.cc.cc.lib",
  "glibc",
  "libgcc",
  "zlib"
]

[env]
LD_LIBRARY_PATH = "/nix/store/*-gcc-*/lib:/nix/store/*-glibc-*/lib:/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
PYTHONPATH = "$PYTHONPATH"
