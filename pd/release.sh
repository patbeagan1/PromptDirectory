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

if [ -f dist ]; then
  rm -r dist
fi

function main() {
  threeflow -r rs
  uv version --bump minor
  git commit -am "updating version"
  uv build
  uv publish
  threeflow -r rf
}

main
