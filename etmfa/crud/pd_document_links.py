import pandas as pd
import psycopg2
from etmfa_core.aidoc.io.load_xml_db_ext import GetIQVDocumentFromDB_headers
from flask import Response as JSONResponse
import logging
from http import HTTPStatus as status
from etmfa.consts import Consts as consts
from etmfa.crud.pd_document_config_terms import get_section_audit_info
from etmfa.db.db import db_context
from sqlalchemy.orm import Session

logger = logging.getLogger(consts.LOGGING_NAME)


def get_document_links(db: Session, aidoc_id: str, link_levels: int, toc: int):
    """
    Get document links for the requested aidoc_id with link_level

    :param db: db instance
    :param aidoc_id: document id 
    :param link_levels: link level of document
    :param toc: table of content list with parent child relationship
    :returns: list of sections/headers
    """

    connection = None
    if abs(toc) > 1:
        response = JSONResponse('TOC required 0 or 1', mimetype='text/html')
        response.status_code = status.PARTIAL_CONTENT
        return response
    try:
        connection = db_context.engine.raw_connection()
        iqv_doc_headers = GetIQVDocumentFromDB_headers(connection, aidoc_id)
        if iqv_doc_headers is None:
            response = JSONResponse(
                'This document is not available in our database',
                mimetype='text/html')
            response.status_code = status.NOT_FOUND
            return response
    except (Exception, psycopg2.Error) as error:
        logger.exception(f"Failed to get connection to postgresql : {error}")
    finally:
        if connection:
            connection.close()

    try:
        df = pd.DataFrame(
            [link.__dict__ for link in iqv_doc_headers.DocumentLinks])
        df = df[(df['LinkType'] == 'toc') & (df['LinkLevel'] <= link_levels) & (
                    df['LinkText'] != "blank_header") & (df['LinkLevel'] > 0)]
        df = df.reset_index(drop=True)
        df['link_id'] = df.apply(lambda x: x['link_id'] if x['LinkLevel']
                                == 1 else x['link_id_level{}'.format(x['LinkLevel'])], axis=1)
        df = df[['doc_id', 'group_type', 'link_id', 'LinkLevel', 'LinkPage',
                 'LinkPrefix', 'LinkText', 'LinkType', 'parent_id',
                 'iqv_standard_term', 'DocumentSequenceIndex']]
        df = df.rename(
            columns={'LinkText': 'source_file_section', 'LinkPage': 'page',
                     'LinkPrefix': 'sec_id', 'parent_id': 'line_id',
                     'iqv_standard_term': 'preferred_term'})
        df['page'] = df['page'] + 1
        # sorting by document sequence index and sec_id
        df = df.sort_values(by=['DocumentSequenceIndex', 'sec_id']).reset_index(
            drop=True)
        df.drop(['DocumentSequenceIndex'], axis=1, inplace=True)
        df['qc_change_type'] = ''
        df['sequence'] = [i for i in range(df.shape[0])]
        df['section_locked'] = False
        df['audit_info'] = get_section_audit_info(psdb=db, aidoc_id=aidoc_id,
                                                  link_ids=df['link_id'],
                                                  link_levels=df['LinkLevel'])

        headers = df.to_dict(orient='records')
        if toc == 0:
            # if toc not 1 then it will return without parent child relationship
            return headers
        elif toc == 1:
            # if toc is 1 returns sections/headers data with parent child relationship
            toc_headers = []  
            doc_headers = []
            for i in headers:              
                linklevel = i.get('LinkLevel')
                section_id = i.get('sec_id')          
                if linklevel == 1:
                    toc_headers.append(i)
                elif linklevel in (2,3,4,5,6):
                    toc_headers.append(i)                   
                    section_id_num = section_id.replace(".", "")
                    if section_id_num.isnumeric():
                        section_id_split = section_id.split(".")
                        section_id_join = ".".join(section_id_split[:-1]) + ("." if section_id_split.pop()=="" else "")
                        filtered_header = filter(lambda x: x.get('sec_id') == section_id_join, headers)
                        for item in filtered_header:
                            if item in headers:
                                index = headers.index(item)
                                if headers[index].get('childlevel'):
                                    headers[index].get('childlevel').append(i)
                                else:                            
                                    headers[index]['childlevel']= [i] 
                    elif isinstance(section_id, str):
                        doc_headers.append(i)

            # filtering headers by linklevel 1 in parent level and          
            # sorting child level  based on sec_id key
            for header in doc_headers:
                toc_headers.append(header)
            childlevel_headers = []
            for header in toc_headers:
                if len(header) != 14:
                    parent_header = (header["childlevel"])
                    sorted_parent_header = sorted(parent_header, key = lambda x:x['sec_id'])
                    for parent_header_item in sorted_parent_header:
                        if len(parent_header_item) != 14:
                            sorted_parent_header_child = sorted((parent_header_item["childlevel"]), key = lambda x:x['sec_id'])
                            for sorted_parent_header_item in sorted_parent_header_child:
                                if len(sorted_parent_header_item) != 14:
                                    sorted_parent_header_child_1 = sorted((sorted_parent_header_item["childlevel"]), key = lambda x:x['sec_id'])
                                    sorted_parent_header_item['childlevel'] = sorted_parent_header_child_1
                            parent_header_item['childlevel'] = sorted_parent_header_child
                    header['childlevel'] = sorted_parent_header
                childlevel_headers.append(header)
            filterd_childlevel_headers = list(filter(lambda x:x['LinkLevel']==1, childlevel_headers))
            return filterd_childlevel_headers

    except Exception as error:
        logger.exception(f"doc id {aidoc_id} having issue : {error}")
        return JSONResponse(status_code=status.PARTIAL_CONTENT,
                            content={"message": "Docid having some issue"})
