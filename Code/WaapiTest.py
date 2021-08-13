import os
import stat
import time
import shutil
from wwisemanager import WwiseManager
from pprint import pprint

w=WwiseManager()
Items,parentid=w.smartCreateRandomContainer()
pprint(Items)
pprint(parentid)
