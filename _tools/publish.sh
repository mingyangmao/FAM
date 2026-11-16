#!/usr/bin/env bash
# Publish docs/ to the public GitHub Pages repo mingyangmao/FAM.
#
#     bash docs/_tools/publish.sh "Update results table"
#
# Commits docs/ in this repo under the site account's GitHub no-reply address,
# so the email in the local git config is not published with the page, then
# pushes the docs/ subtree to the site repo's main branch.
#
# Commit docs/ changes only through this script: `git subtree push` republishes
# every commit that touches docs/, with its author, committer and message.
set -euo pipefail

SITE_REPO=git@github.com:mingyangmao/FAM.git
SITE_NAME=mingyangmao
SITE_EMAIL=160159704+mingyangmao@users.noreply.github.com

cd "$(git rev-parse --show-toplevel)"
git add docs
if git diff --cached --quiet -- docs; then
  echo "docs/ has no new changes; pushing what is already committed"
else
  git -c user.name="$SITE_NAME" -c user.email="$SITE_EMAIL" \
    commit -m "${1:-Update project page}" -- docs
fi
git subtree push --prefix docs "$SITE_REPO" main
