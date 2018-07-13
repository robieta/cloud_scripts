
import argparse
import datetime
import os
import subprocess
import sys
import time

import googleapiclient.discovery

import constants

COMPUTE = googleapiclient.discovery.build('compute', 'v1')


def now():
  return datetime.datetime.utcnow().strftime("%H:%M:%S")

class ShowTime:
  def __init__(self, description, show_elapsed=False):
    self.desc = description
    self.show_elapsed = show_elapsed

  def __enter__(self):
    self.start_time = time.time()  # timeit.default_timer is overkill.
    print("[START] {}  {}".format(now(), self.desc))

  def __exit__(self, exc_type, exc_val, exc_tb):
    print("[END]   {}  {}".format(now(), self.desc))
    if self.show_elapsed:
      print("  Elapsed time: {:0.1f} second(s)".format(time.time() - self.start_time))
    print()


def run(args, silent=False):
  p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
  output, err = p.communicate()
  rc = p.returncode
  if rc != 0:
    if not silent:
      print("Stdout:")
      print(output.decode("utf-8"))
      print("\nStderr")
      print(err.decode("utf-8"))
    raise OSError("Cmd failed")

  return output.decode("utf-8")


def ssh_cmd(cmd: list, instance: str, zone: str, project: str, max_attempts=1,
    backoff=0.5, description=None):
  usr_host = "{user}@{instance}".format(
      user=constants.USER,
      instance=instance,
  )
  command = [constants.GCLOUD, "compute", "ssh", usr_host, "--zone", zone,
             "--project", project, "--command", " ".join(cmd)]
  for i in range(max_attempts):
    final = (i+1) == max_attempts
    try:
      return run(command, silent=(not final))
    except OSError:
      if final:
        raise
      print("Command failed. Retrying with backoff")
      time.sleep(backoff * 2**i)
      continue


def scp_file(local_path, remote_path, instance, zone, project, chmod=None):
  cmd = [constants.GCLOUD, "compute", "scp", local_path,
         "{}:{}".format(instance, remote_path), "--zone", zone, "--project", project]
  print("Transfering file {} to {}:{}".format(local_path, instance, remote_path))
  run(cmd)
  if chmod:
    print("Setting chmod to {}".format(chmod))
    ssh_cmd(["sudo", "chmod", chmod, remote_path], instance=instance, zone=zone,
            project=project)


def calc_num_cpus(num_cpu, num_k80, num_p100, num_v100):
  if num_k80:
    return num_k80 * 8
  if num_p100:
    return num_p100 * 16
  if num_v100:
    return num_v100 * 12

  assert 1 <= num_cpu <= 96
  assert num_cpu % 8 == 0
  return num_cpu


def get_zone(project, num_k80, num_p100, num_v100):
  # TODO: make more permissive if necessary
  if num_k80:
    zone = "us-central1-c"
  elif num_p100:
    zone = "us-central1-c"
  elif num_v100:
    zone = "us-central1-f"
  else:
    zone = constants.ZONES[project][0]
  assert zone in constants.ZONES[project]
  return zone



def list_instances(project):
  output = []
  for zone in constants.ZONES[project]:
    result = COMPUTE.instances().list(
        project=project, zone=zone).execute()
    if "items" not in result:
      continue
    output.extend([i["name"] for i in result["items"]])
  return output


def list_disks(project):
  output = []
  for zone in constants.ZONES[project]:
    result = COMPUTE.disks().list(
        project=project, zone=zone).execute()
    if "items" not in result:
      continue
    output.extend([i["name"] for i in result["items"]])
  return output


def get_new_instance_name(project):
  instances = list_instances(project)
  disks = list_disks(project)
  for i in range(10000):
    name = constants.populate_template(user=constants.USER, id=i)
    if name not in instances and name not in disks:
      return name
  raise NameError("How? ...just how?")


def get_accellerator_spec(num_k80, num_p100, num_v100):
  if num_k80:
    return ["--accelerator", "type=nvidia-tesla-k80,count={}".format(num_k80)]
  if num_p100:
    return ["--accelerator", "type=nvidia-tesla-p100,count={}".format(num_p100)]
  if num_v100:
    return ["--accelerator", "type=nvidia-tesla-v100,count={}".format(num_v100)]
  return []


