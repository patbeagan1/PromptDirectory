#!/usr/bin/env zsh

set -euo pipefail

rm -r dist
threeflow -r rs
uv version --bump minor
git commit -am "updating version"
uv build
uv publish
threeflow -r rf

