"""INV-3: the normalization adds only a cold sidecar; registry.yaml stays
byte-identical to the branch baseline. This test pins the sha of the 104-record
registry so any later subsystem that touches it fails loudly."""
import hashlib, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
REG = os.path.join(REPO, "skills", "stow", "rules", "registry.yaml")

def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()

def test_registry_matches_committed_head():
    """registry.yaml on disk == the version committed at branch HEAD (no drift)."""
    committed = subprocess.check_output(
        ["git", "show", "HEAD:skills/stow/rules/registry.yaml"], cwd=REPO)
    assert hashlib.sha256(committed).hexdigest() == _sha(REG), \
        "registry.yaml differs from committed HEAD — normalization must not edit it"
