# Merge verification checklist

Use this checklist to confirm whether local changes were merged or remain pending before proceeding with new work.

## 1. Sync remote references
```
git fetch --all --prune
```
Fetches the latest branches and removes stale remote refs so comparisons are accurate.

## 2. Verify clean working tree
```
git status -sb
```
Ensures there are no local modifications hiding uncommitted changes.

## 3. Compare local HEAD to the target branch
```
git log --oneline origin/main..HEAD
```
Lists commits present locally but not on the remote target branch. If output is empty, your HEAD matches the remote.

## 4. Inspect diff vs remote (optional)
```
git diff origin/main...HEAD
```
Shows file-level differences if you need to review changes before merging.

## 5. Confirm last commit details
```
git show --stat --oneline HEAD
```
Summarizes the most recent commit and touched files for quick verification.

## 6. Document findings
If a merge is pending, add a brief note to your work log or issue comment with the commit hashes waiting to be merged.
