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


## Step-by-step instructions for Ubuntu 20.04

Starting from a **default Ubuntu 20.04 Desktop installation**

1. update and upgrade all packages (run as root or use `sudo`)
```
apt-get update
apt-get -V upgrade
```
2. install needed software (run as root or use `sudo`)
```
apt-get install python3-setuptools python3-distutils git snapcraft gettext
```
3. install python pip for current user
```
wget https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py
# you may want to add the following to `~/.profile` to make it permanent
export PATH=~/.local/bin/:$PATH
```
4. clone duplicity version to local file system (choose existing tag e.g. "rel.1.2.1")
```
git clone https://gitlab.com/duplicity/duplicity.git -b rel.1.2.1
```
5. change into local git clone folder
```
cd duplicity/
```
6. install needed python modules for duplicity (needed for local builds)
```
python3 -m pip install -r requirements.txt
```
7. setup git user/email (needed for snapcraft remote build)
```
git config --global user.email "your@email.com"
git config --global user.name "Your Name"
```
8. run snap creation script (any non-amd64 target platform will trigger the remote-build)
```
tools/makesnap arm64,amd64,armhf,ppc64el
```
9. the above should result in several duplicity-*.snap files under `build/duplicity-<version>/`, as remote build at times results in truncated snap packages it is a good idea to quickly check if the squash-images are fine.
```
ls -l build/duplicity-1.2.1/*.snap
# example output
#-rw-rw-r-- 1 user user 145268736 Dec 14 06:39 build/duplicity-1.2.1/duplicity_1.2.1_amd64.snap
#-rw-rw-r-- 1 user user 212455424 Dec 14 06:39 build/duplicity-1.2.1/duplicity_1.2.1_arm64.snap
#-rw-rw-r-- 1 user user 208789504 Dec 14 06:38 build/duplicity-1.2.1/duplicity_1.2.1_armhf.snap
#-rw-rw-r-- 1 user user 219574272 Dec 14 06:39 build/duplicity-1.2.1/duplicity_1.2.1_ppc64el.snap
# unsquashfs will print an error in case the image is corrupted
for f in build/duplicity-*/*.snap; do echo $f; unsquashfs -l "$f" > /dev/null; done
```
10. if all went well the snaps can be uploaded to snapcraft
```
# use the `tools/pushsnap` script NEEDS '~/.snaplogin'
tools/pushsnap
# or do it manually
snapcraft login
for f in build/duplicity-*/*.snap; do echo "$f"; snapcraft upload "$f" --release edge; done
```
