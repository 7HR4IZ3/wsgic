import os
import json
from pathlib import Path
from wsgic.handlers.files import FileSystemStorage
from wsgic.thirdparty.bottle import TEMPLATE_PATH
from wsgic.http import request, abort
from wsgic.views import render

core_dir = (Path(__file__).parent / 'core').as_posix()

core = FileSystemStorage(directory=core_dir)

class UiBuilderPlugin:
    def __init__(self, ui_path="ui_editor", assets_path="ui_editor_assets", preview_url="ui_editor_preview", actions_url="ui_editor_action"):
        self.config = {
            "ui_path": ui_path,
            "assets_path": assets_path,
            "preview_url": preview_url,
            "actions_url": actions_url
        }
        self.pages = []
        self.assets = []

    def setup(self, app):
        self.app = app

        app.static(self.config['assets_path'], store=core)
        app.get(self.config["preview_url"] + "/<path:path>", self.preview)
        app.add(self.config['ui_path'], self.editor)
        app.add(self.config["actions_url"], self.handle_actions)

    def editor(self):
        pages = self.generate_pages_from_paths() + self.generate_pages_from_routes(self.app)
        editor_html = core["editor.html"].read().decode("utf-8")
        return render(editor_html, { "static_path": self.config['assets_path'], "pages": json.dumps(self.pages + pages), "actions_url": self.config['actions_url'] })

    def preview(self, path):
        with open(path, "rb") as f:
            return f.read().decode('utf-8')

    def generate_pages_from_paths(self):
        ret = []
        added = []

        for p in TEMPLATE_PATH:
            path = Path(p)

            if path.exists():
                self.assets += [x for x in path.rglob("*")]

                for file in path.rglob("*.htm*"):
                    if file.is_file() and file.name not in added:
                        item = { "name": file.name, "file": file.as_posix(), "title": file.name.title().replace("-", " ").split(".")[0] }

                        item["url"] = f"/{self.config['preview_url']}/{(file.as_posix().replace(os.getcwd(), ''))}"
                        item["folder"] = "Templates"
                        # item["assets"] = [assets]

                        ret.append(item)
                        added.append(file.name)
        return ret

    def generate_pages_from_routes(self, app):
        ret = []

        for route in app.routes:
            if route.method == "GET":
                item = { "name": route.name or route.rule, "title": route.rule }
                item['url'] = route.rule

                file = getattr(route.callback, "__render_template__", None)
                if not file:
                   item['file'] = route.rule
                else:
                    for p in TEMPLATE_PATH:
                        path = Path(p) / file
                        if path.exists():
                            item['file'] = path.as_posix()

                item["folder"] = "Routes"
                ret.append(item)
        return ret
    
    def handle_actions(self):
        html = file = action = None

        if request.method == "POST":
            if request.POST.get("startTemplateUrl"):
                with open(request.POST.get("startTemplateUrl"), "rb") as f:
                    html = f.read().decode("utf-8")
            else:
                html = request.POST.get("html", "")

            file = request.POST.get("file")

        action = request.GET.get("action")
        
        if action:
            if action == "rename":
                new_file = request.POST.get("newFile")
                if file and new_file:
                    return f"File '{file}' renamed to '{new_file}'."
                else:
                    return abort(500, "Error renaming file.")
            elif action == "delete":
                try:
                    return f"File '{file}' deleted."
                except:
                    abort(500, "Error deleting file.")
            elif action == "scandir":

                def make(path):
                    return [{ "name": x.name, 'type': ("file" if x.is_file() else "folder"), "path": x.as_posix(), 'items': make(x) } for x in path.glob("*") if x.exists()]
                
                ret = []
                for x in TEMPLATE_PATH:
                    ret += make(Path(x))

                return json.dumps({ "name": "", "type": "folder", "items": ret, "path": "" })
            else:
                abort(500, "Invalid action.")
        else:
            if html:
                if file:
                    try:
                        with open(file, "wb") as f:
                            f.write(html)
                    except Exception as e:
                        abort(500, "Error saving file.")
                else:
                    abort(500, "Empty file name!")
            else:
                abort("Empty html content!")
    


