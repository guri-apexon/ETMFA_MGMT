import logging

from etmfa.auth import authenticate
from etmfa.db import db_context
from etmfa.server.api import api
from etmfa import crud
from flask import Response
from flask_restplus import Resource, abort
import json
from etmfa.consts import Consts as consts
from etmfa.server.namespaces.serializers import section_data_args, \
    section_header_args, section_data_config_args, enriched_data_args
from etmfa.utilities.extractor.prepare_cpt_section_data import PrepareUpdateData
from etmfa.utilities.redaction.protocol_view_redaction import \
    ProtocolViewRedaction
from etmfa.utilities.section_enriched import \
    update_section_data_with_enriched_data

logger = logging.getLogger(consts.LOGGING_NAME)

db = db_context.session

ns = api.namespace('CPT_config', path='/cpt_data',
                   description='Document paragraph data')


def get_enriched_data(aidoc_id, link_id):
    """
    To fetch enriched content from the nlp entity as per doc and section id
    """
    nlp_entity_data = crud.nlp_entity_content.get(db=db, doc_id=aidoc_id,
                                                  link_id=link_id)
    clinical_data = []
    for entity in nlp_entity_data:
        clinical_values = {
            'doc_id': entity.doc_id,
            'link_id': entity.link_id,
            'parent_id': entity.parent_id,
            'text': entity.standard_entity_name,
            'preferred_term': entity.iqv_standard_term,
            'ontology': entity.ontology,
            'synonyms': entity.entity_xref,
            'medical_term': "",
            'classification': entity.entity_class,
            'clinical_terms': entity.text
        }
        clinical_data.append(clinical_values)
    return clinical_data


def get_enriched_data_with_doc_id(aidoc_id):
    """
    To fetch enriched content from the nlp entity as per doc and section id
    """
    nlp_entity_data = crud.nlp_entity_content.get_with_doc_id(db=db, doc_id=aidoc_id
                                                              )
    clinical_data = []
    for entity in nlp_entity_data:
        clinical_values = {entity.standard_entity_name: {
            'preferred_term': entity.iqv_standard_term,
            'ontology': entity.ontology,
            'synonyms': entity.entity_xref,
            'medical_term': "",
            'classification': entity.entity_class
        }}
        clinical_data.append(clinical_values)
    return clinical_data


def get_section_data(aidoc_id, link_level, link_id, user_id, protocol):
    """
    Separate function to get section data, using doc and section id
    """
    iqv_document, imagebinaries = crud.get_document_object(aidoc_id, link_level,
                                                           link_id)
    if iqv_document is None:
        logger.info(f"Doc_id {aidoc_id} does not exists")
        message = json.dumps(
            {'message': "This document is not available in our database"})
        return Response(message, status=404, mimetype='application/json')
    protocol_view_redaction = ProtocolViewRedaction(user_id, protocol)
    finalized_iqvxml = PrepareUpdateData(iqv_document, imagebinaries,
                                         protocol_view_redaction.profile_details,
                                         protocol_view_redaction.entity_profile_genre)
    finalization_req_dict, _ = finalized_iqvxml.prepare_msg()
    # Collect the enriched clinical data based on doc and link ids.
    enriched_data = get_enriched_data(aidoc_id, link_id)
    # Collect the enriched preferred data based on doc and link ids.
    preferred_data = crud.get_preferred_data(db, aidoc_id, link_id)
    references_data = crud.get_references_data(db, aidoc_id, link_id)
    section_with_enriched = update_section_data_with_enriched_data(
        section_data=finalization_req_dict, enriched_data=enriched_data,
        preferred_data=preferred_data, references_data=references_data)
    return section_with_enriched


@ns.route("/")
@ns.response(500, 'Server error.')
class SectionHeaderAPI(Resource):
    @ns.expect(section_header_args)
    @ns.response(200, 'Success.')
    @ns.response(404, 'Document not found.')
    @api.doc(security='apikey')
    @authenticate
    def get(self):
        """ Get the document section headers """
        args = section_header_args.parse_args()
        aidoc_id = args.get('aidoc_id', '')
        link_level = args.get('link_level', 1)
        toc = args.get('toc', 0)
        headers_dict = crud.get_document_links(db, aidoc_id, link_level, toc)
        return headers_dict


