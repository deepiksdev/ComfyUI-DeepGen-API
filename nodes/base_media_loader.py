import folder_paths
import hashlib

class BaseMediaLoaderNode:
    @classmethod
    def IS_CHANGED(cls, media):
        media_path = folder_paths.get_annotated_filepath(media)
        m = hashlib.sha256()
        with open(media_path, 'rb') as f:
            m.update(f.read())
        return m.digest().hex()

    @classmethod
    def VALIDATE_INPUTS(cls, media):
        if not folder_paths.exists_annotated_filepath(media):
            return "Invalid media file: {}".format(media)
        return True
