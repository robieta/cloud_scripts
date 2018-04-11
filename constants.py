# Copyright 2018 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import os
import sys

if sys.version_info[0] != 3:
  print("Use Python3.")
  sys.exit(255)

try:
  import gcloud
except:
  print("please install gcloud: 'sudo pip3 install -r requirements.txt'")
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
