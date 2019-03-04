#!/usr/bin/env bash
set -e

sudo apt-get install build-essential dkms
sudo apt-get install freeglut3 freeglut3-dev libxi-dev libxmu-dev

if lspci | grep -i nvidia; then
  # Install drivers
  apt-get purge nvidia*
  add-apt-repository ppa:graphics-drivers -y
  apt-get update
  apt-get install nvidia-410 -y

  wget https://developer.nvidia.com/compute/cuda/10.0/Prod/local_installers/cuda-repo-ubuntu1604-10-0-local-10.0.130-410.48_1.0-1_amd64
  gsutil cp gs://garden-team-scripts/nccl-repo-ubuntu1604-2.3.7-ga-cuda10.0_1-1_amd64.deb .
  gsutil cp gs://garden-team-scripts/cudnn-10.0-linux-x64-v7.4.2.24.tgz .
  sudo dpkg -i cuda-repo-ubuntu1604-10-0-local-10.0.130-410.48_1.0-1_amd64
  sudo dpkg -i nccl-repo-ubuntu1604-2.3.7-ga-cuda10.0_1-1_amd64.deb
  sudo apt-key add /var/cuda-repo-10-0-local-10.0.130-410.48/7fa2af80.pub
  sudo apt-get update

  sudo apt install cuda
  sudo apt install libnccl2=2.3.7-1+cuda10.0

  ln -s /usr/local/cuda-10.0 /usr/local/cuda

  tar -xzvf cudnn-10.0-linux-x64-v7.4.2.24.tgz
  sudo cp cuda/include/cudnn.h /usr/local/cuda/include
  sudo cp cuda/lib64/libcudnn* /usr/local/cuda/lib64
  sudo chmod a+r /usr/local/cuda/include/cudnn.h /usr/local/cuda/lib64/libcudnn*
fi

ln -s /usr/local/cuda-10.0 /usr/local/cuda
