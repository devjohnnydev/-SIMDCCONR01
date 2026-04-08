import sys
sys.path.insert(0, '.')
from reports.knowledge_base import validate_coverage, ITEM_METADATA

valid, missing = validate_coverage()
print(f"Total items mapped: {len(ITEM_METADATA)}")
print(f"Valid (all 171 orders covered): {valid}")
if not valid:
    print(f"Missing orders: {missing}")
else:
    print("All items covered!")

# Show breakdown by instrument
instruments = {}
for order, meta in ITEM_METADATA.items():
    inst = meta['instrumento']
    instruments[inst] = instruments.get(inst, 0) + 1

print("\nBreakdown by instrument:")
for inst, count in sorted(instruments.items()):
    print(f"  {inst}: {count} items")

# Show breakdown by reference
refs = {}
for order, meta in ITEM_METADATA.items():
    ref = meta['ref_key']
    refs[ref] = refs.get(ref, 0) + 1

print("\nBreakdown by reference:")
for ref, count in sorted(refs.items()):
    print(f"  {ref}: {count} items")
