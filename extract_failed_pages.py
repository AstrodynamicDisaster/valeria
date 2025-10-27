#!/usr/bin/env python3
import re

failed_pages = []
current_page = None

with open('/Users/albert/repos/valeria/log_danik_tail.txt', 'r', encoding='utf-8') as f:
    for line in f:
        # Check for processing page line
        if '🔄 Processing page' in line:
            match = re.search(r'page (\d+)/\d+', line)
            if match:
                current_page = int(match.group(1))

        # Check for no employee found line
        if '❌ No employee found with any ID variation' in line:
            if current_page is not None:
                failed_pages.append(current_page)

# Remove duplicates and sort
failed_pages = sorted(set(failed_pages))

# Print results
for page in failed_pages:
    print(page)

print(f"\nTotal pages with unmatched employees: {len(failed_pages)}")
