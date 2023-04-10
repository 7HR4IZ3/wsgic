import hashlib

from functools import singledispatch

import io

from wsgic.thirdparty.bottle import (
    mimetypes, HTTPResponse, HTTPError, email, time, tob,
    parse_date, parse_range_header, _file_iter_range, FileUpload, 
    cached_property
)
from wsgic.http import request
from wsgic.routing import route

from functools import lru_cache, partial
import os
import sys
import json


class File(FileUpload):
    def __init__(self, *a, **kw):
        self.init(*a, **kw)

    @singledispatch
    def init(self, fileobj, name, filename=None, headers=None, store=None):
        super().__init__(fileobj, name, filename or name, headers)
        self.__store = store
    
    @init.register(io.IOBase)
    def _(self, file, headers=None, store=None):
        super().__init__(file.read(), file.name, file.name, headers)
        self.__store = store

    @cached_property
    def path(self):
        if self.__store:
            return self.__store.path(self.filename)
        return None
    
    @cached_property
    def url(self):
        url = self.__store.get_url(self.filename)
        if url:
            return url
        return None

    def __getattr__(self, name):
        if hasattr(self.file, name):
            return getattr(self.file, name)

class BaseStorage:
    config = {}
    plugins = None
    
    def __init__(self, **config):
        self.config = config
        self.plugins = []
        self.config["name"] = self.config.get("name", self.config.get("directory", "").lstrip("./").replace("//", "/").split("/")[-1])
        # if not self.exists(self.config['directory']):
        #     self.create_directory("")
    
    def _main(self, *a, **kw):
        return self

    def __str__(self):
        return f'{self.__class__.__name__}(directory={self.config["directory"]})'

    def get(self, filename, **kw):raise NotImplementedError
    def save(self, filename, data, **kw):raise NotImplementedError
    def exists(self, *a, **kw):raise NotImplementedError
    def delete(self, *a, **kw):raise NotImplementedError
    def delete_directory(self, *a, **kw):raise NotImplementedError
    def create_directory(self, *a, **kw):raise NotImplementedError
    def restrict(self, *a, **kw):raise NotImplementedError
    def list(self, *a, **kw):raise NotImplementedError
    def path(self, filename, **kw):raise NotImplementedError
    def has_access(self, filename, **kw):raise NotImplementedError

    def handler(self, path, directory=None,  mimetype=True, download=False, charset='UTF-8', etag=None, headers=None, cache=True):
        directory = directory or self.config["directory"]
        
        filepath = self.join(directory, path)
        splits = os.path.split(filepath)

        try:
            filename = splits[1]
            file = self.get(filename, directory=splits[0]).file
        except FileNotFoundError:
            return HTTPError(404, "File does not exist.")

        headers = headers.copy() if headers else {}

        # if not filename.startswith(store.config["name"]):
        #     return HTTPError(403, "Access denied.")
        # if not self.exists(filename, directory=splits[0]) or not self.is_file(filename, directory=splits[0]):
        #     return HTTPError(404, "File does not exist.")
        if not self.has_access(filename, directory=splits[0]):
            return HTTPError(403, "You do not have permission to access this file.")
    
        if mimetype is True:
            if download and download is not True:
                mimetype, encoding = mimetypes.guess_type(download)
            else:
                mimetype, encoding = mimetypes.guess_type(filename)

            if encoding:
                headers['Content-Encoding'] = encoding
    
        if mimetype:
            if (mimetype[:5] == 'text/' or mimetype == 'application/javascript')\
              and charset and 'charset' not in mimetype:
                mimetype += '; charset=%s' % charset
            headers['Content-Type'] = mimetype
    
        if download:
            download = self.basename(filename if download is True else download)
            headers['Content-Disposition'] = 'attachment; filename="%s"' % download
    
        stats = os.stat(filepath)
        headers['Content-Length'] = clen = stats.st_size
        headers['Last-Modified'] = email.utils.formatdate(stats.st_mtime, usegmt=True)
        headers['Date'] = email.utils.formatdate(time.time(), usegmt=True)
    
        getenv = request.environ.get
    
        if etag is None:
            etag = '%d:%d:%d:%d:%s' % (stats.st_dev, stats.st_ino, stats.st_mtime, clen, filename)
            etag = hashlib.sha1(tob(etag)).hexdigest()
    
        if etag:
            headers['ETag'] = etag
            check = getenv('HTTP_IF_NONE_MATCH')
            if check and check == etag:
                return HTTPResponse(status=304, **headers)
    
        ims = getenv('HTTP_IF_MODIFIED_SINCE')
        if ims:
            ims = parse_date(ims.split(";")[0].strip())
        if ims is not None and ims >= int(stats.st_mtime):
            return HTTPResponse(status=304, **headers)
    
        body = '' if request.method == 'HEAD' else file
    
        headers["Accept-Ranges"] = "bytes"
        range_header = getenv('HTTP_RANGE')
        if range_header:
            ranges = list(parse_range_header(range_header, clen))
            if not ranges:
                return HTTPError(416, "Requested Range Not Satisfiable")
            offset, end = ranges[0]
            headers["Content-Range"] = "bytes %d-%d/%d" % (offset, end - 1, clen)
            headers["Content-Length"] = str(end - offset)
            if body: body = _file_iter_range(body, offset, end - offset, close=True)
            
            return HTTPResponse(body, status=206, **headers)
        return HTTPResponse(body, **headers)
    
    def get_url(self, filename, directory=None):
        directory = directory or self.config["directory"]
        path = self.join(directory, filename)

        for url in list(self._handlers.keys())[::-1]:
            if url in directory:
                diff = path.replace(url, "")
                urlpath = self._handlers[url]

                return route(urlpath, path=diff.lstrip("/").lstrip("\\"))
        return None

