import os.path
import sys

_dir_current = os.path.dirname(os.path.realpath(__file__))
_dir_parent = os.path.dirname(_dir_current)
_dir_parent2 = os.path.dirname(_dir_parent)
sys.path.insert(0, _dir_parent)
sys.path.insert(0, _dir_parent2)

from dashboard.dashboard.content import app

server = app.server  # expose Flask server for gunicorn

if __name__ == '__main__':
    import os
    debug = os.environ.get("DASH_DEBUG", "false").lower() == "true"
    host = os.environ.get("DASH_HOST", "0.0.0.0")
    port = int(os.environ.get("DASH_PORT", "8070"))
    app.run(debug=debug, host=host, port=port,
            dev_tools_hot_reload=debug)
