
import re
import subprocess
import sys

from constants import USER, GCLOUD, PROJECTS, ZONES, SANDBOX_TEMPLATE

project_string = "\n".join(
    ["  {}: {}".format(key, val) for key, val in sorted(PROJECTS.items())])

def construct_command(machine_id, port_list=None):
  port_list = port_list or []
  project=None

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

  if len(port_list) > 0:
    ssh_cmd += " -- -N"
    ports = set()
    for i in port_list:
      if i == "-":
        i = str(6006 + int(machine_id))
      ports.add(i)
    for i in sorted(ports):
      ssh_cmd += " -L {i}:localhost:{i}".format(i=i)

  return ssh_cmd

usage_examples = [
  "  {}\n   $ cssh {}\n      {}".format(
      i[0], " ".join(i[1:]), construct_command(i[1], i[2:]))
  for i in [("SSH into sandbox 0:", "0",),
            ("Same SSH command. (a is inferred if not specified)", "0a", ),
            ("SSH into a sandbox in a different project", "1c", ),
            ("Forward port for TensorBoard", "0a", "6006"),
            ("'-' is rewritten to (sandbox_id + 6006)", "4", "-"),
            ("Multiple ports can be forwarded.", "2", "-", "7000", "7001")]]

SSH_HELP_TEXT = ("Convenience function for ssh-ing into cloud instances.\n\n"
             "Projects:\n{project_string}\n\nExample usages:\n{usage_examples}").format(
    project_string=project_string,
    usage_examples="\n\n".join(usage_examples)
)

RSYNC_HELP_TEXT = ("Convenience function for rsyncing files to and from cloud instances.\n"
                   "Usage:\n  $ crsync <sandbox> <source> CLOUD<dest>\n    or\n"
                   "  $ crsync <sandbox> CLOUD<source> <dest>\n\nFor example:\n"
                   "  $ crsync 1c ~/foo.txt CLOUD:bar/\n\nThe script will replace 'CLOUD' "
                   "with USER@HOST")

def main():
  args = sys.argv[1:]
  if len(args) == 0:
    print("Provide a command")
    sys.exit(1)

  command = args[0]
  args = args[1:]

  if command == "ssh":
    if len(args) == 0 or "-h" in args or "--help" in args:
      print(SSH_HELP_TEXT)
      sys.exit(1)

    print(construct_command(args[0], args[1:]))
    sys.exit()
  elif command == "rsync":
    if len(args) == 0 or "-h" in args or "--help" in args:
      print(RSYNC_HELP_TEXT)
      sys.exit(1)

    ssh_cmd = construct_command(args[0])
    raw_ssh_cmd = subprocess.check_output(ssh_cmd.split() + ["--dry-run"]).decode("utf-8").strip().split()
    destination = raw_ssh_cmd.pop()
    remote_shell = "'" + " ".join(raw_ssh_cmd) + "'"
    print(" ".join(["rsync", "--cvs-exclude", "-rvz", "-e", remote_shell] + [arg.replace("CLOUD", destination) for arg in args[1:]]))
    sys.exit()
  else:
    print("invalid command")
    sys.exit(1)


if __name__ == "__main__":
  main()