# class Folder:
#     def __init__(self, **config):
#         self.config = config
#         self.name = config.get("name", None)
#         self.parent = config.get("parent", None)
    
#     def create(self):
#         if not self.exists(store=self):
#             self.create_directory(store=self)
#         return self

#     def __getattr__(self, name):
#         return partial(getattr(self.parent, name), store=self)
    
#     def __getitem__(self, name):
#         if self.exists(name) and self.is_file(name):
#             return self.get(name)
#         return Folder(directory=self.join(self.config["directory"], name), name=name, parent=self)

class Folder:
    def __init__(self, **config):
        self.config = config
        self.store = self.config.get('store', None)
    
    def create(self):
        if not self.exists(directory=self.config["directory"]):
            self.create_directory(directory=self.config["directory"])
        return self

    def __getattr__(self, name):
        return partial(getattr(self.store, name), directory=self.config["directory"])
    
    def __getitem__(self, name):
        if self.exists(name) and self.is_file(name):
            return self.get(name)
        return Folder(directory=self.store.join(self.config["directory"], name), store=self, name=name)
    
    def __str__(self):
        return f'Folder(directory={self.config["directory"]})'
    
    def parent(self):
        if self.store:
            return self.store.config["directory"]

class FileSystemStorage(BaseStorage):
    modes = {
        "truncate": 'wb',
        "create": 'xb',
        "append": 'ab',
        "update": 'wb+'
    }
    __restricted = []
    _handlers = {}

    def __getitem__(self, name):
        if self.exists(name) and self.is_file(name):
            return self.get(name)
        path = self.path(name)
        return Folder(directory=path, store=self, name=name)

    def path(self, filename, validate=False, directory=None, **kwargs):
        path = self.join(directory or self.config['directory'], filename)
        if validate:
            if self.exists(filename, directory=directory):
                return path
            else:
                raise FileNotFoundError(f"File/Folder {filename} not found on filesystem at {path}")
        return path
    
    def basename(self, filename, directory=None):
        return os.path.basename(self.join(filename, directory or self.config["directory"]))
    
    def create(self, directory=None):
        if not self.exists(directory=directory):
            self.create_directory(directory=directory)
        return self
    
    def join(self, *paths, **kwargs):
        return os.path.join(*paths)
    
    def exists(self, path=None, directory=None):
        return os.path.exists(
            self.join(directory or self.config['directory'], path or "")
        )
    
    def list(self, directory=None):
        return os.listdir(
            directory or self.config['directory']
        )
    
    def has_access(self, file, directory=None):
        path = self.join(directory or self.config["directory"], file)
        return os.access(path, os.R_OK)
    
    def is_dir(self, item, directory=None):
        path = self.join(directory or self.config["directory"], item)
        return os.path.isdir(path)
    
    def is_file(self, item, directory=None):
        path = self.join(directory or self.config["directory"], item)
        return os.path.isfile(path)
    
    def get(self, filename, directory=None, filebuffer=False):
        store = Folder(directory=directory, store=self) if directory else self
        path = self.path(filename, validate=True, directory=directory)

        file = open(path, "rb")
        if filebuffer:
            return file
        data = File(file, file.name, store=store)
        # file.close()
        return data
    
    def save(self, filename, data, mode="truncate", directory=None, **kwargs):
        '''
        Modes: ["truncate", "create", "append",  "update"]
        '''
        path = self.path(filename, directory=directory)
        with open(path, self.modes.get(mode, "+")) as f:
            f.write(data)
    
    def delete(self, filename, directory=None):
        path = self.path(filename, validate=True, directory=directory)
        if os.path.isdirectory(path):
            os.removedirs(path)
        else:
            os.remove(path)
    
    def create_directory(self, folder=None, directory=None):
        path = self.path(folder or "", directory=directory)
        os.mkdir(path)
    
    def restore(self, data, directory=None):
        def main(data, directory=""):
            for item in data:
                path = self.join(directory, item)
                d = data[item]
                if isinstance(d, dict):
                    self.create_directory(item, directory)
                    main(d, path)
                elif isinstance(d, bytes):
                    self.save(item, d, directory=directory)
        main(data, directory or self.config["directory"])
    
    def backup(self, directory=None, buffer=None, skip=[], apply=lambda x:x):

        def main(directory):
            data = {}
            for item in self.list(directory):
                path = self.join(directory, item)
                if self.is_dir(item, directory):
                    data[item] = main(path)
                elif self.is_file(item, directory):
                    data[item] = self.get(path, directory=".")
            return data
        
        data = apply(
            main(directory or self.config["directory"]
        ))
        if buffer:
            buffer.write(data)
        return data


