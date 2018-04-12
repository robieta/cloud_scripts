
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

  if len(args) > 1:
    ssh_cmd += " -- -N"
    ports = set()
    for i in args[1:]:
      if i == "-":
        i = str(6006 + int(machine_id))
      ports.add(i)
    for i in sorted(ports):
      ssh_cmd += " -L {i}:localhost:{i}".format(i=i)

  print(ssh_cmd)
  sys.exit()


if __name__ == "__main__":
  main()
