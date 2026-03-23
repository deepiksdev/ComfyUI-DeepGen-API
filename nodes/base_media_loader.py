import folder_paths
import hashlib

class BaseMediaLoaderNode:
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        media = kwargs.get("image") or kwargs.get("video")
        if not media:
            return ""
        media_path = folder_paths.get_annotated_filepath(media)
        m = hashlib.sha256()
        with open(media_path, 'rb') as f:
            m.update(f.read())
        return m.digest().hex()

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        media = kwargs.get("image") or kwargs.get("video")
        if not media:
            return "Missing media input"
        if not folder_paths.exists_annotated_filepath(media):
            return "Invalid media file: {}".format(media)
        return True
