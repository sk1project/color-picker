import pytest, os
from PIL import Image

from uc2 import uc2const
from uc2.cms import libcms


_pkgdir = os.path.abspath(os.path.dirname(__file__))


def get_filepath(filename):
    return os.path.join(_pkgdir, 'cms_data', filename)


IN_PROFILE = libcms.cms_open_profile_from_file(get_filepath('sRGB.icm'))
OUT_PROFILE = libcms.cms_open_profile_from_file(get_filepath('GenericCMYK.icm'))
TRANSFORM = libcms.cms_create_transform(
    IN_PROFILE, uc2const.TYPE_RGBA_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
    uc2const.INTENT_PERCEPTUAL, uc2const.cmsFLAGS_NOTPRECALC)
TRANSFORM2 = libcms.cms_create_transform(
    IN_PROFILE, uc2const.TYPE_RGBA_8, OUT_PROFILE,
    uc2const.TYPE_CMYK_8, uc2const.INTENT_PERCEPTUAL, 0)


def test_open_invalid_profile():
    try:
        profile = get_filepath('empty.icm')
        libcms.cms_open_profile_from_file(profile)
    except libcms.CmsError:
        return
    assert False
