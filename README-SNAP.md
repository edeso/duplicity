# Building

Some instructions and hints for building duplicity snaps.

## Prerequisites

1. Must be in a git clone of duplicity
2. Must have all requirements.txt modules available
3. For remote build (non-amd64) you'll need access to Launchpad

## Build Process 

1. cd into clone root
2. Run `tools/makesnap [arm64,amd64,armhf,ppc64el]`
   1. run without args to build amd64 only locally
   2. run with all args to build remotely on LP
3. Run `tools/installsnap` to install to local machine
4. Run `tools/testsnap` to run simple tests
5. Run `tools/pushsnap` to push snap(s) to edge
6. Sign on to [snapcraft.io](https://snapcraft.io/duplicity/releases) to promote snaps if needed

## Notes

1. Running 1 with all args is by far the easiest.
2. Do not remove makesnap's `--destructive-mode`!
   1. it'll try to use `Multipass` and fail miserably
   2. if it should run, it'll interfere with other VMs
   3. use a Ubuntu 20.04 VM or Docker image (core20)