def make_instance(project, name, zone, machine_type, min_cpu_platform, accellerator_spec, rebuild):
  if rebuild and project not in constants.SNAPSHOTS:
    print("No snapshot present. rebuild set to True.")
    rebuild = True

  if rebuild or not accellerator_spec:
    boot_disk_spec = [
      "--image", "ubuntu-1604-lts-drawfork-v20180423",
      "--image-project", "eip-images",
      "--boot-disk-size", "200GB",
      "--boot-disk-type", "pd-standard",
      "--boot-disk-device-name", name,
    ]
  else:
    disk_cmd = [constants.GCLOUD, "compute",
                "--project", project,
                "disks", "create", name,
                "--size", "200GB",
                "--zone", zone,
                "--source-snapshot", constants.SNAPSHOTS[project],
                "--type", "pd-standard"]
    with ShowTime("Creating boot disk from snapshot", show_elapsed=True):
      run(disk_cmd)

    boot_disk_spec = [
      "--disk", ("name={name},device-name={dev_name},mode=rw,boot=yes,"
                 "auto-delete=yes").format(name=name, dev_name=name)
    ]

  inst_cmd = [
      constants.GCLOUD, "beta", "compute", "--project", project,
      "instances", "create", name,
      "--zone",  zone,
      "--machine-type", machine_type,
      "--subnet", "default",
      "--maintenance-policy", "TERMINATE",
      "--network-tier", "PREMIUM",
      "--no-restart-on-failure",
      "--service-account", constants.ACCOUNT[project],
      "--scopes", "https://www.googleapis.com/auth/cloud-platform"] + \
      accellerator_spec + \
      ["--min-cpu-platform", min_cpu_platform,
      "--tags", 'http-server,https-server'] + \
      boot_disk_spec

  inst_cmd_pretty = " ".join(inst_cmd).replace("--", "\n  --")
  with ShowTime("Creating instance", show_elapsed=True):
    print(inst_cmd_pretty)
    print()

    run(args=inst_cmd)

  # Give the instance a moment to come up
  with ShowTime("Establishing SSH connection"):
    ssh_cmd(cmd=["echo", "a"], instance=name, zone=zone,
            project=namespace.project, max_attempts=8, backoff=4)

  if accellerator_spec:
    if rebuild:
      with ShowTime("Installing CUDA and CudNN", show_elapsed=True):
        scp_file(local_path="install_cuda.sh", remote_path="/tmp/install_cuda.sh",
                 instance=name, zone=zone, project=project, chmod="777")
        input("install script is on remote. Best of luck...")
        # # This is sufficiently rare and very finicky, so I just run the script
        # # on remote manually.

        # print("Running install_cuda.sh on remote. (This will take a few moments.)")
        # ssh_cmd(["sudo", "/tmp/install_cuda.sh"], instance=name, zone=zone, project=project)
  else:
    if rebuild:
      print("No GPUs specified. CUDA will not be installed.")


def make_data_disk(project, name, zone):
  disks = list_disks(project)
  data_disk_name = ""
  for i in range(10000):
    data_disk_name = "{}-data-disk-{}".format(name, i)
    if data_disk_name in disks:
      continue
    break
  data_disk_cmd = [constants.GCLOUD, "compute",
                   "--project", project,
                   "disks", "create", data_disk_name,
                   "--size", "100GB",
                   "--zone", zone,
                   "--type", "pd-standard"]
  data_disk_cmd_pretty = " ".join(data_disk_cmd).replace("--", "\n  --")
  with ShowTime("Creating data disk", show_elapsed=True):
    print(data_disk_cmd_pretty)
    run(data_disk_cmd)

  data_attach_cmd = [constants.GCLOUD, "compute", "instances", "attach-disk", name,
                     "--disk", data_disk_name, "--mode", "rw", "--zone", zone]
  with ShowTime("Attaching data disk to instance"):
    run(data_attach_cmd)

  with ShowTime("Creating mount point"):
    ssh_cmd(cmd=["sudo", "mkdir", "-p", "/data"], instance=name, zone=zone,
            project=project, max_attempts=3)

  with ShowTime("Formatting data disk"):
    ssh_cmd(["sudo", "mkfs.ext4", "-F", "/dev/sdb"],
            instance=name, zone=zone, project=project, max_attempts=3)

  with ShowTime("Adding to fstab"):
    ssh_cmd(["echo", "'/dev/sdb /data ext4 discard,defaults 0 2'", "|", "sudo", "tee", "--append", "/etc/fstab"],
            instance=name, zone=zone, project=project, max_attempts=1)

  with ShowTime("Mounting disk"):
    ssh_cmd(["sudo", "mount", "-a"], instance=name, zone=zone, project=project,
            max_attempts=3)

  with ShowTime("Setting permissions"):
    ssh_cmd(cmd=["sudo", "chmod", "777", "/data"], instance=name, zone=zone,
            project=project, max_attempts=3)


