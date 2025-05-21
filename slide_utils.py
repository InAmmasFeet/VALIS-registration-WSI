import json
from typing import List, Dict


def load_wasabi_tree(json_path: str) -> Dict:
    """Load the JSON file describing the wasabi file tree."""
    with open(json_path, "r") as f:
        return json.load(f)


def _collect_pairs(node: Dict, prefix: List[str], pairs: List[Dict]):
    if node.get("type") == "directory" and "Pair" in node.get("name", ""):
        pair_info = {
            "pair_name": node["name"],
            "he_slide": None,
            "cd8_slide": None,
        }
        for child in node.get("children", []):
            if child.get("type") == "file":
                name_lower = child["name"].lower()
                path = "/".join(prefix + [node["name"], child["name"]])
                if "unmixed if" in name_lower:
                    pair_info["cd8_slide"] = path
                elif "he" in name_lower:
                    pair_info["he_slide"] = path
        if pair_info["he_slide"] and pair_info["cd8_slide"]:
            pairs.append(pair_info)
    for child in node.get("children", []):
        if child.get("type") == "directory":
            _collect_pairs(child, prefix + [node["name"]], pairs)


def get_slide_pairs(tree: Dict) -> List[Dict]:
    """Return a list of dictionaries containing HE and CD8 slide paths."""
    pairs: List[Dict] = []
    _collect_pairs(tree, [], pairs)
    return pairs
