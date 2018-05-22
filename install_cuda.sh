if lspci | grep -i nvidia; then
  # Install drivers
  apt-get purge nvidia*
  add-apt-repository ppa:graphics-drivers -y
  apt-get update
  apt-get install nvidia-384 -y

  # Check for CUDA and try to install.
  if ! dpkg-query -W cuda; then
    # The 16.04 installer works with 16.10.
    curl -O http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/cuda-repo-ubuntu1604_9.0.176-1_amd64.deb
    dpkg -i ./cuda-repo-ubuntu1604_9.0.176-1_amd64.deb
   curl -O https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/7fa2af80.pub
    apt-key add 7fa2af80.pub
    apt-get update
    apt-get install cuda=9.0.176-1 -y
  fi
  apt-get install -y nvidia-cuda-toolkit

  # Install corresponding cuDNN
  if ! ls /usr/local/cuda/lib64 | grep cudnn; then
    wget http://developer.download.nvidia.com/compute/redist/cudnn/v7.0.5/cudnn-9.0-linux-x64-v7.tgz
    tar -xvzf cudnn-9.0-linux-x64-v7.tgz
    cp cuda/include/cudnn.h /usr/local/cuda/include
    cp cuda/lib64/libcudnn* /usr/local/cuda/lib64
    chmod a+r /usr/local/cuda/include/cudnn.h /usr/local/cuda/lib64/libcudnn*
  fi
fi
