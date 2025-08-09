#!/bin/bash

DATABASE_URL="postgresql://neondb_owner:npg_ax6S0rubeKIX@ep-shy-shape-ad0hgd7o-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

echo "Generating models..."

sqlacodegen "postgresql://neondb_owner:npg_ax6S0rubeKIX@ep-shy-shape-ad0hgd7o-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"  --outfile models.py

echo "Models generated successfully!"