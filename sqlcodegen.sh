#!/bin/bash

echo "Generating models..."

sqlacodegen "postgresql://xxxxxxxxxxxxxxx"  --outfile infra/db/models.py

echo "Models generated successfully!"