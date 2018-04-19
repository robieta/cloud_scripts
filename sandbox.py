
import argparse
import sys

import googleapiclient.discovery

import constants

COMPUTE = googleapiclient.discovery.build('compute', 'v1')


def list_instances(project):
  result = COMPUTE.instances().list(
      project=project, zone=constants.ZONES[project]).execute()
  return [i["name"] for i in result["items"]]


def list_disks(project):
  result = COMPUTE.disks().list(
      project=project, zone=constants.ZONES[project]).execute()
  return [i["name"] for i in result["items"]]


def get_new_instance_name(project):
  instances = list_instances(project)
  disks = list_disks(project)
  for i in range(10000):
    name = constants.populate_template(user=constants.USER, id=i)
    if name not in instances and name not in disks:
      return name
  raise NameError("How? ...just how?")


def make(namespace):
  name = get_new_instance_name(namespace.project)
  print(name)


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
  list_parser = subparser.add_parser("list", help="List current sandboxes.",
                                     formatter_class=formatter)

  make_parser.set_defaults(func=make)
  list_parser.set_defaults(func=list)

  [add_project(p) for p in [make_parser, list_parser]]

  make_parser.add_argument("--cpus", "-c", type=int, default=8,
                           help="[default: %(default)s] Number of CPUs.", metavar="<C>")
  make_parser.add_argument(
      "--p100", type=int, default=0,
      help="[default: %(default)s] Number of P100s. (Max 4)", metavar="<P>"
  )
  make_parser.add_argument(
      "--k80", type=int, default=0,
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

  return parser

if __name__ == "__main__":
  parser = construct_parser()
  namespace = parser.parse_args(sys.argv[1:])
  namespace.project = constants.PROJECTS[namespace.project]
  namespace.func(namespace)