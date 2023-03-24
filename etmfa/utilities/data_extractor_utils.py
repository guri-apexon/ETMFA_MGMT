import logging
import re
from typing import Tuple
from etmfa.consts.constants import ModuleConfig
from etmfa_core.aidoc.IQVDocumentFunctions import IQVDocument
from etmfa.consts import Consts as consts, constants

logger = logging.getLogger(consts.LOGGING_NAME)


def get_redaction_entities(level_roi=None) -> Tuple[int, list]:
    """
    Extracts only the redaction entities from the identified NLP entities and extracts redacted_text
    Returns: Length of redaction entities found and list of redaction entity properties and redacted text
    """
    redaction_entities = []
    if level_roi:
        for entity in level_roi.NLP_Entities:
            for property in entity.Properties:
                if property.key == ModuleConfig.GENERAL.REDACTION_SUBCATEGORY_KEY:
                    redaction_entities.append({'standard_entity_name': entity.standard_entity_name, 'subcategory': property.value, 'text': entity.text, 'start_pos': entity.start,
                                            'text_len': len(entity.text), 'end_pos': entity.start+len(entity.text)-1, 'confidence': entity.confidence})
                             
    return len(redaction_entities), redaction_entities


def align_redaction_with_subtext(text: str, redaction_entities: list) -> Tuple[list, list]:
    """
    Align redaction entity with each subtext of childbox

    Inputs
        text: string to be matched (of subtext)
        redaction_entities: List of redaction entities associated with the childbox
    Outputs
        matched_entity_set: List of matched entities in subtext
        subtext_redaction_entities: List of subtext level adjusted entity details
    """
    subtext_redaction_entities = []
    matching_spans = []
    matched_entity_set = set()
    for idx, entity in enumerate(redaction_entities):
        try:
            entity_adjusted_text = ModuleConfig.GENERAL.REGEX_SPECIAL_CHAR_REPLACE.sub(r".{1}", entity['text'])
            matching_spans = [(match.start(), match.end()-1) for match in re.finditer(entity_adjusted_text, text, re.I)]
            if matching_spans:
                matched_entity_set.add(idx)
                _ = [subtext_redaction_entities.append({'start_idx': start, 'end_idx': end, 'standard_entity_name': entity['standard_entity_name'], 'subcategory': entity['subcategory'], 'confidence': entity['confidence'], 'text': entity['text']})
                                            for start, end in matching_spans]
        except Exception as exc:
            logger.warning(f"[entity# {idx}] subtext: {text}; redaction_entities: {redaction_entities}; Exception message: {str(exc)}")

    return matched_entity_set, subtext_redaction_entities


def redact_text(text :str = "", text_redaction_entity :list = [], redact_profile_entities : list =[], redact_flg: bool = True) -> str:
    redacted_text = text[:]
    if redact_flg and text and text_redaction_entity:
        for idx, entity in enumerate(text_redaction_entity):
            try:
                if entity.get('subcategory', '') in redact_profile_entities and len(
                        constants.REGEX_SPECIAL_CHAR_REPLACE.sub(r"", entity['text'])) != 0:
                    entity_adjusted_text = constants.REGEX_SPECIAL_CHAR_REPLACE.sub(r".{1}", entity['text'])
                    redacted_text = re.sub(entity_adjusted_text, constants.REDACT_PARAGRAPH_STR, redacted_text)
            except Exception as exc:
                logger.warning(f"[entity# {idx}] subtext: {text}; font_info: {text_redaction_entity}; Exception message: {str(exc)}")

    return redacted_text


def get_matched_redact_entity_roi(roi: IQVDocument) -> Tuple[int, int, list]:
    """
    Collects all the redaction entities from the ROI and finds the matching redaction string
    Input: ROI
    Ouput: Length of redaction entity, Length of matched redactin entity, list of redaction entity
    """
    roi_fulltext = roi.GetFullText()
    len_redaction_entities, redaction_entities = get_redaction_entities(level_roi=roi)
    roi_entity_set = set(range(0, len_redaction_entities))
    roi_matched_entity_set = set()

    roi_redaction_entities = []
    if len_redaction_entities:
        matched_entity_set, roi_redaction_entities = align_redaction_with_subtext(text=roi_fulltext, redaction_entities=redaction_entities)
        roi_matched_entity_set.update(matched_entity_set)
        logger.debug(f"*** roi_id[{roi.id}]: {roi_fulltext}")
        logger.debug(f"redaction_entity: {roi_redaction_entities}")
        debug_notfound_entity = (roi_entity_set - roi_matched_entity_set)
        if len(debug_notfound_entity) > 0:
            logger.debug(f"Debug report: [{roi.id}] [**No subtext**]: Missing entity idx: {debug_notfound_entity} \
                roi_fulltext: {roi_fulltext} ; redaction_entities: {redaction_entities}")
                
    return len_redaction_entities, len(roi_entity_set.intersection(roi_matched_entity_set)), roi_redaction_entities