def attach_imagenet(project, name, zone, data_disk):
  imn_dev = "/dev/sdc" if data_disk else "/dev/sdb"
  imagenet_attach_cmd = [constants.GCLOUD, "compute", "instances", "attach-disk", name,
                         "--disk", constants.IMAGENET[project][zone], "--mode", "ro", "--zone", zone]
  with ShowTime("Attaching ImageNet disk to instance"):
    run(imagenet_attach_cmd)

  with ShowTime("Creating moint point /imn for ImageNet disk"):
    ssh_cmd(cmd=["sudo", "mkdir", "-p", "/imn"], instance=name, zone=zone,
            project=project, max_attempts=3)

  with ShowTime("Adding disk to fstab"):
    ssh_cmd(["echo", "'{} /imn ext4 discard,defaults,norecovery 0 2'".format(imn_dev),
             "|", "sudo", "tee", "--append", "/etc/fstab"],
            instance=name, zone=zone, project=project, max_attempts=1)

  with ShowTime("Mounting disk"):
    ssh_cmd(["sudo", "mount", "-a"], instance=name, zone=zone, project=project,
            max_attempts=3)


def open_http(project, zone):
  http_cmd = [constants.GCLOUD, "compute", "--project", project, "firewall-rules",
              "create", "default-allow-http", "--network=default",
              "--action=ALLOW", "--rules=tcp:80", "--source-ranges=0.0.0.0/0",
              "--target-tags=http-server"]

  https_cmd = [constants.GCLOUD, "compute", "--project", project, "firewall-rules",
               "create", "default-allow-https", "--network=default",
               "--action=ALLOW", "--rules=tcp:443", "--source-ranges=0.0.0.0/0",
               "--target-tags=https-server"]

  try:
    with ShowTime("Opening HTTP and HTTPS"):
      run(http_cmd)
      print("  HTTP opened.")
      run(https_cmd)
      print("  HTTPS opened.")
  except:
    print("Skipping HTTP/HTTPS.")


