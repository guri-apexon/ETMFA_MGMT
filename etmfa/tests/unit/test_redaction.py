import logging
import re

import pytest
from etmfa.db.db import db_context
from etmfa.utilities.redact import Redactor
from etmfa.consts import Consts as consts, constants as config

logger = logging.getLogger(consts.LOGGING_NAME)

# Init
sample_text = ": Efficacy and safety of GSK3196165 versus placebo and sarilumab in participants with moderately to severely active rheumatoid arthritis who have an inadequate response to biological DMARDs and/or Janus Kinase inhibitors. sarilumab(new compound) is beneficial"
sample_font_info = {'IsBold': False, 'font_size': -1, 'font_style': '', 'entity': [{'start_idx': 25, 'end_idx': 34, 'subcategory': 'Molecule', 'confidence': 75.0, 'text': 'GSK3196165', 'debug_redact_text': 'GSK3196165', 'debug_redact_text_match_flg': True}, {'start_idx': 55, 'end_idx': 63, 'subcategory': 'Molecule', 'confidence': 75.0, 'text': 'sarilumab', 'debug_redact_text': 'sarilumab', 'debug_redact_text_match_flg': True}, {'start_idx': 0, 'end_idx': 0, 'subcategory': 'Molecule', 'confidence': 75.0, 'text': 'sarilumab(new'}], 'Bold': False, 'Caps': False, 'ColorRGB': 0, 'DStrike': False, 'Emboss': False, 'Highlight': '', 'Imprint': False, 'Italics': False, 'Outline': False, 'rFonts': '', 'rStyle': '', 'Shadow': False, 'Size': -1, 'SmallCaps': False, 'Strike': False, 'Underline': '', 'Vanish': False, 'VertAlign': ''}

@pytest.mark.parametrize("expected_profiles", [
    (set(config.USERROLE_REDACTPROFILE_MAP.values()))
])
def test_get_all_redact_profile_names(new_app_context, expected_profiles):
    """
    Verify all configured profiles extracted
    """
    _, _app_context = new_app_context
    with _app_context:
        db = db_context.session
        red_obj = Redactor(db)
        all_profiles = red_obj.get_profiles()
        assert expected_profiles == set(all_profiles.keys())
        logger.debug(f"all_profiles: {all_profiles}")


@pytest.mark.parametrize("redact_profile, genre, max_genre_count, comments", [
    (config.USERROLE_REDACTPROFILE_MAP.get("primary", ""), config.GENRE_ENTITY_NAME, 0 ,"primary user's redact profile for genre entity"),
    (config.USERROLE_REDACTPROFILE_MAP.get("primary", ""), config.GENRE_ATTRIBUTE_NAME, 0 ,"primary user's redact profile for genre attribute"),
    (config.USERROLE_REDACTPROFILE_MAP.get("primary", ""), config.GENRE_ACTION_NAME, 0 ,"primary user's redact profile for genre action"),
    (config.USERROLE_REDACTPROFILE_MAP.get("primary", ""), config.GENRE_SECTION_NAME, 0 ,"primary user's redact profile for genre section"),
    (config.USERROLE_REDACTPROFILE_MAP.get("secondary", ""), config.GENRE_ENTITY_NAME, 60 ,"secondary user's redact profile for genre entity"),
    (config.USERROLE_REDACTPROFILE_MAP.get("secondary", ""), config.GENRE_ATTRIBUTE_NAME, 60 ,"secondary user's redact profile for genre attribute"),
    (config.USERROLE_REDACTPROFILE_MAP.get("secondary", ""), config.GENRE_ACTION_NAME, 2 ,"secondary user's redact profile for genre action"),
    (config.USERROLE_REDACTPROFILE_MAP.get("secondary", ""), config.GENRE_SECTION_NAME, 3 ,"secondary user's redact profile for genre section")
])
def test_current_redact_genre(new_app_context, redact_profile, genre, max_genre_count, comments):
    """
    Verify correct genre details extracted based on profile
    """
    logger.debug(f"Testing for {comments}")
    _, _app_context = new_app_context
    with _app_context:
        db = db_context.session
        redactor = Redactor(db)
        # Validate redact genre
        profile_name, profile, profile_genre = redactor.get_current_redact_profile(
            current_db=db, profile_name=redact_profile, genre=genre)
        assert profile_name == redact_profile
        assert len(profile_genre) <= max_genre_count
        assert len(profile.get(genre)) <= max_genre_count
        logger.debug(f"profile_name: {profile_name}; profile_genre: {profile_genre}")


@pytest.mark.parametrize("text, font_info, redact_profile_entities, redact_flg, exclude_redact_property_flg, comments", [
    (sample_text, sample_font_info, "profile_0_entities", True, True, "Ideal secondary profile"),
    (sample_text, sample_font_info, "profile_0_entities", False, True, "Do not redact text but exclude property"),
    (sample_text, sample_font_info, "profile_0_entities", True, False, "Redact text and include property"),
    (sample_text, sample_font_info, "profile_0_entities", False, False, "Do not redact text and include property"),
    (sample_text, sample_font_info, "profile_1_entities", True, True, "Ideal primary profile"),
    (sample_text, sample_font_info, "profile_1_entities", False, True, "Do not redact text but exclude property"),
    (sample_text, sample_font_info, "profile_1_entities", True, False, "Redact text and include property"),
    (sample_text, sample_font_info, "profile_1_entities", False, False, "Do not redact text and include property"),
    ("", sample_font_info, "profile_1_entities", True, True, "Empty text"),
    (sample_text, {}, "profile_1_entities", True, True, "Empty font_info"),
    ("", {}, "profile_1_entities", True, True, "Empty text AND font_info"),
    (sample_text, {"entity": []}, "profile_1_entities", True, True, "Empty entity"),
    ("", {"entity": []}, "profile_1_entities", True, True, "Empty text AND Empty entity"),
    ("", {"entity": []}, "profile_1_entities", True, False, "Empty text AND Empty entity but include property")
])
def test_redact_text(new_app_context, text, font_info, redact_profile_entities, redact_flg, exclude_redact_property_flg, comments):
    """
    Verify text and properties are redacted
    """
    _, _app_context = new_app_context
    with _app_context:
        db = db_context.session
        redactor = Redactor(db)
        if redact_profile_entities == "profile_0_entities":
            _, _, redact_profile_entities = redactor.get_current_redact_profile(current_db=db, profile_name='secondary', genre=config.GENRE_ENTITY_NAME)
        elif redact_profile_entities == "profile_1_entities":
            _, _, redact_profile_entities = redactor.get_current_redact_profile(current_db=db, profile_name='primary',
                                                                           genre=config.GENRE_ENTITY_NAME)
        redacted_text, redacted_property = redactor.on_paragraph(text, font_info, redact_profile_entities, redact_flg, exclude_redact_property_flg)

        for each_entity in font_info.get('entity', []):
            entity_adjusted_text = config.REGEX_SPECIAL_CHAR_REPLACE.sub(r".{1}", each_entity.get('text'))
            if each_entity.get('subcategory') in redact_profile_entities and len(config.REGEX_SPECIAL_CHAR_REPLACE.sub(r"", each_entity.get('text', ''))) != 0 and redact_flg:
                assert re.search(entity_adjusted_text, redacted_text, re.I) is None
            else:
                assert re.search(entity_adjusted_text, redacted_text, re.I) is not None

        if exclude_redact_property_flg:
            assert redacted_property.get('entity') is None
        else:
            assert redacted_property.get('entity') is not None
