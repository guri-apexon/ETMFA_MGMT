import logging
import re
from etmfa.consts import Consts as consts, constants

logger = logging.getLogger(consts.LOGGING_NAME)


class RedactFootNotes:
    def __init__(self, attachments: list, redacted_placeholder: str, redact_flag: bool, redact_profile_entities = list()):
        self.attachments = attachments
        self.redacted_placeholder = redacted_placeholder
        self.redact_flag = redact_flag
        self.redact_profile_entities = redact_profile_entities

    def redact_footnotes(self, content: str, entities: dict) -> str:
        if content:
            for entity in sorted(entities, key=lambda x: (x[
                                                              constants.FOOTNOTES_START_INDEX],
                                                          x[
                                                              constants.FOOTNOTES_END_INDEX]), reverse=True):
                if entity.get('subcategory', '') in self.redact_profile_entities and len(
                        constants.REGEX_SPECIAL_CHAR_REPLACE.sub(r"", entity['text'])) != 0:
                    entity_adjusted_text = constants.REGEX_SPECIAL_CHAR_REPLACE.sub(r".{1}", entity.get('text', ''))
                    content = re.sub(entity_adjusted_text, self.redacted_placeholder, content)

        return content

    def redact_footnotes_pipeline(self):
        redacted_json = {}
        try:
            if self.attachments:
                for idx, attachment in enumerate(self.attachments):
                    text = attachment.get(constants.FOOTNOTES_TEXT, '')
                    entities = attachment.get(constants.FOOTNOTES_ENTITIES, list())
                    if self.redact_flag:
                        redacted_text = self.redact_footnotes(text, entities)
                    else:
                        redacted_text = text
                    foot_note_key = f"{constants.FOOTNOTE_STR}_{idx}"
                    redacted_json[foot_note_key] = " ".join([attachment[
                                                                 constants.FOOTNOTES_KEY], redacted_text]).strip()
        except KeyError as exc:
            logger.error(f"Missing Key : {str(exc)}")
        except Exception as exc:
            logger.error(f"Exception raised : {str(exc)}")
        return redacted_json