def configure_new_instance(instance: str, zone: str, project: str, gpu_present: bool):
  """
  Very much work in progress. Apt can be finicky, so backoff is used.
  """
  with ShowTime("Beginning apt installs", show_elapsed=True):
    print("  (Retries are expected due to locking.)")

    # Needed by cloud TPU profile tool.
    ssh_cmd(cmd=[
      "sudo", "add-apt-repository", "-y", "ppa:ubuntu-toolchain-r/test", "&&",
      "sudo", "apt-get", "update", "&&", "sudo", "apt-get", "install", "-y",
      "gcc-4.9", "&&", "sudo", "apt-get", "upgrade", "-y", "libstdc++6"],
            instance=instance,
            zone=zone,
            project=project,
            max_attempts=10,
            backoff=4,
            )

    ssh_cmd(cmd=["sudo", "apt-get", "install", "-y", "python-pip", "python3-pip",
                 "virtualenv", "htop", "iotop"],
            instance=instance,
            zone=zone,
            project=project,
            max_attempts=10,
            backoff=4,
            )

  with ShowTime("Upgrading PIP"):
    ssh_cmd(["sudo", "pip", "install", "--upgrade", "pip", "setuptools"],
            instance=instance, zone=zone, project=project, max_attempts=3)

    ssh_cmd(["sudo", "pip3", "install", "--upgrade", "pip", "setuptools"],
            instance=instance, zone=zone, project=project, max_attempts=3)

  with ShowTime("Cloning Garden"):
    ssh_cmd(cmd=["mkdir", "-p", "TensorFlow", "&&", "cd", "TensorFlow", "&&", "git",
                 "clone", "https://github.com/tensorflow/models.git"], instance=instance,
            zone=zone, project=project, max_attempts=3)

  with ShowTime("Setting environment vars."):
    export0 = ("export LD_LIBRARY_PATH=/usr/local/cuda/lib64:"
               "/usr/local/cuda/extras/CUPTI/lib64\n")
    export1 = "export garden_bucket=\"gs://garden-team-scripts\"\n"
    ssh_cmd(cmd=["mkdir", "-p", "~/.cloud", "&&",
                 "printf", "'" + export0 + "'", ">", constants.PROFILE, "&&",
                 "printf", "'" + export1 + "'", ">>", constants.PROFILE],
            instance=instance, zone=zone, project=project, max_attempts=3)

  with ShowTime("Creating virtualenvs (~/envs)"):
    ssh_cmd(cmd=["mkdir", "~/envs", "&&", "mkdir", "~/envs/py2_garden", "&&",
                 "mkdir", "~/envs/py3_garden"], instance=instance, zone=zone,
            project=project, max_attempts=3)

    ssh_cmd(cmd=["virtualenv", "--system-site-packages", "~/envs/py2_garden"],
            instance=instance, zone=zone, project=project, max_attempts=3)
    ssh_cmd(cmd=["virtualenv", "--system-site-packages", "-p", "python3",
                 "~/envs/py3_garden"],
          instance=instance, zone=zone, project=project, max_attempts=3)

  nightly = "tf-nightly-gpu" if gpu_present else "tf-nightly"
  python_pkgs = ["numpy", "scipy", "sklearn", nightly]
  install_requirements = ["pip", "install", "-r", "~/TensorFlow/models/official/requirements.txt"]

  with ShowTime("Installing Python2 virtualenv"):
    ssh_cmd(cmd=["source", "~/envs/py2_garden/bin/activate", "&&",
                 "pip", "install", "--upgrade"] + ["setuptools"] + python_pkgs +
                ["&&"] + install_requirements,
            instance=instance, zone=zone, project=project, max_attempts=3)

  with ShowTime("Install Python3 virtualenv"):
    ssh_cmd(cmd=["source", "~/envs/py3_garden/bin/activate", "&&",
                 "pip", "install", "setuptools==39.1.0", "&&", # 39.2.0 is buggy in py3.
                 "pip", "install", "--upgrade"] + python_pkgs + ["&&"] + install_requirements,
            instance=instance, zone=zone, project=project, max_attempts=3)

  with ShowTime("Adding cloud profile to .bashrc"):
    ssh_cmd(cmd=["printf", '"\nsource ~/.cloud/.profile\n"', ">>", "~/.bashrc"],
            instance=instance, zone=zone, project=project, max_attempts=3)

  with ShowTime("Disabling automatic restart for unattended-upgrades"):
    # I am extremely angry that this was on by default.
    ssh_cmd(cmd=["printf", '"\nUnattended-Upgrade::Automatic-Reboot \"false\";\n"', "|",
                 "sudo", "tee", "-a", "/etc/apt/apt.conf.d/50unattended-upgrades"],
            instance=instance, zone=zone, project=project, max_attempts=3)

  if constants.USER in os.listdir("user_config"):
    for i in os.listdir(os.path.join("user_config", constants.USER)):
      local_path = os.path.join("user_config", constants.USER, i)
      scp_file(local_path=local_path, remote_path=i, instance=instance,
               zone=zone, project=project)


def restart_instance(instance, zone):
  with ShowTime("Restarting instance (Needed to properly load drivers)"):
    run([constants.GCLOUD, "compute", "instances", "stop", instance, "--zone", zone])
    run([constants.GCLOUD, "compute", "instances", "start", instance, "--zone", zone])


