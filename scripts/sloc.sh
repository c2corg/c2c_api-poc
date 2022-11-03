#!/bin/bash

echo "---- Legacy test code ----"
pygount c2corg_api/tests/legacy/ --suffix=py,json --format=summary

echo "---- Legacy app code ----"
pygount c2corg_api/legacy/  --suffix=py,json --format=summary

echo "---- Test code ----"
pygount c2corg_api/tests --folders-to-skip=[...],legacy  --suffix=py,json --format=summary

echo "---- App code (markdown) ----"
pygount c2corg_api/markdown --suffix=py,json --format=summary

echo "---- App code ----"
pygount c2corg_api --folders-to-skip=[...],legacy,markdown,tests --suffix=py,json --format=summary
