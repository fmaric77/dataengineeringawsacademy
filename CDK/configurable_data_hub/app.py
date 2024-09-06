#!/usr/bin/env python3
import os

import aws_cdk as cdk

from configurable_data_hub_fmaric.configurable_data_hub_fmaric_stack import ConfigurableDataHubFmaricStack

app = cdk.App()
ConfigurableDataHubFmaricStack(app, "ConfigurableDataHubFmaricStack")

app.synth()