def make(namespace):
  name = get_new_instance_name(namespace.project)
  print("Name:", name)
  num_cpu = calc_num_cpus(num_cpu=namespace.cpus, num_k80=namespace.k80,
                          num_p100=namespace.p100, num_v100=namespace.v100)
  min_cpu_platform = "Automatic" if num_cpu <= 64 else "skylake"
  zone = get_zone(project=namespace.project, num_k80=namespace.k80,
                  num_p100=namespace.p100, num_v100=namespace.v100)
  machine_type = "n1-standard-{}".format(num_cpu)
  if num_cpu == 12:
    machine_type = "custom-12-46080"  # 1 V100 case
  accellerator_spec = get_accellerator_spec(
      num_k80=namespace.k80, num_p100=namespace.p100, num_v100=namespace.v100)
  if num_cpu != namespace.cpus:
    print("Overriding cpus to {}".format(num_cpu))
  if namespace.imagenet:
    assert namespace.project in constants.IMAGENET
    assert zone in constants.IMAGENET[namespace.project]

  assert namespace.project in constants.ACCOUNT
  make_instance(project=namespace.project, name=name, zone=zone,
                machine_type=machine_type, min_cpu_platform=min_cpu_platform,
                accellerator_spec=accellerator_spec, rebuild=namespace.rebuild)

  if not namespace.no_data_disk:
    make_data_disk(project=namespace.project, name=name, zone=zone)
  if namespace.imagenet:
    attach_imagenet(project=namespace.project, name=name, zone=zone,
                    data_disk=not namespace.no_data_disk)

  if namespace.project == "tensorflow-onboarding":
    open_http(project=namespace.project, zone=zone)
  configure_new_instance(instance=name, zone=zone, project=namespace.project,
                         gpu_present=bool(accellerator_spec))

  restart_instance(instance=name, zone=zone)

  print("\n\n", "="*50, "\n", "==== {} ".format(name).ljust(50, "="), "\n", "="*50)


def list(namespace):
  raise NotImplementedError


def construct_parser():
  def add_project(parser):
    project_string = "\n".join(
        ["  {}: {}".format(key, val) for key, val in sorted(constants.PROJECTS.items())])
    parser.add_argument(
        "--project", "-p", default="a", choices=sorted(constants.PROJECTS.keys()),
        help="[default: %(default)s] Options:\n{}".format(project_string),
        metavar="<P>"
    )

  formatter = argparse.RawTextHelpFormatter
  parser = argparse.ArgumentParser(formatter_class=formatter)

  subparser = parser.add_subparsers(help="")
  make_parser = subparser.add_parser("make", help="Construct GCE sandbox.",
                                     formatter_class=formatter)
  list_parser = subparser.add_parser("list", help="List current sandboxes. (Not implemented yet.)",
                                     formatter_class=formatter)

  make_parser.set_defaults(func=make)
  list_parser.set_defaults(func=list)

  [add_project(p) for p in [make_parser, list_parser]]

  make_parser.add_argument("--cpus", "-c", type=int, default=8,
                           help="[default: %(default)s] Number of CPUs. This "
                                "can be overwritten if GPUs are specified.",
                           metavar="<C>")\

  gpu_group = make_parser.add_mutually_exclusive_group()
  gpu_group.add_argument(
      "--v100", "-v100", type=int, default=0,
      choices=[1, 8],
      help="[default: %(default)s] Number of V100s. {1, 8}", metavar="<P>"
  )

  gpu_group.add_argument(
      "--p100", "-p100", type=int, default=0,
      choices=[1, 2, 4],
      help="[default: %(default)s] Number of P100s. (Max 4)", metavar="<P>"
  )
  gpu_group.add_argument(
      "--k80", "-k80", type=int, default=0,
      choices=[1, 2, 4, 8],
      help="[default: %(default)s] Number of K80s. (Max 8)", metavar="<K>"
  )
  make_parser.add_argument(
      "--imagenet", "-imn", action="store_true",
      help="Attach the ImageNet drive to this instance."
  )
  make_parser.add_argument(
      "--no_data_disk", "-ndd", action="store_true",
      help="Do not create a secondary volume for data. "
           "Set this flag for trivial instances."
  )
  make_parser.add_argument(
      "--rebuild", action="store_true",
      help="Create from scratch rather than starting from a snapshot. "
           "Unnecessary if GPUs are not used."
  )

  return parser

if __name__ == "__main__":
  parser = construct_parser()
  argv = sys.argv[1:]
  if len(argv) <= 1:
    argv.append("-h")
  namespace = parser.parse_args(argv)
  namespace.project = constants.PROJECTS[namespace.project]
  namespace.func(namespace)
