import argparse
import copy
import logging
import json
import pkg_resources
import jinja2
import os

from channelstream.cli import CONFIGURABLE_PARAMS, SHARED_DEFAULTS
from channelstream.utils import set_config_types

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def main():
    config = copy.deepcopy(SHARED_DEFAULTS)

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "operation", help="Operation", default=None, choices=["make_config"]
    )
    parser.add_argument("-j", "--json", dest="json", help="Config JSON", default=None)
    parser.add_argument("-o", "--output", dest="output", help="Output file")
    args = parser.parse_args()
    if args.json:
        data_json = json.loads(args.json)
        for key in CONFIGURABLE_PARAMS:
            conf_value = data_json.get(key)
            if conf_value:
                config[key] = conf_value
    else:
        for key in CONFIGURABLE_PARAMS:
            conf_value = os.environ.get(f"channelstream_{key}".upper())
            if conf_value is not None:
                config[key] = conf_value
        config = set_config_types(config)

    if args.operation == "make_config":
        template_path = os.path.join("templates", "ini", "channelstream.ini.jinja2")
        template_str = pkg_resources.resource_string("channelstream", template_path)
        template = jinja2.Template(template_str.decode("utf8"))
        template_vars = config
        compiled = template.render(**template_vars)
        if args.output:
            with open(args.output, "w") as f:
                f.write(compiled)
            log.info("Config written")
        else:
            print(compiled)
