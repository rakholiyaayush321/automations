import re

with open(r'C:\Users\rakho\.openclaw\workspace\job_apply\batch_loader.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove all TechXYZ/WebXYZ generated companies (keep only real company names)
# Pattern: lines with Tech[A-Z][a-z]+ where name is obviously fake
# Keep: MindInventory, Simform, Tatvasoft, etc. - known real companies
# Remove: TechSpark, WebBoost, etc. - generated names

# Find and remove generated company tuples
# These are the ones with "10-30" size and obvious generated names
pattern = r'\n    \("Tech[A-Z][a-z]+", "[^"]+", "10-30", ""\),'
matches = re.findall(pattern, content)
print(f"Found {len(matches)} generated TechXYZ companies to remove")

# Remove them
new_content = re.sub(pattern, '', content)

pattern2 = r'\n    \("Web[A-Z][a-z]+", "[^"]+", "10-30", ""\),'
matches2 = re.findall(pattern2, new_content)
print(f"Found {len(matches2)} generated WebXYZ companies to remove")
new_content = re.sub(pattern2, '', new_content)

with open(r'C:\Users\rakho\.openclaw\workspace\job_apply\batch_loader.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Done cleaning!")
