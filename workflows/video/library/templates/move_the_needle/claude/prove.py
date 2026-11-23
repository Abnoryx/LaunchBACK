"""Write a native LaunchBACK project dump from the editable template."""
import argparse
import json

from library.aeb import Project
from follow_needle import build

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out", required=True)
parser.add_argument("--name", default="S9")
parser.add_argument("--overrides", default="{}", help="JSON object for the template's keyword overrides")
args = parser.parse_args()

project = Project()
build(project, args.name, **json.loads(args.overrides))
print(project.dump(args.out))