@ns.route("/get_enriched_terms")
@ns.response(500, 'Server error.')
class GetEnrichedAPI(Resource):
    @ns.expect(enriched_data_args)
    @ns.response(200, 'Success.')
    @ns.response(404, 'Document not found.')
    @api.doc(security='apikey')
    @authenticate
    def get(self):
        """
        Get clinical terms values for the enriched text as per doc and section id
        """
        args = enriched_data_args.parse_args()
        aidoc_id = args.get('aidoc_id', '')
        link_id = args.get('link_id', '')
        clinical_data = get_enriched_data(aidoc_id=aidoc_id, link_id=link_id)
        return clinical_data


@ns.route('/get_section_data')
@ns.response(500, 'Server error.')
class SectionDataAPI(Resource):
    @ns.expect(section_data_args)
    @ns.response(200, 'Success.')
    @ns.response(404, 'Document not found.')
    @api.doc(security='apikey')
    @authenticate
    def get(self):
        """Get the source protocol document"""
        args = section_data_args.parse_args()
        aidoc_id = args.get('aidoc_id', '')
        link_level = args.get('link_level', 1)
        link_id = args.get('link_id', '')
        user_id = args.get('user_id', '')
        protocol = args.get('protocol', '')
        section_data = get_section_data(aidoc_id=aidoc_id,
                                        link_level=link_level, link_id=link_id,
                                        user_id=user_id, protocol=protocol)
        return section_data


@ns.route('/get_section_data_configurable_parameter')
@ns.response(500, 'Server error.')
class SectionDataConfigAPI(Resource):
    @ns.expect(section_data_config_args)
    @ns.response(200, 'Success.')
    @ns.response(404, 'Document not found.')
    @api.doc(security='apikey')
    @authenticate
    def get(self):
        """Get the source protocol document"""
        args = section_data_config_args.parse_args()
        aidoc_id = args.get('aidoc_id', '')
        link_level = args.get('link_level', 1)
        toc = args.get('toc', '')
        link_id = args.get('link_id', '')
        section_text = args.get('section_text', '')
        user_id = args.get('user_id', '')
        protocol = args.get('protocol', '')
        config_variables = args.get('config_variables', '')
        try:
            if toc and (link_id or section_text):
                return {"message": "Not valid parameter, please provide for toc or link_id/section text, not both"}

            if toc:
                link_level = link_level or 1
                section_header = crud.get_document_links(db, aidoc_id,
                                                         link_level, int(toc))
                # Terms values based on given configuration values
                terms_values = crud.get_document_terms_data(db, aidoc_id,
                                                            link_id,
                                                            config_variables,
                                                            {})

                enriched_data = get_enriched_data_with_doc_id(
                    aidoc_id=aidoc_id)
                return [section_header, terms_values, enriched_data]
            else:
                link_id, link_level, link_dict = crud.link_id_link_level_based_on_section_text(
                    db, aidoc_id, section_text, link_id, link_level)

                if not protocol:
                    protocol = crud.get_doc_protocol(db, aidoc_id)

                section_res = get_section_data(aidoc_id=aidoc_id,
                                               link_level=link_level,
                                               link_id=link_id, user_id=user_id,
                                               protocol=protocol)
                
                if isinstance(section_res, Response):                      
                    if section_res.status_code == 404:
                        message = json.dumps(
                            {'message': "This document is not available in our database"})
                        return Response(message, status=404, mimetype='application/json')

                # Terms values based on given configuration values
                terms_values = crud.get_document_terms_data(db, aidoc_id,
                                                            link_id,
                                                            config_variables,
                                                            link_dict)

                # enriched data from existing end point
                enriched_data = get_enriched_data(aidoc_id=aidoc_id,
                                                  link_id=link_id)
                logger.info(f"config api process completed")

                return [section_res, terms_values, enriched_data]
        except Exception as e:
            logger.exception(f"exception occurred in config api for doc_id {aidoc_id} and link_id {link_id} and exception is {e}")
            return abort(404, f"Exception to fetch configuration data {str(e)}")


