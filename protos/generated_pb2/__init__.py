import os
import sys

'''Workaround solution for relative import issue from proto codegen.

See:
* https://stackoverflow.com/questions/53934591/when-i-try-to-generate-files-for-protobuf-i-get-error-modulenotfounderror
* https://stackoverflow.com/questions/61637430/relative-imports-with-protobuf-generating-python-classes-with-protobuf-gives-mo
* https://github.com/protocolbuffers/protobuf/issues/1491
'''

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
