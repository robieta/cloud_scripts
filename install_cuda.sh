#!/usr/bin/env bash
set -e

if lspci | grep -i nvidia; then
  # Install drivers
  apt-get purge nvidia*
  add-apt-repository ppa:graphics-drivers -y
  apt-get update
  apt-get install nvidia-396 -y

  # Check for CUDA and try to install.
  if ! dpkg-query -W cuda; then
    sudo apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/7fa2af80.pub
    wget http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/cuda-repo-ubuntu1604_9.1.85-1_amd64.deb
    wget http://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1604/x86_64/nvidia-machine-learning-repo-ubuntu1604_1.0.0-1_amd64.deb
    sudo dpkg -i cuda-repo-ubuntu1604_9.1.85-1_amd64.deb
    sudo dpkg -i nvidia-machine-learning-repo-ubuntu1604_1.0.0-1_amd64.deb
    sudo apt-get update
    # Includes optional NCCL 2.x.
    sudo apt-get install cuda9.0 cuda-cublas-9-0 cuda-cufft-9-0 cuda-curand-9-0 \
      cuda-cusolver-9-0 cuda-cusparse-9-0 libcudnn7=7.2.1.38-1+cuda9.0 \
       libnccl2=2.2.13-1+cuda9.0 cuda-command-line-tools-9-0
    # Optionally install TensorRT runtime, must be done after above cuda install.
    sudo apt-get update
    sudo apt-get install libnvinfer4=4.1.2-1+cuda9.0

#    # The 16.04 installer works with 16.10.
#    curl -O http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/cuda-repo-ubuntu1604_9.0.176-1_amd64.deb
#    dpkg -i ./cuda-repo-ubuntu1604_9.0.176-1_amd64.deb
#   curl -O https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/7fa2af80.pub
#    apt-key add 7fa2af80.pub
#    apt-get update
#    apt-get install cuda=9.0.176-1 -y
  fi
  apt-get install -y nvidia-cuda-toolkit

#  # Install corresponding cuDNN
#  if ! ls /usr/local/cuda/lib64 | grep cudnn; then
#    wget http://developer.download.nvidia.com/compute/redist/cudnn/v7.0.5/cudnn-9.0-linux-x64-v7.tgz
#    tar -xvzf cudnn-9.0-linux-x64-v7.tgz
#    cp cuda/include/cudnn.h /usr/local/cuda/include
#    cp cuda/lib64/libcudnn* /usr/local/cuda/lib64
#    chmod a+r /usr/local/cuda/include/cudnn.h /usr/local/cuda/lib64/libcudnn*
#  fi
fi

ln -s /usr/local/cuda-9.0 /usr/local/cuda
