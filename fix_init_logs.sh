#!/bin/bash

# Change initialization logs from INFO to DEBUG across all phase files
for file in pipeline/phases/*.py; do
    # Change "initialized" messages
    sed -i 's/self\.logger\.info("\(.*initialized.*\)")/self.logger.debug("\1")/g' "$file"
    sed -i "s/self\.logger\.info('\(.*initialized.*\)')/self.logger.debug('\1')/g" "$file"
    
    # Change "Subscribed to" messages
    sed -i 's/self\.logger\.info("\(.*Subscribed to.*\)")/self.logger.debug("\1")/g' "$file"
    sed -i "s/self\.logger\.info('\(.*Subscribed to.*\)')/self.logger.debug('\1')/g" "$file"
    
    # Change "Architecture config loaded" messages
    sed -i 's/self\.logger\.info("\(.*Architecture config loaded.*\)")/self.logger.debug("\1")/g' "$file"
    sed -i "s/self\.logger\.info('\(.*Architecture config loaded.*\)')/self.logger.debug('\1')/g" "$file"
done

echo "Fixed initialization logs in all phase files"