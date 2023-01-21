from wsgic.thirdparty.cache3 import SimpleCache, SafeCache, SimpleDiskCache, DiskCache, JsonDiskCache

caches = {
    "simple": SimpleCache,
    "safe": SafeCache,
    "disk": SimpleDiskCache,
    "pickle_disk": DiskCache,
    "json_disk": JsonDiskCache
}

def cache(cache_type="simple", *args, **kwargs):
    return caches.get(cache_type)(*args, **kwargs)
