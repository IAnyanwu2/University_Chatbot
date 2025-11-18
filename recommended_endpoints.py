#!/usr/bin/env python3
"""
Clean and prioritize the discovered endpoints for faculty information
"""

# High-value faculty profile URLs discovered
faculty_profiles = [
    "https://csds.gsu.edu/profile/ying-zhu/",
    "https://csds.gsu.edu/profile/yanqing-zhang/", 
    "https://csds.gsu.edu/profile/xiaolin-hu/",
    "https://csds.gsu.edu/profile/yubao-wu/",
    "https://csds.gsu.edu/profile/michael-weeks/",
    "https://csds.gsu.edu/profile/anu-bourgeois/",
    "https://csds.gsu.edu/profile/berkay-aydin/",
    "https://csds.gsu.edu/profile/xiaojun-cao/",
    "https://csds.gsu.edu/profile/wei-li/",
    "https://csds.gsu.edu/profile/robyn-miller/",
    "https://csds.gsu.edu/profile/sergey-plis/",
    "https://csds.gsu.edu/profile/murray-patterson/",
    "https://csds.gsu.edu/profile/alex-zelikovsky/",
    "https://csds.gsu.edu/profile/armin-mikler/",
    "https://csds.gsu.edu/profile/louis-henry/"
]

# Research and directory pages
research_pages = [
    "https://csds.gsu.edu/research-groups-labs/",
    "https://csds.gsu.edu/directory/",
    "https://csds.gsu.edu/research/"  # Already have this one
]

# Key graduate program pages
graduate_pages = [
    "https://csds.gsu.edu/graduate/advisement/",
    "https://csds.gsu.edu/course-descriptions-schedule/"
]

print("🎯 RECOMMENDED ENDPOINTS TO ADD:")
print("\n# Faculty Profiles (Rich research info + contact details):")
for url in faculty_profiles[:10]:  # Top 10 faculty
    print(f'    "{url}",')

print("\n# Research & Directory Pages:")
for url in research_pages:
    print(f'    "{url}",')

print("\n# Additional Graduate Info:")
for url in graduate_pages:
    print(f'    "{url}",')

print(f"\n📊 Total new endpoints: {len(faculty_profiles[:10]) + len(research_pages) + len(graduate_pages)}")
print("\n💡 These faculty profiles should contain:")
print("   - Research areas (robotics, AI, etc.)")
print("   - Complete contact information")
print("   - Lab/group affiliations")
print("   - Publications and expertise")