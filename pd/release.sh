#!/usr/bin/env zsh

set -euo pipefail

if ! [ "$(command -v threeflow)" ]; then
  echo "Threeflow is not installed"
  echo "Please install it with"
  echo "- cargo install threeflow"
  exit 1
fi

if [[ -n $(git status --porcelain 2>/dev/null) ]]; then
  echo "You have uncommitted changes."
  return 1
fi

if [ -d dist ]; then
  rm -r dist
fi

if [ -z "$PYPI_TOKEN" ]; then
  echo "Please set token"
fi

function main() {
  threeflow -r rs
  uv version --bump minor
  git commit -am "updating version"
  uv build
  uv publish --username __token__ --password "$PYPI_TOKEN"
  threeflow -r rf
}

main
