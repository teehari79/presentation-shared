#!/usr/bin/env bash
set -euo pipefail

while IFS= read -r file; do
  ruby -e "require 'yaml'; YAML.load_file('$file')" >/dev/null
  echo "valid yaml: $file"
done < <(find . -type f -name '*.yaml' -not -path './.git/*' | sort)
