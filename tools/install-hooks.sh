#!/bin/sh
# Install the repository's pre-push hook into .git/hooks and pin this clone's commit identity to the
# GitHub noreply address, so a personal address cannot reach this public repository again.
repo="$(git rev-parse --show-toplevel)" || exit 1
cp "$repo/tools/hooks/pre-push" "$repo/.git/hooks/pre-push"
chmod +x "$repo/.git/hooks/pre-push"
git -C "$repo" config --local user.email "70870645+SamuelJWebber@users.noreply.github.com"
git -C "$repo" config --local user.name "SamuelJWebber"
echo "pre-push hook installed; local identity set to the noreply address"
