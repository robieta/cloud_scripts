
import os
import sys

if sys.version_info[0] != 3:
  print("Use Python3.")
  sys.exit(255)

ACCOUNT = {
  "tensorflow-onboarding": "814778702491-compute@developer.gserviceaccount.com",
  "google.com:tensorflow-performance": "283123161091-compute@developer.gserviceaccount.com",
  "ctpu-2017-09-01": "855031184363-compute@developer.gserviceaccount.com",
}

USER = os.getlogin()
if USER != os.getenv("USER"):
  env_user = os.getenv("USER")
  print("Overriding user {} to {}".format(USER, env_user))
  USER = env_user

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
  "b": "google.com:tensorflow-performance",
  "c": "ctpu-2017-09-01",
}

ZONES = {
  "tensorflow-onboarding":             ["us-central1-c", "us-central1-f", "us-central1-a", "us-central1-b"],
  "google.com:tensorflow-performance": ["us-west1-b"],
  "ctpu-2017-09-01":                   ["us-central1-c"],
}

REZONE = {
  "tensorflow-onboarding": True,
  "google.com:tensorflow-performance": False,
  "ctpu-2017-09-01": False,
}

SNAPSHOTS = {
  "tensorflow-onboarding": "ubuntu-1604-lts-drawfork-with-cuda-20180921",
  "google.com:tensorflow-performance": "ubuntu-1604-lts-drawfork-with-cuda-20180924",
}

IMAGENET = {
  "tensorflow-onboarding": {"us-central1-a": "imagenet-copy-1a",
                            "us-central1-b": "imagenet-copy-1b",
                            "us-central1-c": "imagenet-copy-1c",
                            "us-central1-f": "imagenet-copy-1f"},
}
