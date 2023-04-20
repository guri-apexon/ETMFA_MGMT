import logging
from etmfa.consts import Consts as consts
import pandas as pd

logger = logging.getLogger(consts.LOGGING_NAME)


def update_section_data_with_enriched_data(section_data: dict,
                                           enriched_data: list,
                                           preferred_data: list,
                                           references_data: list) -> dict:
    """
    To modify the section data with enriched text and terms.
    :param section_data: Response of section data API
    :param enriched_data: Response of enriched API with clinical terms
    :param preferred_data: Response of enriched API with preferred terms
    :param references_data: Response of enriched API with reference data
    :returns: Updated section data with clinical terms
    """
    enriched_df = pd.DataFrame(enriched_data)
    preferred_df = pd.DataFrame(preferred_data)
    reference_df = pd.DataFrame(references_data)

    if enriched_df.empty and preferred_df.empty and reference_df.empty:
        logger.info(
            "There is no clinical and preferred terms and references present for the sections")
    else:
        for sub_section in section_data:
            font_info = sub_section.get("font_info")
            content = sub_section.get("content")
            link_id = font_info.get("link_id")
            link_id_level2 = font_info.get("link_id_level2")
            link_id_level3 = font_info.get("link_id_level3")
            link_id_level4 = font_info.get("link_id_level4")
            link_id_level5 = font_info.get("link_id_level5")
            link_id_level6 = font_info.get("link_id_level6")
            sub_section.update({'clinical_terms': {}, 'preferred_terms': {},
                                'link_and_reference': {}})
            if content:
                roi_id = font_info.get("roi_id")
                para_id = roi_id.get("para")
                if not enriched_df.empty:
                    rows = enriched_df[enriched_df['parent_id'].isin([para_id])]
                    # remove the duplicates records from the rows df
                    rows.drop_duplicates(subset=['text'], keep="last", inplace=True)
                    # Deleted df columns which is not needed any more
                    rows.drop(['doc_id', 'link_id', 'parent_id'], axis=1, inplace=True)
                    terms_values = rows.set_index('text').to_dict(orient='index')
                    sub_section.update({'clinical_terms': terms_values})

                if not preferred_df.empty:
                    rows = preferred_df[preferred_df['id'].isin(
                        [link_id, link_id_level2, link_id_level3,
                         link_id_level4, link_id_level5, link_id_level6])]
                    # Deleted df columns which is not needed any more
                    rows.drop(['parent_id'], axis=1, inplace=True)
                    terms_values = rows.set_index('text').to_dict(orient='index')
                    sub_section.update({'preferred_terms': terms_values})

                if not reference_df.empty and reference_df.iloc[0]['parent_id']:
                    rows = reference_df[reference_df['parent_id'].isin([para_id])]
                    ref_values = rows.set_index('id').to_dict(orient='index')
                    sub_section.update({'link_and_reference': ref_values})

    return section_data
