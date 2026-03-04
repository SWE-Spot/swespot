from feaswebench.harness.constants.constants import *
from feaswebench.harness.constants.javascript import *
from feaswebench.harness.constants.python import *

MAP_REPO_VERSION_TO_SPECS = DefaultDict({
    **MAP_REPO_VERSION_TO_SPECS_JS,
    **MAP_REPO_VERSION_TO_SPECS_PY,
})

MAP_REPO_TO_INSTALL = {
    **MAP_REPO_TO_INSTALL_JS,
    **MAP_REPO_TO_INSTALL_PY,
}

MAP_REPO_TO_EXT = DefaultDict({
    **{k: "js" for k in MAP_REPO_VERSION_TO_SPECS_JS.keys()},
    **{k: "py" for k in MAP_REPO_VERSION_TO_SPECS_PY.keys()},
    "default": "py"
})

LATEST = "latest"
USE_X86 = USE_X86_PY
