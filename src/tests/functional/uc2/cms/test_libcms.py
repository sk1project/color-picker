import os

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


def test_open_absent_profile():
    try:
        profile = get_filepath('xxx.icm')
        libcms.cms_open_profile_from_file(profile)
    except libcms.CmsError:
        return
    assert False


def test_create_transform():
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.TYPE_CMYK_8) is not None
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGBA_8,
        OUT_PROFILE, uc2const.TYPE_CMYK_8) is not None
    assert libcms.cms_create_transform(
        OUT_PROFILE, uc2const.TYPE_CMYK_8,
        IN_PROFILE, uc2const.TYPE_RGBA_8) is not None
    assert libcms.cms_create_transform(
        OUT_PROFILE, uc2const.TYPE_CMYK_8,
        IN_PROFILE, uc2const.TYPE_RGB_8) is not None


def test_create_transform_with_custom_intent():
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_PERCEPTUAL) is not None
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_RELATIVE_COLORIMETRIC) is not None
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_SATURATION) is not None
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_ABSOLUTE_COLORIMETRIC) is not None


def test_create_transform_with_custom_flags():
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_PERCEPTUAL,
        uc2const.cmsFLAGS_NOTPRECALC | uc2const.cmsFLAGS_GAMUTCHECK) is not None
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_PERCEPTUAL,
        uc2const.cmsFLAGS_PRESERVEBLACK |
        uc2const.cmsFLAGS_BLACKPOINTCOMPENSATION) is not None
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_PERCEPTUAL,
        uc2const.cmsFLAGS_NOTPRECALC |
        uc2const.cmsFLAGS_HIGHRESPRECALC) is not None
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_PERCEPTUAL,
        uc2const.cmsFLAGS_NOTPRECALC |
        uc2const.cmsFLAGS_LOWRESPRECALC) is not None


def test_create_transform_with_invalid_intent():
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.TYPE_CMYK_8, 3) is not None
    try:
        libcms.cms_create_transform(
            IN_PROFILE, uc2const.TYPE_RGB_8,
            OUT_PROFILE, uc2const.TYPE_CMYK_8, 4)
    except libcms.CmsError:
        return
    assert False