# class FileSystemStorage(BaseStorage):
#     modes = {
#         "truncate": 'wb',
#         "create": 'xb',
#         "append": 'ab',
#         "update": 'wb+'
#     }
#     __restricted = []

#     def __getitem__(self, name):
#         if self.exists(name) and self.is_file(name):
#             return self.get(name)
#         path = self.path(name)
#         return Folder(directory=path, parent=self, name=name)

#     def path(self, filename, validate=False, store=None, **kwargs):
#         store = store or self
#         path = self.join(store.config.get("directory"), filename)
#         if validate:
#             if self.exists(filename, store=store):
#                 return path
#             else:
#                 raise FileNotFoundError(f"File/Folder {filename} not found on filesystem at {path}")
#         return path
    
#     def basename(self, filename, store=None):
#         store = store or self
#         return os.path.basename(self.join(filename, store.config.get("directory")))
    
#     def create(self, store=None):
#         store = store or self
#         if not self.exists(store=store):
#             self.create_directory(store=store)
#         return self
    
#     def join(self, *paths, **kwargs):
#         return os.path.join(*paths)
    
#     def exists(self, path=None, store=None):
#         store = store or self
#         return os.path.exists(
#             self.join(store.config.get("directory"), path or "")
#         )
    
#     def list(self, store=None):
#         store = store or self
#         return os.listdir(
#             store.config.get("directory")
#         )
    
#     def has_access(self, file, store=None):
#         store = store or self
#         path = self.join(store.config.get("directory"), file)
#         return os.access(path, os.R_OK)
    
#     def is_dir(self, item, store=None):
#         store = store or self
#         path = self.join(store.config.get("directory"), item)
#         return os.path.isdir(path)
    
#     def is_file(self, item, store=None):
#         store = store or self
#         path = self.join(store.config.get("directory"), item)
#         return os.path.isfile(path)
    
#     def get(self, filename, store=None, filebuffer=False):
#         store = store or self
#         path = self.path(filename, validate=True, store=store)

#         file = open(path, "rb")
#         if filebuffer:
#             return file
#         data = File(file.read(), file.name, file.name, store=store)
#         file.close()
#         return data
    
#     def save(self, filename, data, mode="truncate", store=None, **kwargs):
#         '''
#         Modes: ["truncate", "create", "append",  "update"]
#         '''
#         store = store or self
#         path = self.path(filename, store=store)
#         with open(path, self.modes.get(mode, "+")) as f:
#             f.write(data)
    
#     def delete(self, filename, store=None):
#         store = store or self
#         path = self.path(filename, validate=True, store=store)
#         if os.path.isdirectory(path):
#             os.removedirs(path)
#         else:
#             os.remove(path)
    
#     def create_directory(self, folder=None, store=None):
#         store = store or self
#         path = self.path(folder or "", store=store)
#         os.mkdir(path)
    
#     def restore(self, data, store=None):
#         store = store or self
        
#         def main(data, directory=""):
#             for item in data:
#                 path = self.join(directory, item)
#                 d = data[item]
#                 if isinstance(d, dict):
#                     self.create_directory(item, directory)
#                     main(d, path)
#                 elif isinstance(d, bytes):
#                     self.save(item, d, store=store)
#         main(data, store.config.get("directory"))
    
#     def backup(self, store=None, buffer=None, skip=[], apply=lambda x:x):

#         def main(directory):
#             data = {}
#             for item in self.list(directory):
#                 path = self.join(directory, item)
#                 if self.is_dir(item, directory):
#                     data[item] = main(path)
#                 elif self.is_file(item, directory):
#                     data[item] = self.get(path, store=".")
#             return data
        
#         data = apply(
#             main(store.config.get("directory")
#         ))
#         if buffer:
#             buffer.write(data)
#         return data

