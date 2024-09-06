#!/usr/bin/env python3
import os
import aws_cdk as cdk
from ingestion_stack import IngestionStack
from processing_stack import ProcessingStack

app = cdk.App()

ingestion_stack = IngestionStack(app, "IngestionStack")

ProcessingStack(app, "ProcessingStack", ingestion_stack=ingestion_stack)

app.synth()