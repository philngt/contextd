#!/usr/bin/env bash
# Hook that doesn't use set -e and has no trap.
echo "running"
cp /nonexistent /tmp/x
echo "still running even after failure"
