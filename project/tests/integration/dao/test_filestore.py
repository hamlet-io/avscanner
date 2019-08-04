from src.dao import filestore
from src.dao import conf


def test():
    filestore.Quarantine(conf.get_s3_env_conf())
    filestore.Unprocessed(conf.get_s3_env_conf())
    filestore.Archive(conf.get_s3_env_conf())
