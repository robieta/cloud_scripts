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

import re
import sys

from constants import USER, GCLOUD, PROJECTS, ZONES, SANDBOX_TEMPLATE

project_string = "\n".join(
    ["  {}: {}".format(key, val) for key, val in sorted(PROJECTS.items())])

HELP_TEXT = "Convenience function for ssh-ing into cloud instances.\n\n" \
            "Projects:\n{}".format(project_string)

def main():
  args = sys.argv[1:]
  if len(args) == 0:
    print(HELP_TEXT)
    sys.exit(1)

  machine_id = args[0]
  project = None
  for i in sorted(PROJECTS.keys()):
    if machine_id.endswith(i):
      project = PROJECTS[i]
      machine_id = re.sub(i+"$", "", machine_id)
      break
  project = project or PROJECTS["a"]

  if not re.search(r"^[0-9]+$", machine_id):
    print("Invalid machine id.")
    sys.exit(255)

  zone = ZONES[project]

  ssh_cmd = ("{gcloud} compute --project {project} ssh "
             "{user}-sandbox-{machine_id} --zone {zone}".format(
      gcloud=GCLOUD, project=project, user=USER, machine_id=machine_id, zone=zone
  ))
  print(ssh_cmd)
  sys.exit()


if __name__ == "__main__":
  main()
