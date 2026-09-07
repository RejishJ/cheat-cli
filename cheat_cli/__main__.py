"""Allow running cheat-cli as: python -m cheat_cli"""

import sys

from .cli import main

sys.exit(main())
