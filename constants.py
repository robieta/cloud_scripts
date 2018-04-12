
import os
import sys

if sys.version_info[0] != 3:
  print("Use Python3.")
  sys.exit(255)

ACCOUNT = "814778702491-compute@developer.gserviceaccount.com"
USER = os.getlogin()
GCLOUD = "/usr/bin/gcloud"
SANDBOX_TEMPLATE = "{user}-sandbox-{id}"

ROOT = os.path.dirname(os.path.abspath(__file__))


# Projects are given terse letter assignments to allow concise CLI commands
PROJECTS = {
  "a": "tensorflow-onboarding",
  "b": "tensorflow-performance",
  "c": "ctpu-2017-09-01",
}

ZONES = {
  "tensorflow-onboarding":  "us-central1-c",
  "tensorflow-performance": "us-west1-b",
  "ctpu-2017-09-01":        "us-central1-c",
}
