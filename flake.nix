{
  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config = {
            allowUnfree = true;
            cudaSupport = true;
            cudnnSupoprt = true;
          };
        };
        twitchio = pkgs.python3Packages.buildPythonPackage rec {
          pname = "twitchio";
          version = "3.0.1";
          src = pkgs.fetchPypi {
            inherit pname version;
            hash = "sha256-ThQE1wn/7zYtNMOtCWVWuDY+dlr1jgwzpHZvHlU3vZw=";
          };
          dependencies = [ pkgs.python3Packages.aiohttp ];
          pythonImportsCheck = [ "twitchio" ];
          build-system = [ pkgs.python3Packages.setuptools ];
          pyproject = true;
        };
        pythonDeps = p: [
          twitchio
        ];
      in
      {
        devShell = pkgs.mkShell {
          buildInputs = [
            (pkgs.python3.withPackages pythonDeps)
          ];
        };
      }
    );
  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };
}
