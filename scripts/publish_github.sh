#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
target="${1:-zhai-yuan/quant-research-cloud}"
[[ "$target" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || exit 2
command -v gh >/dev/null || { echo 'Install GitHub CLI and run gh auth login --hostname github.com --scopes workflow first.' >&2; exit 1; }
gh auth status --hostname github.com
gh auth setup-git
if [[ ! -d .git ]]; then
  git init -b main
  git add .
  git -c user.name='Quant research setup' -c user.email='quant-research@users.noreply.github.com' commit -m 'Configure A-share quant research environment'
fi
if gh repo view "$target" >/dev/null 2>&1; then
  remote_head="$(git ls-remote "https://github.com/$target.git" HEAD)"
  if [[ -n "$remote_head" ]]; then
    echo 'Repository already contains commits. Use a normal review and merge workflow; refusing to overwrite.' >&2
    exit 1
  fi
  if git remote get-url origin >/dev/null 2>&1; then
    [[ "$(git remote get-url origin)" == "https://github.com/$target.git" ]] || { echo 'Unexpected origin; refusing to change it.' >&2; exit 1; }
  else
    git remote add origin "https://github.com/$target.git"
  fi
  gh auth setup-git
  git push -u origin main
else
  gh repo create "$target" --private --source . --remote origin --push
fi
