import argparse
import copy
import logging
import json
import pkg_resources
import jinja2
import os

from channelstream.cli import CONFIGURABLE_PARAMS, SHARED_DEFAULTS

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def main():
    config = copy.deepcopy(SHARED_DEFAULTS)

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "operation", help="Operation", default=None, choices=["make_config"]
    )
    parser.add_argument("-j", "--json", dest="json", help="Config JSON", default=None)
    parser.add_argument(
        "-o", "--output", dest="output", help="Output file", required=True
    )
    args = parser.parse_args()
    data_json = {}
    if args.json:
        data_json = json.loads(args.json)

    for key in CONFIGURABLE_PARAMS:
        conf_value = data_json.get(key)
        if conf_value:
            config[key] = conf_value

    if args.operation == "make_config":
        template_path = os.path.join("templates", "ini", "channelstream.ini.jinja2")
        template_str = pkg_resources.resource_string("channelstream", template_path)
        template = jinja2.Template(template_str.decode("utf8"))
        template_vars = config
        compiled = template.render(**template_vars)
        with open(args.output, "w") as f:
            f.write(compiled)
        log.info("Config written")
