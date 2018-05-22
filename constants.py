
import os
import sys

if sys.version_info[0] != 3:
  print("Use Python3.")
  sys.exit(255)

ACCOUNT = {
  "tensorflow-onboarding": "814778702491-compute@developer.gserviceaccount.com",
  "ctpu-2017-09-01": "855031184363-compute@developer.gserviceaccount.com",
}
USER = os.getlogin()
PROFILE = "~/.cloud/.profile"
GCLOUD = "/usr/bin/gcloud"
SANDBOX_TEMPLATE = "{user}-sandbox-{id}"

def populate_template(user, id):
  id_str = str(id).zfill(3)
  return SANDBOX_TEMPLATE.format(user=user, id=id_str)

ROOT = os.path.dirname(os.path.abspath(__file__))


# Projects are given terse letter assignments to allow concise CLI commands
PROJECTS = {
  "a": "tensorflow-onboarding",
  "b": "tensorflow-performance",
  "c": "ctpu-2017-09-01",
}

ZONES = {
  "tensorflow-onboarding":  ["us-central1-c", "us-central1-f"],
  "tensorflow-performance": ["us-west1-b"],
  "ctpu-2017-09-01":        ["us-central1-c"],
}

SNAPSHOTS = {
  "tensorflow-onboarding": "ubuntu-1604-lts-drawfork-with-cuda-20180521",
}

IMAGENET = {
  "tensorflow-onboarding": {"us-central1-c": "imagenet-copy-1c",
                            "us-central1-f": "imagenet-copy-1f"},
}
