#!/usr/bin/env python3
import os
import aws_cdk as cdk
from ingestion_stack import IngestionStack
from processing_stack import ProcessingStack

app = cdk.App()

# Deploy the Ingestion Stack first
ingestion_stack = IngestionStack(app, "IngestionStack")

# Deploy the Processing Stack, passing the Ingestion Stack as a parameter
ProcessingStack(app, "ProcessingStack", ingestion_stack=ingestion_stack)

app.synth()