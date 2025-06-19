modules = ["python-3.12"]
run = "streamlit run app.py"

[nix]
channel = "stable-24_05"
packages = [
  "glibcLocales",
  "gcc-unwrapped.lib",
  "stdenv.cc.cc.lib",
  "zlib"
]